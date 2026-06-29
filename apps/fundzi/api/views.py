import json
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from apps.fundzi.models import (
    DynamicForm,
    FinancialPartner,
    FinancialService,
    FinancingRequest,
    FormField,
    InternalNote,
    RequestAttachment,
    ServiceContent,
    Workflow,
    WorkflowStep,
    decimal_from_payload,
)
from apps.fundzi.services import create_financing_request


def api_login_required(view_func):
    """Like login_required but returns JSON 401 instead of redirecting to the
    login page, so the SPA can detect an expired/missing session reliably."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'errors': {'detail': 'برای انجام این عملیات باید وارد شوید.'}},
                status=401,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def api_staff_required(view_func):
    """Require an authenticated admin/operator and return JSON 401/403 instead
    of redirecting to the login page."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'errors': {'detail': 'برای انجام این عملیات باید وارد شوید.'}},
                status=401,
            )
        if not is_admin_or_operator(request.user):
            return JsonResponse(
                {'errors': {'detail': 'شما به این بخش دسترسی ندارید.'}},
                status=403,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def error_response(error, status=400):
    if isinstance(error, ValidationError):
        return JsonResponse({'errors': error.message_dict if hasattr(error, 'message_dict') else error.messages}, status=status)
    return JsonResponse({'errors': error}, status=status)


def parse_payload(request):
    if request.content_type and request.content_type.startswith('application/json'):
        body = request.body.decode('utf-8') or '{}'
        return json.loads(body)
    return request.POST.dict()


def parse_bool(value, default=False):
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def parse_json_value(value, default):
    if value in (None, ''):
        return default
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def paginate_payload(request, queryset, serializer, default_page_size=20):
    try:
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(max(int(request.GET.get('page_size', default_page_size)), 1), 100)
    except ValueError:
        return None, error_response({'pagination': 'پارامترهای صفحه‌بندی معتبر نیستند.'})
    paginator = Paginator(queryset, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages or 1)
        page = page_obj.number
    return {
        'results': [serializer(item) for item in page_obj.object_list],
        'count': paginator.count,
        'page': page,
        'page_size': page_size,
    }, None


# Roles assignable from the admin panel. ``applicant`` is the implicit default.
ROLE_CHOICES = ('admin', 'operator', 'investor', 'vendor', 'applicant')
# Roles represented as Django groups (admin is represented via is_staff).
ROLE_GROUPS = ('operator', 'investor', 'vendor', 'applicant')


def user_role(user):
    if not user.is_authenticated:
        return 'guest'
    if user.is_superuser:
        return 'admin'
    # Group-based roles take priority so a staff operator is not mislabeled admin.
    user_groups = {name.lower() for name in user.groups.values_list('name', flat=True)}
    if 'operator' in user_groups:
        return 'operator'
    if 'investor' in user_groups:
        return 'investor'
    if 'vendor' in user_groups:
        return 'vendor'
    if user.is_staff:
        return 'admin'
    return 'applicant'


def apply_role(user, role):
    """Set a user's role consistently: clear role groups, then grant the new
    role. Admin is expressed via is_staff; never auto-escalate to superuser."""
    user.groups.remove(*Group.objects.filter(name__in=ROLE_GROUPS))
    user.is_staff = role == 'admin'
    if role in ROLE_GROUPS:
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
    user.save()
    return user


def user_payload(user):
    if not user.is_authenticated:
        return None
    return {
        'id': user.id,
        'username': user.get_username(),
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.get_username(),
        'role': user_role(user),
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }


def is_admin_or_operator(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name__iexact='operator').exists())


def service_summary(service):
    return {
        'id': service.id,
        'title': service.title,
        'slug': service.slug,
        'short_description': service.short_description,
        'full_description': service.full_description,
        'service_type': service.service_type,
        'is_active': service.is_active,
        'order': service.order,
        'rules_config': service.rules_config,
        'metadata': service.metadata,
    }


def service_detail(service):
    data = service_summary(service)
    data.update({
        'full_description': service.full_description,
        'contents': [
            {
                'id': content.id,
                'content_type': content.content_type,
                'title': content.title,
                'body': content.body,
                'order': content.order,
                'metadata': content.metadata,
            }
            for content in service.contents.filter(is_active=True)
        ],
    })
    return data


def form_schema(service):
    form = getattr(service, 'form', None)
    if not form:
        return None
    return {
        'id': form.id,
        'title': form.title,
        'description': form.description,
        'fields': [
            {
                'id': field.id,
                'label': field.label,
                'key': field.key,
                'type': field.field_type,
                'required': field.required,
                'placeholder': field.placeholder,
                'help_text': field.help_text,
                'options': field.options,
                'validation_config': field.validation_config,
                'order': field.order,
            }
            for field in form.fields.filter(is_active=True)
        ],
    }


def request_payload(instance, include_values=False):
    data = {
        'id': instance.id,
        'tracking_code': instance.tracking_code,
        'service': service_summary(instance.service),
        'current_status': instance.current_status,
        'current_workflow_step': {
            'id': instance.current_workflow_step_id,
            'key': instance.current_workflow_step.key if instance.current_workflow_step else None,
            'title': instance.current_workflow_step.title if instance.current_workflow_step else None,
        },
        'submitted_at': instance.submitted_at.isoformat(),
        'updated_at': instance.updated_at.isoformat(),
        'is_archived': instance.is_archived,
        'user': user_payload(instance.user),
        'admin_assignee': user_payload(instance.admin_assignee) if instance.admin_assignee else None,
    }
    if include_values:
        data['field_values'] = [
            {
                'field': value.field.key,
                'label': value.field.label,
                'type': value.field.field_type,
                'value': value.value,
                'file': value.file.url if value.file else None,
            }
            for value in instance.field_values.select_related('field')
        ]
        data['history'] = history_payload(instance)
    return data


def content_payload(content):
    return {
        'id': content.id,
        'content_type': content.content_type,
        'title': content.title,
        'body': content.body,
        'order': content.order,
        'is_active': content.is_active,
        'metadata': content.metadata,
    }


def admin_service_payload(service):
    data = service_summary(service)
    data['contents'] = [content_payload(item) for item in service.contents.all()]
    form = getattr(service, 'form', None)
    data['form'] = None if not form else {
        'id': form.id,
        'title': form.title,
        'description': form.description,
        'is_active': form.is_active,
        'metadata': form.metadata,
        'fields': [
            {
                'id': field.id,
                'label': field.label,
                'key': field.key,
                'type': field.field_type,
                'field_type': field.field_type,
                'required': field.required,
                'placeholder': field.placeholder,
                'help_text': field.help_text,
                'options': field.options,
                'validation_config': field.validation_config,
                'order': field.order,
                'is_active': field.is_active,
            }
            for field in form.fields.all()
        ],
    }
    workflow = getattr(service, 'workflow', None)
    data['workflow'] = None if not workflow else {
        'id': workflow.id,
        'name': workflow.name,
        'description': workflow.description,
        'is_active': workflow.is_active,
        'steps': [
            {
                'id': step.id,
                'key': step.key,
                'title': step.title,
                'description': step.description,
                'order': step.order,
                'is_initial': step.is_initial,
                'is_terminal': step.is_terminal,
                'is_active': step.is_active,
                'metadata': step.metadata,
            }
            for step in workflow.steps.all()
        ],
    }
    return data


def user_admin_payload(user):
    return {
        'id': user.id,
        'username': user.get_username(),
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.get_username(),
        'role': user_role(user),
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'is_active': user.is_active,
        'date_joined': user.date_joined.isoformat(),
        'groups': list(user.groups.values_list('name', flat=True)),
        'requests_count': getattr(user, 'requests_count', user.fundzi_requests.count()),
    }


def partner_payload(partner):
    return {
        'id': partner.id,
        'name': partner.name,
        'type': partner.type,
        'service_categories': partner.service_categories,
        'min_amount': partner.min_amount,
        'max_amount': partner.max_amount,
        'accepted_collateral_types': partner.accepted_collateral_types,
        'is_active': partner.is_active,
        'description': partner.description,
        'created_at': partner.created_at.isoformat(),
        'updated_at': partner.updated_at.isoformat(),
    }


@method_decorator(csrf_exempt, name='dispatch')
class SendOtpView(View):
    def post(self, request):
        try:
            payload = parse_payload(request)
        except json.JSONDecodeError as exc:
            return error_response(exc)
        phone_number = payload.get('phone_number') or payload.get('username')
        if not phone_number:
            return error_response({'phone_number': 'شماره موبایل الزامی است.'})
        return JsonResponse({'detail': 'کد ورود ارسال شد.', 'demo_code': '123456'})


@method_decorator(csrf_exempt, name='dispatch')
class VerifyOtpView(View):
    def post(self, request):
        try:
            payload = parse_payload(request)
        except json.JSONDecodeError as exc:
            return error_response(exc)
        phone_number = payload.get('phone_number') or payload.get('username')
        otp_code = payload.get('otp_code') or payload.get('code')
        if not phone_number:
            return error_response({'phone_number': 'شماره موبایل الزامی است.'})
        if getattr(settings, 'FUNDZI_OTP_ENABLED', True):
            if not otp_code:
                return error_response({'otp_code': 'کد ورود الزامی است.'})
            if otp_code != '123456':
                return error_response({'otp_code': 'کد وارد شده معتبر نیست.'})
        User = get_user_model()
        user, _ = User.objects.get_or_create(username=phone_number, defaults={'first_name': ''})
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return JsonResponse({'user': user_payload(user)})


@method_decorator(csrf_exempt, name='dispatch')
class PasswordLoginView(View):
    def post(self, request):
        try:
            payload = parse_payload(request)
        except json.JSONDecodeError as exc:
            return error_response(exc)
        user = authenticate(request, username=payload.get('username'), password=payload.get('password'))
        if not user:
            return error_response({'credentials': 'نام کاربری یا رمز عبور معتبر نیست.'}, status=401)
        login(request, user)
        return JsonResponse({'user': user_payload(user)})


@method_decorator(api_login_required, name='dispatch')
class CurrentUserView(View):
    def get(self, request):
        return JsonResponse({'user': user_payload(request.user)})


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    def post(self, request):
        logout(request)
        return JsonResponse({'detail': 'خارج شدید.'})


def history_payload(instance):
    return [
        {
            'id': item.id,
            'from_status': item.from_status,
            'to_status': item.to_status,
            'changed_by': item.changed_by.get_username() if item.changed_by else None,
            'note': item.note,
            'created_at': item.created_at.isoformat(),
        }
        for item in instance.history.select_related('changed_by')
    ]


@require_GET
def service_list(request):
    services = FinancialService.objects.filter(is_active=True)
    return JsonResponse({'results': [service_summary(service) for service in services]})


@require_GET
def service_detail_view(request, slug):
    service = get_object_or_404(FinancialService, slug=slug, is_active=True)
    return JsonResponse(service_detail(service))


@require_GET
def service_form_view(request, slug):
    service = get_object_or_404(FinancialService, slug=slug, is_active=True)
    schema = form_schema(service)
    if not schema:
        return error_response({'form': 'فرم این سرویس تعریف نشده است.'}, status=404)
    return JsonResponse(schema)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_login_required, name='dispatch')
class ServiceRequestCreateView(View):
    def post(self, request, slug):
        service = get_object_or_404(FinancialService, slug=slug, is_active=True)
        try:
            payload = parse_payload(request)
            financing_request = create_financing_request(service, request.user, payload, request.FILES)
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        return JsonResponse(request_payload(financing_request, include_values=True), status=201)


@method_decorator(api_login_required, name='dispatch')
class RequestListView(View):
    def get(self, request):
        queryset = FinancingRequest.objects.filter(user=request.user).select_related('service', 'current_workflow_step')
        return JsonResponse({'results': [request_payload(item) for item in queryset]})


@method_decorator(api_login_required, name='dispatch')
class RequestDetailView(View):
    def get(self, request, pk):
        instance = get_object_or_404(
            FinancingRequest.objects.select_related('service', 'current_workflow_step'),
            pk=pk,
            user=request.user,
        )
        return JsonResponse(request_payload(instance, include_values=True))


@method_decorator(api_login_required, name='dispatch')
class RequestHistoryView(View):
    def get(self, request, pk):
        instance = get_object_or_404(FinancingRequest, pk=pk, user=request.user)
        return JsonResponse({'results': history_payload(instance)})


@method_decorator(api_staff_required, name='dispatch')
class AdminRequestListView(View):
    def get(self, request):
        queryset = FinancingRequest.objects.select_related(
            'service',
            'current_workflow_step',
            'user',
            'admin_assignee',
        ).all()
        service = request.GET.get('service')
        status = request.GET.get('status')
        tracking_code = request.GET.get('tracking_code')
        user_phone = request.GET.get('user_phone')
        search = request.GET.get('q') or request.GET.get('search')
        ordering = request.GET.get('ordering') or '-submitted_at'
        if service:
            queryset = queryset.filter(service__slug=service)
        if status:
            queryset = queryset.filter(current_status=status)
        if tracking_code:
            queryset = queryset.filter(tracking_code__icontains=tracking_code)
        if user_phone:
            queryset = queryset.filter(user__username__icontains=user_phone)
        if search:
            queryset = queryset.filter(
                Q(tracking_code__icontains=search)
                | Q(user__username__icontains=search)
                | Q(service__title__icontains=search)
                | Q(current_status__icontains=search)
            )
        allowed_ordering = {'submitted_at', '-submitted_at', 'current_status', '-current_status', 'updated_at', '-updated_at'}
        if ordering not in allowed_ordering:
            ordering = '-submitted_at'
        queryset = queryset.order_by(ordering, '-id')
        payload, error = paginate_payload(request, queryset, request_payload)
        if error:
            return error
        return JsonResponse(payload)


@method_decorator(api_staff_required, name='dispatch')
class AdminStatsView(View):
    def get(self, request):
        today = timezone.localdate()
        week_ago = timezone.now() - timedelta(days=7)
        requests = FinancingRequest.objects.select_related('service', 'user', 'admin_assignee')
        by_status = list(requests.values('current_status').annotate(count=Count('id')).order_by('current_status'))
        by_service = list(requests.values('service__id', 'service__title', 'service__slug').annotate(count=Count('id')).order_by('-count'))
        latest = requests.order_by('-submitted_at')[:8]
        User = get_user_model()
        return JsonResponse({
            'total_requests': requests.count(),
            'by_status': by_status,
            'by_service': [
                {
                    'service_id': item['service__id'],
                    'title': item['service__title'],
                    'slug': item['service__slug'],
                    'count': item['count'],
                }
                for item in by_service
            ],
            'today_requests': requests.filter(submitted_at__date=today).count(),
            'last_7_days_requests': requests.filter(submitted_at__gte=week_ago).count(),
            'archived_requests': requests.filter(is_archived=True).count(),
            'users_count': User.objects.count(),
            'latest_requests': [request_payload(item) for item in latest],
        })


@method_decorator(api_staff_required, name='dispatch')
class AdminRequestDetailView(View):
    def get(self, request, pk):
        instance = get_object_or_404(
            FinancingRequest.objects.select_related('service', 'current_workflow_step', 'user'),
            pk=pk,
        )
        data = request_payload(instance, include_values=True)
        data['attachments'] = [
            {
                'id': attachment.id,
                'title': attachment.title,
                'document_type': attachment.document_type,
                'file': attachment.file.url if attachment.file else None,
                'created_at': attachment.created_at.isoformat(),
            }
            for attachment in instance.attachments.all()
        ]
        data['internal_notes'] = [
            {
                'id': note.id,
                'body': note.body,
                'author': note.author.get_username() if note.author else None,
                'created_at': note.created_at.isoformat(),
            }
            for note in instance.internal_notes.select_related('author')
        ]
        data['workflow_steps'] = [
            {'id': step.id, 'key': step.key, 'title': step.title, 'order': step.order}
            for step in instance.service.workflow.steps.filter(is_active=True)
        ]
        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminRequestAssignView(View):
    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest.objects.select_related('service'), pk=pk)
        try:
            payload = parse_payload(request)
        except json.JSONDecodeError as exc:
            return error_response(exc)
        assignee_id = payload.get('assignee_id')
        if assignee_id in (None, '', 'null'):
            instance.admin_assignee = None
        else:
            User = get_user_model()
            assignee = get_object_or_404(User, pk=assignee_id)
            if not is_admin_or_operator(assignee):
                return error_response({'assignee_id': 'مسئول انتخاب‌شده باید ادمین یا اپراتور باشد.'}, status=400)
            instance.admin_assignee = assignee
        instance.save(update_fields=['admin_assignee', 'updated_at'])
        return JsonResponse(request_payload(instance, include_values=True))


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminRequestArchiveView(View):
    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest.objects.select_related('service'), pk=pk)
        try:
            payload = parse_payload(request)
        except json.JSONDecodeError as exc:
            return error_response(exc)
        instance.is_archived = parse_bool(payload.get('is_archived'), instance.is_archived)
        instance.save(update_fields=['is_archived', 'updated_at'])
        return JsonResponse(request_payload(instance, include_values=True))


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminRequestAttachmentListView(View):
    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest, pk=pk)
        upload = request.FILES.get('file')
        if not upload:
            return error_response({'file': 'فایل پیوست الزامی است.'})
        attachment = RequestAttachment.objects.create(
            request=instance,
            file=upload,
            title=request.POST.get('title', upload.name),
            document_type=request.POST.get('document_type', ''),
            uploaded_by=request.user,
        )
        return JsonResponse({
            'id': attachment.id,
            'title': attachment.title,
            'document_type': attachment.document_type,
            'file': attachment.file.url if attachment.file else None,
            'created_at': attachment.created_at.isoformat(),
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminRequestAttachmentDetailView(View):
    def delete(self, request, pk, att_id):
        attachment = get_object_or_404(RequestAttachment, pk=att_id, request_id=pk)
        attachment.delete()
        return JsonResponse({'detail': 'پیوست حذف شد.'})


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminRequestStatusView(View):
    def post(self, request, pk):
        return self.update_status(request, pk)

    def patch(self, request, pk):
        return self.update_status(request, pk)

    def update_status(self, request, pk):
        instance = get_object_or_404(FinancingRequest.objects.select_related('service'), pk=pk)
        try:
            payload = parse_payload(request)
            step_key = payload.get('status') or payload.get('step')
            step = get_object_or_404(WorkflowStep, workflow=instance.service.workflow, key=step_key, is_active=True)
            instance.change_status(step, changed_by=request.user, note=payload.get('note', ''))
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        return JsonResponse(request_payload(instance, include_values=True))


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminRequestNoteView(View):
    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest, pk=pk)
        try:
            payload = parse_payload(request)
        except json.JSONDecodeError as exc:
            return error_response(exc)
        body = payload.get('body') or payload.get('note')
        if not body:
            return error_response({'body': 'متن یادداشت الزامی است.'})
        note = InternalNote.objects.create(request=instance, author=request.user, body=body)
        return JsonResponse({
            'id': note.id,
            'body': note.body,
            'author': request.user.get_username(),
            'created_at': note.created_at.isoformat(),
        }, status=201)


def service_from_payload(service, payload, partial=False):
    required = ['title', 'slug']
    if not partial:
        for key in required:
            if not payload.get(key):
                raise ValidationError({key: 'این فیلد الزامی است.'})
    for key in ['title', 'slug', 'short_description', 'full_description', 'service_type']:
        if key in payload:
            setattr(service, key, payload.get(key) or '')
    if 'is_active' in payload:
        service.is_active = parse_bool(payload.get('is_active'), service.is_active)
    if 'order' in payload:
        service.order = int(payload.get('order') or 0)
    if 'rules_config' in payload:
        service.rules_config = parse_json_value(payload.get('rules_config'), {})
    if 'metadata' in payload:
        service.metadata = parse_json_value(payload.get('metadata'), {})
    service.full_clean()
    service.save()
    return service


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceListView(View):
    def get(self, request):
        queryset = FinancialService.objects.prefetch_related(
            'contents',
            'form__fields',
            'workflow__steps',
        ).all()
        search = request.GET.get('q') or request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(slug__icontains=search))
        return JsonResponse({'results': [admin_service_payload(service) for service in queryset]})

    def post(self, request):
        try:
            payload = parse_payload(request)
            service = service_from_payload(FinancialService(), payload)
            DynamicForm.objects.get_or_create(service=service, defaults={'title': f'فرم {service.title}'})
            Workflow.objects.get_or_create(service=service, defaults={'name': f'گردش‌کار {service.title}'})
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(service), status=201)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceDetailView(View):
    def get(self, request, pk):
        service = get_object_or_404(FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps'), pk=pk)
        return JsonResponse(admin_service_payload(service))

    def patch(self, request, pk):
        service = get_object_or_404(FinancialService, pk=pk)
        try:
            payload = parse_payload(request)
            service_from_payload(service, payload, partial=True)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(service))

    def delete(self, request, pk):
        service = get_object_or_404(FinancialService, pk=pk)
        if service.requests.exists():
            return error_response({'service': 'این سرویس درخواست ثبت‌شده دارد و قابل حذف نیست.'}, status=409)
        service.delete()
        return JsonResponse({'detail': 'سرویس حذف شد.'})


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceContentListView(View):
    def post(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        try:
            payload = parse_payload(request)
            content = ServiceContent.objects.create(
                service=service,
                content_type=payload.get('content_type') or 'introduction',
                title=payload.get('title', ''),
                body=payload.get('body') or '',
                order=int(payload.get('order') or 0),
                is_active=parse_bool(payload.get('is_active'), True),
                metadata=parse_json_value(payload.get('metadata'), {}),
            )
            content.full_clean()
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(content_payload(content), status=201)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceContentDetailView(View):
    def patch(self, request, service_id, content_id):
        content = get_object_or_404(ServiceContent, pk=content_id, service_id=service_id)
        try:
            payload = parse_payload(request)
            for key in ['content_type', 'title', 'body']:
                if key in payload:
                    setattr(content, key, payload.get(key) or '')
            if 'order' in payload:
                content.order = int(payload.get('order') or 0)
            if 'is_active' in payload:
                content.is_active = parse_bool(payload.get('is_active'), content.is_active)
            if 'metadata' in payload:
                content.metadata = parse_json_value(payload.get('metadata'), {})
            content.full_clean()
            content.save()
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(content_payload(content))

    def delete(self, request, service_id, content_id):
        content = get_object_or_404(ServiceContent, pk=content_id, service_id=service_id)
        content.delete()
        return JsonResponse({'detail': 'محتوا حذف شد.'})


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceFormView(View):
    def patch(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        form, _ = DynamicForm.objects.get_or_create(service=service, defaults={'title': f'فرم {service.title}'})
        try:
            payload = parse_payload(request)
            for key in ['title', 'description']:
                if key in payload:
                    setattr(form, key, payload.get(key) or '')
            if 'is_active' in payload:
                form.is_active = parse_bool(payload.get('is_active'), form.is_active)
            if 'metadata' in payload:
                form.metadata = parse_json_value(payload.get('metadata'), {})
            form.full_clean()
            form.save()
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(service))


def field_from_payload(field, payload, form=None, partial=False):
    if form:
        field.form = form
    if not partial:
        for key in ['label', 'key', 'field_type']:
            if not payload.get(key):
                raise ValidationError({key: 'این فیلد الزامی است.'})
    if 'type' in payload and 'field_type' not in payload:
        payload['field_type'] = payload['type']
    for key in ['label', 'key', 'field_type', 'placeholder', 'help_text']:
        if key in payload:
            setattr(field, key, payload.get(key) or '')
    if 'required' in payload:
        field.required = parse_bool(payload.get('required'), field.required)
    if 'is_active' in payload:
        field.is_active = parse_bool(payload.get('is_active'), field.is_active)
    if 'order' in payload:
        field.order = int(payload.get('order') or 0)
    if 'options' in payload:
        field.options = parse_json_value(payload.get('options'), [])
    if 'validation_config' in payload:
        field.validation_config = parse_json_value(payload.get('validation_config'), {})
    field.full_clean()
    field.save()
    return field


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceFieldListView(View):
    def post(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        form, _ = DynamicForm.objects.get_or_create(service=service, defaults={'title': f'فرم {service.title}'})
        try:
            payload = parse_payload(request)
            field = field_from_payload(FormField(), payload, form=form)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(service), status=201)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceFieldDetailView(View):
    def patch(self, request, service_id, field_id):
        field = get_object_or_404(FormField, pk=field_id, form__service_id=service_id)
        try:
            payload = parse_payload(request)
            field_from_payload(field, payload, partial=True)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(field.form.service))

    def delete(self, request, service_id, field_id):
        field = get_object_or_404(FormField, pk=field_id, form__service_id=service_id)
        service = field.form.service
        field.delete()
        return JsonResponse(admin_service_payload(service))


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceWorkflowView(View):
    def patch(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        workflow, _ = Workflow.objects.get_or_create(service=service, defaults={'name': f'گردش‌کار {service.title}'})
        try:
            payload = parse_payload(request)
            for key in ['name', 'description']:
                if key in payload:
                    setattr(workflow, key, payload.get(key) or '')
            if 'is_active' in payload:
                workflow.is_active = parse_bool(payload.get('is_active'), workflow.is_active)
            workflow.full_clean()
            workflow.save()
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(service))


def workflow_step_from_payload(step, payload, workflow=None, partial=False):
    if workflow:
        step.workflow = workflow
    if not partial:
        for key in ['key', 'title']:
            if not payload.get(key):
                raise ValidationError({key: 'این فیلد الزامی است.'})
    for key in ['key', 'title', 'description']:
        if key in payload:
            setattr(step, key, payload.get(key) or '')
    if 'order' in payload:
        step.order = int(payload.get('order') or 0)
    if 'is_initial' in payload:
        step.is_initial = parse_bool(payload.get('is_initial'), step.is_initial)
    if 'is_terminal' in payload:
        step.is_terminal = parse_bool(payload.get('is_terminal'), step.is_terminal)
    if 'is_active' in payload:
        step.is_active = parse_bool(payload.get('is_active'), step.is_active)
    if 'metadata' in payload:
        step.metadata = parse_json_value(payload.get('metadata'), {})
    step.full_clean()
    step.save()
    if step.is_initial:
        WorkflowStep.objects.filter(workflow=step.workflow).exclude(pk=step.pk).update(is_initial=False)
    return step


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceWorkflowStepListView(View):
    def post(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        workflow, _ = Workflow.objects.get_or_create(service=service, defaults={'name': f'گردش‌کار {service.title}'})
        try:
            payload = parse_payload(request)
            workflow_step_from_payload(WorkflowStep(), payload, workflow=workflow)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(service), status=201)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminServiceWorkflowStepDetailView(View):
    def patch(self, request, service_id, step_id):
        step = get_object_or_404(WorkflowStep, pk=step_id, workflow__service_id=service_id)
        try:
            payload = parse_payload(request)
            workflow_step_from_payload(step, payload, partial=True)
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            return error_response(exc)
        return JsonResponse(admin_service_payload(step.workflow.service))

    def delete(self, request, service_id, step_id):
        step = get_object_or_404(WorkflowStep, pk=step_id, workflow__service_id=service_id)
        service = step.workflow.service
        if FinancingRequest.objects.filter(current_workflow_step=step).exists():
            return error_response({'step': 'این مرحله روی درخواست‌های موجود استفاده شده است.'}, status=409)
        step.delete()
        return JsonResponse(admin_service_payload(service))


def require_admin_user(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return error_response({'detail': 'فقط ادمین به این بخش دسترسی دارد.'}, status=403)
    return None


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminUserListView(View):
    def get(self, request):
        denied = require_admin_user(request)
        if denied:
            return denied
        User = get_user_model()
        queryset = User.objects.annotate(requests_count=Count('fundzi_requests')).prefetch_related('groups').all().order_by('-date_joined')
        search = request.GET.get('q') or request.GET.get('search')
        role = request.GET.get('role')
        if search:
            queryset = queryset.filter(Q(username__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search))
        if role:
            if role == 'admin':
                queryset = queryset.filter(Q(is_staff=True) | Q(is_superuser=True))
            else:
                queryset = queryset.filter(groups__name__iexact=role)
        payload, error = paginate_payload(request, queryset.distinct(), user_admin_payload)
        if error:
            return error
        return JsonResponse(payload)

    def post(self, request):
        denied = require_admin_user(request)
        if denied:
            return denied
        User = get_user_model()
        try:
            payload = parse_payload(request)
            username = (payload.get('phone_number') or payload.get('username') or '').strip()
            if not username:
                return error_response({'phone_number': 'شماره موبایل الزامی است.'})
            if User.objects.filter(username=username).exists():
                return error_response({'phone_number': 'کاربری با این شماره موبایل از قبل وجود دارد.'}, status=409)
            role = payload.get('role') or 'applicant'
            if role not in ROLE_CHOICES:
                return error_response({'role': 'نقش انتخاب‌شده معتبر نیست.'})
            user = User(
                username=username,
                first_name=payload.get('first_name') or '',
                last_name=payload.get('last_name') or '',
                is_active=parse_bool(payload.get('is_active'), True),
            )
            password = payload.get('password')
            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()
            user.save()
            apply_role(user, role)
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        user = User.objects.annotate(requests_count=Count('fundzi_requests')).get(pk=user.pk)
        return JsonResponse(user_admin_payload(user), status=201)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminUserDetailView(View):
    def get(self, request, pk):
        denied = require_admin_user(request)
        if denied:
            return denied
        User = get_user_model()
        user = get_object_or_404(User.objects.annotate(requests_count=Count('fundzi_requests')).prefetch_related('groups'), pk=pk)
        return JsonResponse(user_admin_payload(user))

    def patch(self, request, pk):
        denied = require_admin_user(request)
        if denied:
            return denied
        User = get_user_model()
        user = get_object_or_404(User, pk=pk)
        try:
            payload = parse_payload(request)
            for key in ['first_name', 'last_name']:
                if key in payload:
                    setattr(user, key, payload.get(key) or '')
            if 'is_active' in payload and user.pk == request.user.pk and not parse_bool(payload.get('is_active'), True):
                return error_response({'is_active': 'نمی‌توانید حساب خود را غیرفعال کنید.'}, status=409)
            for key in ['is_active', 'is_staff']:
                if key in payload:
                    setattr(user, key, parse_bool(payload.get(key), getattr(user, key)))
            if 'groups' in payload:
                groups = []
                for name in parse_json_value(payload.get('groups'), []):
                    group, _ = Group.objects.get_or_create(name=str(name))
                    groups.append(group)
                user.groups.set(groups)
            user.save()
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        return JsonResponse(user_admin_payload(user))


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminUserSetRoleView(View):
    def post(self, request, pk):
        denied = require_admin_user(request)
        if denied:
            return denied
        User = get_user_model()
        user = get_object_or_404(User, pk=pk)
        try:
            payload = parse_payload(request)
            role = payload.get('role')
            if role not in ROLE_CHOICES:
                return error_response({'role': 'نقش انتخاب‌شده معتبر نیست.'})
            if user.pk == request.user.pk and role != 'admin':
                return error_response({'role': 'نمی‌توانید نقش مدیریتی خود را تغییر دهید.'}, status=409)
            apply_role(user, role)
        except json.JSONDecodeError as exc:
            return error_response(exc)
        user = type(user).objects.annotate(requests_count=Count('fundzi_requests')).get(pk=user.pk)
        return JsonResponse(user_admin_payload(user))


def partner_from_payload(partner, payload, partial=False):
    if not partial and not payload.get('name'):
        raise ValidationError({'name': 'نام همکار الزامی است.'})
    for key in ['name', 'type', 'description']:
        if key in payload:
            setattr(partner, key, payload.get(key) or '')
    if 'service_categories' in payload:
        partner.service_categories = parse_json_value(payload.get('service_categories'), [])
    if 'accepted_collateral_types' in payload:
        partner.accepted_collateral_types = parse_json_value(payload.get('accepted_collateral_types'), [])
    if 'min_amount' in payload:
        partner.min_amount = decimal_from_payload(payload.get('min_amount'))
    if 'max_amount' in payload:
        partner.max_amount = decimal_from_payload(payload.get('max_amount'))
    if 'is_active' in payload:
        partner.is_active = parse_bool(payload.get('is_active'), partner.is_active)
    partner.full_clean()
    partner.save()
    return partner


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminPartnerListView(View):
    def get(self, request):
        queryset = FinancialPartner.objects.all().order_by('name')
        search = request.GET.get('q') or request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(type__icontains=search))
        return JsonResponse({'results': [partner_payload(item) for item in queryset]})

    def post(self, request):
        try:
            payload = parse_payload(request)
            partner = partner_from_payload(FinancialPartner(), payload)
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        return JsonResponse(partner_payload(partner), status=201)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(api_staff_required, name='dispatch')
class AdminPartnerDetailView(View):
    def get(self, request, pk):
        return JsonResponse(partner_payload(get_object_or_404(FinancialPartner, pk=pk)))

    def patch(self, request, pk):
        partner = get_object_or_404(FinancialPartner, pk=pk)
        try:
            payload = parse_payload(request)
            partner_from_payload(partner, payload, partial=True)
        except (ValidationError, json.JSONDecodeError) as exc:
            return error_response(exc)
        return JsonResponse(partner_payload(partner))

    def delete(self, request, pk):
        partner = get_object_or_404(FinancialPartner, pk=pk)
        partner.delete()
        return JsonResponse({'detail': 'همکار مالی حذف شد.'})
