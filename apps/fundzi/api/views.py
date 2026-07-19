import csv
import io
import time
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.fundzi.api.permissions import IsAdminOrOperator, IsAuthenticatedJSON, IsPartnerUser, is_admin_or_operator
from apps.fundzi.api.serializers import (
    AdminRequestDetailSerializer,
    AdminServiceSerializer,
    FinancialPartnerSerializer,
    FinancingRequestDetailSerializer,
    FinancingRequestSerializer,
    FormSchemaSerializer,
    MatchingRuleSerializer,
    MatchingRuleWriteSerializer,
    MatchResultSerializer,
    NotificationSerializer,
    PartnerOfferSerializer,
    PasswordLoginSerializer,
    SendOtpSerializer,
    ServiceDetailSerializer,
    ServiceListSerializer,
    UserAdminSerializer,
    VendorApplicationSerializer,
    VendorSerializer,
    VendorServiceSerializer,
    VerifyOtpSerializer,
)
from apps.fundzi.models import (
    DynamicForm,
    FinancialPartner,
    FinancialService,
    FinancingRequest,
    FormField,
    InternalNote,
    MatchingRule,
    MatchResult,
    Notification,
    PartnerOffer,
    RequestAttachment,
    ServiceContent,
    Vendor,
    VendorApplication,
    VendorService,
    Workflow,
    WorkflowStep,
    decimal_from_payload,
)
from apps.fundzi.services import create_financing_request, normalize_option


# ── Utilities ─────────────────────────────────────────────────────────────────

ROLE_CHOICES = ('admin', 'operator', 'investor', 'vendor', 'applicant')
ROLE_GROUPS = ('operator', 'investor', 'vendor', 'applicant')


def user_role(user):
    if not user.is_authenticated:
        return 'guest'
    if user.is_superuser:
        return 'admin'
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
    user.groups.remove(*Group.objects.filter(name__in=ROLE_GROUPS))
    user.is_staff = role == 'admin'
    if role in ROLE_GROUPS:
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
    user.save()
    return user


def user_payload(user):
    if not user or not user.is_authenticated:
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


def paginate(request, queryset, serializer_fn, default_page_size=20):
    try:
        page = max(int(request.GET.get('page', 1)), 1)
        page_size = min(max(int(request.GET.get('page_size', default_page_size)), 1), 100)
    except ValueError:
        raise ValidationError({'pagination': 'پارامترهای صفحه‌بندی معتبر نیستند.'})
    paginator = Paginator(queryset, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages or 1)
        page = page_obj.number
    return {
        'results': [serializer_fn(item) for item in page_obj.object_list],
        'count': paginator.count,
        'page': page,
        'page_size': page_size,
    }


def parse_bool(value, default=False):
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('1', 'true', 'yes', 'on')


def parse_json_value(value, default):
    import json
    if value in (None, ''):
        return default
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def _django_validation_error_to_drf(exc):
    if hasattr(exc, 'message_dict'):
        raise ValidationError(exc.message_dict)
    raise ValidationError({'detail': exc.messages})


# ── Auth views ────────────────────────────────────────────────────────────────

class SendOtpView(APIView):
    permission_classes = []

    def post(self, request):
        data = request.data
        phone_number = data.get('phone_number') or data.get('username')
        ser = SendOtpSerializer(data={'phone_number': phone_number or ''})
        ser.is_valid(raise_exception=True)
        phone_number = ser.validated_data['phone_number']

        from apps.fundzi.otp_backend import OTP_TTL_SECONDS, generate_otp, send_otp
        code = generate_otp()
        request.session['_otp_code'] = code
        request.session['_otp_phone'] = phone_number
        request.session['_otp_expires'] = time.time() + OTP_TTL_SECONDS

        sent = send_otp(phone_number, code)
        if not sent:
            raise ValidationError({'detail': 'ارسال کد ورود ناموفق بود. لطفاً دوباره تلاش کنید.'})
        return Response({'detail': 'کد ورود ارسال شد.'})


class VerifyOtpView(APIView):
    permission_classes = []

    def post(self, request):
        from django.conf import settings as django_settings
        data = request.data
        phone_number = data.get('phone_number') or data.get('username')
        otp_code = data.get('otp_code') or data.get('code') or ''
        ser = VerifyOtpSerializer(data={'phone_number': phone_number or '', 'otp_code': otp_code})
        ser.is_valid(raise_exception=True)
        phone_number = ser.validated_data['phone_number']
        otp_code = ser.validated_data['otp_code']

        if getattr(django_settings, 'FUNDZI_OTP_ENABLED', True):
            if not otp_code:
                raise ValidationError({'otp_code': 'کد ورود الزامی است.'})
            stored_code = request.session.get('_otp_code')
            stored_phone = request.session.get('_otp_phone')
            expires = request.session.get('_otp_expires', 0)
            if stored_phone != phone_number or not stored_code:
                raise ValidationError({'otp_code': 'ابتدا درخواست ارسال کد کنید.'})
            if time.time() > expires:
                raise ValidationError({'otp_code': 'کد ورود منقضی شده است. لطفاً کد جدید دریافت کنید.'})
            if otp_code != stored_code:
                raise ValidationError({'otp_code': 'کد وارد شده معتبر نیست.'})
            for key in ('_otp_code', '_otp_phone', '_otp_expires'):
                request.session.pop(key, None)

        User = get_user_model()
        user, _ = User.objects.get_or_create(username=phone_number, defaults={'first_name': ''})
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return Response({'user': user_payload(user)})


class PasswordLoginView(APIView):
    permission_classes = []

    def post(self, request):
        ser = PasswordLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=ser.validated_data['username'],
            password=ser.validated_data['password'],
        )
        if not user:
            raise ValidationError({'credentials': 'نام کاربری یا رمز عبور معتبر نیست.'})
        login(request, user)
        return Response({'user': user_payload(user)})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def get(self, request):
        return Response({'user': user_payload(request.user)})


class LogoutView(APIView):
    permission_classes = []

    def post(self, request):
        logout(request)
        return Response({'detail': 'خارج شدید.'})


# ── Service views ─────────────────────────────────────────────────────────────

class ServiceListView(APIView):
    permission_classes = []

    def get(self, request):
        services = FinancialService.objects.filter(is_active=True)
        return Response({'results': ServiceListSerializer(services, many=True).data})


class ServiceDetailView(APIView):
    permission_classes = []

    def get(self, request, slug):
        service = get_object_or_404(FinancialService, slug=slug, is_active=True)
        return Response(ServiceDetailSerializer(service).data)


class ServiceFormView(APIView):
    permission_classes = []

    def get(self, request, slug):
        service = get_object_or_404(FinancialService, slug=slug, is_active=True)
        form = getattr(service, 'form', None)
        if not form:
            raise NotFound({'form': 'فرم این سرویس تعریف نشده است.'})
        return Response(FormSchemaSerializer().to_representation(form))


# Fields that must never appear in the public P2P listing
_P2P_PRIVATE_KEYS = frozenset({
    'full_name', 'national_id', 'phone',
    'collateral_documents',
    'monthly_income', 'credit_history',
    'additional_info', 'additional_conditions', 'collateral_notes',
})


class PublicP2PRequestListView(APIView):
    """Public listing of admin-approved P2P requests for a service.

    Only services with rules_config.p2p=true are served.
    Only requests in 'matching' status appear (identity + collateral verified by admin).
    Personal fields are stripped server-side.
    """
    permission_classes = []

    def get(self, request, slug):
        service = get_object_or_404(FinancialService, slug=slug, is_active=True)
        if not service.rules_config.get('p2p'):
            return Response({'count': 0, 'results': []})

        qs = (
            FinancingRequest.objects
            .filter(service=service, current_status='matching', is_archived=False)
            .prefetch_related('field_values__field')
            .order_by('-submitted_at')
        )

        results = []
        for req in qs:
            fields = {}
            for fv in req.field_values.select_related('field'):
                key = fv.field.key
                if key in _P2P_PRIVATE_KEYS:
                    continue
                val = fv.value
                if val not in (None, '', []):
                    fields[key] = {
                        'label': fv.field.label,
                        'value': val,
                        'type': fv.field.field_type,
                    }
            results.append({
                'id': req.id,
                'ref': f'#{req.tracking_code[-4:]}' if req.tracking_code else f'#{req.pk}',
                'current_status': req.current_status,
                'submitted_at': req.submitted_at.isoformat(),
                'fields': fields,
            })

        return Response({'count': len(results), 'results': results})


# ── User request views ────────────────────────────────────────────────────────

class ServiceRequestCreateView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def post(self, request, slug):
        service = get_object_or_404(FinancialService, slug=slug, is_active=True)
        try:
            financing_request = create_financing_request(service, request.user, request.data, request.FILES)
        except DjangoValidationError as exc:
            _django_validation_error_to_drf(exc)
        return Response(
            FinancingRequestDetailSerializer(financing_request).data,
            status=status.HTTP_201_CREATED,
        )


class RequestListView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def get(self, request):
        qs = (
            FinancingRequest.objects
            .filter(user=request.user)
            .select_related('service', 'current_workflow_step')
        )
        return Response({'results': FinancingRequestSerializer(qs, many=True).data})


class RequestDetailView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def get(self, request, pk):
        instance = get_object_or_404(
            FinancingRequest.objects.select_related('service', 'current_workflow_step'),
            pk=pk,
            user=request.user,
        )
        return Response(FinancingRequestDetailSerializer(instance).data)


class RequestHistoryView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def get(self, request, pk):
        instance = get_object_or_404(FinancingRequest, pk=pk, user=request.user)
        from apps.fundzi.api.serializers import RequestHistorySerializer
        history = instance.history.select_related('changed_by')
        return Response({'results': RequestHistorySerializer(history, many=True).data})


# ── Admin request views ───────────────────────────────────────────────────────

class AdminRequestListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = FinancingRequest.objects.select_related(
            'service', 'current_workflow_step', 'user', 'admin_assignee'
        )
        svc = request.GET.get('service')
        req_status = request.GET.get('status')
        tracking_code = request.GET.get('tracking_code')
        user_phone = request.GET.get('user_phone')
        search = request.GET.get('q') or request.GET.get('search')
        ordering = request.GET.get('ordering') or '-submitted_at'
        if svc:
            qs = qs.filter(service__slug=svc)
        if req_status:
            qs = qs.filter(current_status=req_status)
        if tracking_code:
            qs = qs.filter(tracking_code__icontains=tracking_code)
        if user_phone:
            qs = qs.filter(user__username__icontains=user_phone)
        if search:
            qs = qs.filter(
                Q(tracking_code__icontains=search)
                | Q(user__username__icontains=search)
                | Q(service__title__icontains=search)
                | Q(current_status__icontains=search)
            )
        allowed_ordering = {
            'submitted_at', '-submitted_at', 'current_status',
            '-current_status', 'updated_at', '-updated_at',
        }
        if ordering not in allowed_ordering:
            ordering = '-submitted_at'
        qs = qs.order_by(ordering, '-id')
        return Response(paginate(request, qs, lambda r: FinancingRequestSerializer(r).data))


class AdminStatsView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        today = timezone.localdate()
        week_ago = timezone.now() - timedelta(days=7)
        requests = FinancingRequest.objects.select_related('service', 'user', 'admin_assignee')
        by_status = list(requests.values('current_status').annotate(count=Count('id')).order_by('current_status'))
        by_service = list(
            requests.values('service__id', 'service__title', 'service__slug')
            .annotate(count=Count('id')).order_by('-count')
        )
        latest = requests.order_by('-submitted_at')[:8]
        User = get_user_model()
        return Response({
            'total_requests': requests.count(),
            'by_status': by_status,
            'by_service': [
                {'service_id': i['service__id'], 'title': i['service__title'], 'slug': i['service__slug'], 'count': i['count']}
                for i in by_service
            ],
            'today_requests': requests.filter(submitted_at__date=today).count(),
            'last_7_days_requests': requests.filter(submitted_at__gte=week_ago).count(),
            'archived_requests': requests.filter(is_archived=True).count(),
            'users_count': User.objects.count(),
            'latest_requests': FinancingRequestSerializer(latest, many=True).data,
        })


class AdminRequestDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request, pk):
        instance = get_object_or_404(
            FinancingRequest.objects.select_related('service', 'current_workflow_step', 'user'),
            pk=pk,
        )
        return Response(AdminRequestDetailSerializer(instance).data)


class AdminRequestAssignView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest.objects.select_related('service'), pk=pk)
        assignee_id = request.data.get('assignee_id')
        if assignee_id in (None, '', 'null'):
            instance.admin_assignee = None
        else:
            User = get_user_model()
            assignee = get_object_or_404(User, pk=assignee_id)
            if not is_admin_or_operator(assignee):
                raise ValidationError({'assignee_id': 'مسئول انتخاب‌شده باید ادمین یا اپراتور باشد.'})
            instance.admin_assignee = assignee
        instance.save(update_fields=['admin_assignee', 'updated_at'])
        return Response(FinancingRequestDetailSerializer(instance).data)


class AdminRequestArchiveView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest.objects.select_related('service'), pk=pk)
        instance.is_archived = parse_bool(request.data.get('is_archived'), instance.is_archived)
        instance.save(update_fields=['is_archived', 'updated_at'])
        return Response(FinancingRequestDetailSerializer(instance).data)


class AdminRequestAttachmentListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest, pk=pk)
        upload = request.FILES.get('file')
        if not upload:
            raise ValidationError({'file': 'فایل پیوست الزامی است.'})
        attachment = RequestAttachment.objects.create(
            request=instance,
            file=upload,
            title=request.POST.get('title', upload.name),
            document_type=request.POST.get('document_type', ''),
            uploaded_by=request.user,
        )
        return Response({
            'id': attachment.id,
            'title': attachment.title,
            'document_type': attachment.document_type,
            'file': attachment.file.url if attachment.file else None,
            'created_at': attachment.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class AdminRequestAttachmentDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def delete(self, request, pk, att_id):
        attachment = get_object_or_404(RequestAttachment, pk=att_id, request_id=pk)
        attachment.delete()
        return Response({'detail': 'پیوست حذف شد.'})


class AdminRequestStatusView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, pk):
        return self._update_status(request, pk)

    def patch(self, request, pk):
        return self._update_status(request, pk)

    def _update_status(self, request, pk):
        instance = get_object_or_404(FinancingRequest.objects.select_related('service'), pk=pk)
        step_key = request.data.get('status') or request.data.get('step')
        try:
            step = get_object_or_404(WorkflowStep, workflow=instance.service.workflow, key=step_key, is_active=True)
            instance.change_status(step, changed_by=request.user, note=request.data.get('note', ''))
        except DjangoValidationError as exc:
            _django_validation_error_to_drf(exc)
        return Response(FinancingRequestDetailSerializer(instance).data)


class AdminRequestNoteView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, pk):
        instance = get_object_or_404(FinancingRequest, pk=pk)
        body = request.data.get('body') or request.data.get('note')
        if not body:
            raise ValidationError({'body': 'متن یادداشت الزامی است.'})
        note = InternalNote.objects.create(request=instance, author=request.user, body=body)
        return Response({
            'id': note.id,
            'body': note.body,
            'author': request.user.get_username(),
            'created_at': note.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


# ── Admin service views ───────────────────────────────────────────────────────

def _service_from_data(service, data, partial=False):
    if not partial:
        for key in ['title', 'slug']:
            if not data.get(key):
                raise ValidationError({key: 'این فیلد الزامی است.'})
    for key in ['title', 'slug', 'short_description', 'full_description', 'service_type']:
        if key in data:
            setattr(service, key, data.get(key) or '')
    if 'is_active' in data:
        service.is_active = parse_bool(data.get('is_active'), service.is_active)
    if 'order' in data:
        service.order = int(data.get('order') or 0)
    if 'rules_config' in data:
        service.rules_config = parse_json_value(data.get('rules_config'), {})
    if 'metadata' in data:
        service.metadata = parse_json_value(data.get('metadata'), {})
    try:
        service.full_clean()
    except DjangoValidationError as exc:
        _django_validation_error_to_drf(exc)
    service.save()
    return service


class AdminServiceListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').all()
        search = request.GET.get('q') or request.GET.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(slug__icontains=search))
        return Response({'results': [AdminServiceSerializer().to_representation(s) for s in qs]})

    def post(self, request):
        service = _service_from_data(FinancialService(), request.data)
        DynamicForm.objects.get_or_create(service=service, defaults={'title': f'فرم {service.title}'})
        Workflow.objects.get_or_create(service=service, defaults={'name': f'گردش‌کار {service.title}'})
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service.pk)
        return Response(AdminServiceSerializer().to_representation(service), status=status.HTTP_201_CREATED)


class AdminServiceDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request, pk):
        service = get_object_or_404(
            FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps'),
            pk=pk,
        )
        return Response(AdminServiceSerializer().to_representation(service))

    def patch(self, request, pk):
        service = get_object_or_404(FinancialService, pk=pk)
        _service_from_data(service, request.data, partial=True)
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service.pk)
        return Response(AdminServiceSerializer().to_representation(service))

    def delete(self, request, pk):
        service = get_object_or_404(FinancialService, pk=pk)
        if service.requests.exists():
            raise ValidationError({'service': 'این سرویس درخواست ثبت‌شده دارد و قابل حذف نیست.'})
        service.delete()
        return Response({'detail': 'سرویس حذف شد.'})


class AdminServiceContentListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        try:
            content = ServiceContent(
                service=service,
                content_type=request.data.get('content_type') or 'introduction',
                title=request.data.get('title', ''),
                body=request.data.get('body') or '',
                order=int(request.data.get('order') or 0),
                is_active=parse_bool(request.data.get('is_active'), True),
                metadata=parse_json_value(request.data.get('metadata'), {}),
            )
            content.full_clean()
            content.save()
        except DjangoValidationError as exc:
            _django_validation_error_to_drf(exc)
        return Response({
            'id': content.id, 'content_type': content.content_type, 'title': content.title,
            'body': content.body, 'order': content.order, 'is_active': content.is_active,
            'metadata': content.metadata,
        }, status=status.HTTP_201_CREATED)


class AdminServiceContentDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def patch(self, request, service_id, content_id):
        content = get_object_or_404(ServiceContent, pk=content_id, service_id=service_id)
        data = request.data
        try:
            for key in ['content_type', 'title', 'body']:
                if key in data:
                    setattr(content, key, data.get(key) or '')
            if 'order' in data:
                content.order = int(data.get('order') or 0)
            if 'is_active' in data:
                content.is_active = parse_bool(data.get('is_active'), content.is_active)
            if 'metadata' in data:
                content.metadata = parse_json_value(data.get('metadata'), {})
            content.full_clean()
            content.save()
        except DjangoValidationError as exc:
            _django_validation_error_to_drf(exc)
        return Response({
            'id': content.id, 'content_type': content.content_type, 'title': content.title,
            'body': content.body, 'order': content.order, 'is_active': content.is_active,
            'metadata': content.metadata,
        })

    def delete(self, request, service_id, content_id):
        content = get_object_or_404(ServiceContent, pk=content_id, service_id=service_id)
        content.delete()
        return Response({'detail': 'محتوا حذف شد.'})


class AdminServiceFormView(APIView):
    permission_classes = [IsAdminOrOperator]

    def patch(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        form, _ = DynamicForm.objects.get_or_create(service=service, defaults={'title': f'فرم {service.title}'})
        data = request.data
        try:
            for key in ['title', 'description']:
                if key in data:
                    setattr(form, key, data.get(key) or '')
            if 'is_active' in data:
                form.is_active = parse_bool(data.get('is_active'), form.is_active)
            if 'metadata' in data:
                form.metadata = parse_json_value(data.get('metadata'), {})
            form.full_clean()
            form.save()
        except DjangoValidationError as exc:
            _django_validation_error_to_drf(exc)
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service.pk)
        return Response(AdminServiceSerializer().to_representation(service))


def _apply_field_group(field, data):
    """Set ``parent``/``group_option`` (conditional group) from admin payload."""
    if 'parent' not in data and 'group_option' not in data:
        return
    parent_id = data.get('parent') if 'parent' in data else field.parent_id
    if parent_id in (None, '', 0, '0'):
        field.parent = None
        field.group_option = ''
        return

    parent = FormField.objects.filter(pk=parent_id, form=field.form).first()
    if not parent:
        raise ValidationError({'parent': 'فیلد والد یافت نشد یا متعلق به این فرم نیست.'})
    if field.pk and parent.pk == field.pk:
        raise ValidationError({'parent': 'فیلد نمی‌تواند والد خودش باشد.'})
    if parent.field_type not in ('select', 'multi_select'):
        raise ValidationError({'parent': 'فیلد والد باید از نوع انتخاب تکی یا چندتایی باشد.'})
    if parent.parent_id:
        raise ValidationError({'parent': 'گروه‌بندی تو در تو پشتیبانی نمی‌شود.'})
    if field.pk and field.children.exists():
        raise ValidationError({'parent': 'فیلدی که خودش والد گروه است نمی‌تواند زیرمجموعه فیلد دیگری شود.'})

    group_option = data.get('group_option') if 'group_option' in data else field.group_option
    group_option = '' if group_option is None else str(group_option)
    if not group_option:
        raise ValidationError({'group_option': 'گزینه فعال‌کننده گروه را انتخاب کنید.'})
    allowed = [str(normalize_option(option)) for option in (parent.options or [])]
    if group_option not in allowed:
        raise ValidationError({'group_option': 'گزینه انتخاب‌شده در فیلد والد وجود ندارد.'})

    field.parent = parent
    field.group_option = group_option


def _field_from_data(field, data, form=None, partial=False):
    if form:
        field.form = form
    if not partial:
        for key in ['label', 'key', 'field_type']:
            if not data.get(key) and not data.get('type' if key == 'field_type' else key):
                raise ValidationError({key: 'این فیلد الزامی است.'})
    if 'type' in data and 'field_type' not in data:
        data = dict(data)
        data['field_type'] = data['type']
    for key in ['label', 'key', 'field_type', 'placeholder', 'help_text']:
        if key in data:
            setattr(field, key, data.get(key) or '')
    if 'required' in data:
        field.required = parse_bool(data.get('required'), field.required)
    if 'is_active' in data:
        field.is_active = parse_bool(data.get('is_active'), field.is_active)
    if 'order' in data:
        field.order = int(data.get('order') or 0)
    if 'options' in data:
        field.options = parse_json_value(data.get('options'), [])
    if 'validation_config' in data:
        field.validation_config = parse_json_value(data.get('validation_config'), {})
    _apply_field_group(field, data)
    if field.pk and field.children.exists():
        if field.field_type not in ('select', 'multi_select'):
            raise ValidationError({'field_type': 'این فیلد والد یک گروه است و باید از نوع انتخابی بماند.'})
        allowed = [str(normalize_option(option)) for option in (field.options or [])]
        orphaned = field.children.exclude(group_option__in=allowed)
        if orphaned.exists():
            labels = '، '.join(orphaned.values_list('label', flat=True))
            raise ValidationError({'options': f'این گزینه‌ها توسط فیلدهای زیرمجموعه استفاده می‌شوند: {labels}'})
    try:
        field.full_clean()
    except DjangoValidationError as exc:
        _django_validation_error_to_drf(exc)
    field.save()
    return field


class AdminServiceFieldListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        form, _ = DynamicForm.objects.get_or_create(service=service, defaults={'title': f'فرم {service.title}'})
        _field_from_data(FormField(), request.data, form=form)
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service.pk)
        return Response(AdminServiceSerializer().to_representation(service), status=status.HTTP_201_CREATED)


class AdminServiceFieldDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def patch(self, request, service_id, field_id):
        field = get_object_or_404(FormField, pk=field_id, form__service_id=service_id)
        _field_from_data(field, request.data, partial=True)
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service_id)
        return Response(AdminServiceSerializer().to_representation(service))

    def delete(self, request, service_id, field_id):
        field = get_object_or_404(FormField, pk=field_id, form__service_id=service_id)
        service_pk = field.form.service_id
        field.delete()
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service_pk)
        return Response(AdminServiceSerializer().to_representation(service))


class AdminServiceWorkflowView(APIView):
    permission_classes = [IsAdminOrOperator]

    def patch(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        workflow, _ = Workflow.objects.get_or_create(service=service, defaults={'name': f'گردش‌کار {service.title}'})
        data = request.data
        try:
            for key in ['name', 'description']:
                if key in data:
                    setattr(workflow, key, data.get(key) or '')
            if 'is_active' in data:
                workflow.is_active = parse_bool(data.get('is_active'), workflow.is_active)
            workflow.full_clean()
            workflow.save()
        except DjangoValidationError as exc:
            _django_validation_error_to_drf(exc)
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service.pk)
        return Response(AdminServiceSerializer().to_representation(service))


def _step_from_data(step, data, workflow=None, partial=False):
    if workflow:
        step.workflow = workflow
    if not partial:
        for key in ['key', 'title']:
            if not data.get(key):
                raise ValidationError({key: 'این فیلد الزامی است.'})
    for key in ['key', 'title', 'description']:
        if key in data:
            setattr(step, key, data.get(key) or '')
    if 'order' in data:
        step.order = int(data.get('order') or 0)
    for flag in ['is_initial', 'is_terminal', 'is_active']:
        if flag in data:
            setattr(step, flag, parse_bool(data.get(flag), getattr(step, flag)))
    if 'metadata' in data:
        step.metadata = parse_json_value(data.get('metadata'), {})
    try:
        step.full_clean()
    except DjangoValidationError as exc:
        _django_validation_error_to_drf(exc)
    step.save()
    if step.is_initial:
        WorkflowStep.objects.filter(workflow=step.workflow).exclude(pk=step.pk).update(is_initial=False)
    return step


class AdminServiceWorkflowStepListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, service_id):
        service = get_object_or_404(FinancialService, pk=service_id)
        workflow, _ = Workflow.objects.get_or_create(service=service, defaults={'name': f'گردش‌کار {service.title}'})
        _step_from_data(WorkflowStep(), request.data, workflow=workflow)
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service_id)
        return Response(AdminServiceSerializer().to_representation(service), status=status.HTTP_201_CREATED)


class AdminServiceWorkflowStepDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def patch(self, request, service_id, step_id):
        step = get_object_or_404(WorkflowStep, pk=step_id, workflow__service_id=service_id)
        _step_from_data(step, request.data, partial=True)
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service_id)
        return Response(AdminServiceSerializer().to_representation(service))

    def delete(self, request, service_id, step_id):
        step = get_object_or_404(WorkflowStep, pk=step_id, workflow__service_id=service_id)
        if FinancingRequest.objects.filter(current_workflow_step=step).exists():
            raise ValidationError({'step': 'این مرحله روی درخواست‌های موجود استفاده شده است.'})
        service_pk = step.workflow.service_id
        step.delete()
        service = FinancialService.objects.prefetch_related('contents', 'form__fields', 'workflow__steps').get(pk=service_pk)
        return Response(AdminServiceSerializer().to_representation(service))


# ── Admin user views ──────────────────────────────────────────────────────────

def _require_admin_user(request):
    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied(detail='فقط ادمین به این بخش دسترسی دارد.')


class AdminUserListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        _require_admin_user(request)
        User = get_user_model()
        qs = (
            User.objects
            .annotate(requests_count=Count('fundzi_requests'))
            .prefetch_related('groups')
            .order_by('-date_joined')
        )
        search = request.GET.get('q') or request.GET.get('search')
        role = request.GET.get('role')
        if search:
            qs = qs.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )
        if role:
            if role == 'admin':
                qs = qs.filter(Q(is_staff=True) | Q(is_superuser=True))
            else:
                qs = qs.filter(groups__name__iexact=role)
        return Response(paginate(request, qs.distinct(), lambda u: _user_admin_payload(u)))

    def post(self, request):
        _require_admin_user(request)
        User = get_user_model()
        data = request.data
        username = (data.get('phone_number') or data.get('username') or '').strip()
        if not username:
            raise ValidationError({'phone_number': 'شماره موبایل الزامی است.'})
        if User.objects.filter(username=username).exists():
            raise ValidationError({'phone_number': 'کاربری با این شماره موبایل از قبل وجود دارد.'})
        role = data.get('role') or 'applicant'
        if role not in ROLE_CHOICES:
            raise ValidationError({'role': 'نقش انتخاب‌شده معتبر نیست.'})
        user = User(
            username=username,
            first_name=data.get('first_name') or '',
            last_name=data.get('last_name') or '',
            is_active=parse_bool(data.get('is_active'), True),
        )
        password = data.get('password')
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        apply_role(user, role)
        user = User.objects.annotate(requests_count=Count('fundzi_requests')).get(pk=user.pk)
        return Response(_user_admin_payload(user), status=status.HTTP_201_CREATED)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request, pk):
        _require_admin_user(request)
        User = get_user_model()
        user = get_object_or_404(
            User.objects.annotate(requests_count=Count('fundzi_requests')).prefetch_related('groups'),
            pk=pk,
        )
        return Response(_user_admin_payload(user))

    def patch(self, request, pk):
        _require_admin_user(request)
        User = get_user_model()
        user = get_object_or_404(User, pk=pk)
        data = request.data
        for key in ['first_name', 'last_name']:
            if key in data:
                setattr(user, key, data.get(key) or '')
        if 'is_active' in data and user.pk == request.user.pk and not parse_bool(data.get('is_active'), True):
            raise ValidationError({'is_active': 'نمی‌توانید حساب خود را غیرفعال کنید.'})
        for key in ['is_active', 'is_staff']:
            if key in data:
                setattr(user, key, parse_bool(data.get(key), getattr(user, key)))
        if 'groups' in data:
            groups = []
            for name in parse_json_value(data.get('groups'), []):
                group, _ = Group.objects.get_or_create(name=str(name))
                groups.append(group)
            user.groups.set(groups)
        user.save()
        user = User.objects.annotate(requests_count=Count('fundzi_requests')).get(pk=user.pk)
        return Response(_user_admin_payload(user))


class AdminUserSetRoleView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, pk):
        _require_admin_user(request)
        User = get_user_model()
        user = get_object_or_404(User, pk=pk)
        role = request.data.get('role')
        if role not in ROLE_CHOICES:
            raise ValidationError({'role': 'نقش انتخاب‌شده معتبر نیست.'})
        if user.pk == request.user.pk and role != 'admin':
            raise ValidationError({'role': 'نمی‌توانید نقش مدیریتی خود را تغییر دهید.'})
        apply_role(user, role)
        user = type(user).objects.annotate(requests_count=Count('fundzi_requests')).get(pk=user.pk)
        return Response(_user_admin_payload(user))


def _user_admin_payload(user):
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


# ── Admin partner views ───────────────────────────────────────────────────────

class AdminPartnerListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = FinancialPartner.objects.all().order_by('name')
        search = request.GET.get('q') or request.GET.get('search')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(type__icontains=search))
        return Response({'results': FinancialPartnerSerializer(qs, many=True).data})

    def post(self, request):
        ser = FinancialPartnerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        partner = ser.save()
        return Response(FinancialPartnerSerializer(partner).data, status=status.HTTP_201_CREATED)


class AdminPartnerDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request, pk):
        partner = get_object_or_404(FinancialPartner, pk=pk)
        return Response(FinancialPartnerSerializer(partner).data)

    def patch(self, request, pk):
        partner = get_object_or_404(FinancialPartner, pk=pk)
        ser = FinancialPartnerSerializer(partner, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(FinancialPartnerSerializer(partner).data)

    def delete(self, request, pk):
        partner = get_object_or_404(FinancialPartner, pk=pk)
        partner.delete()
        return Response({'detail': 'همکار مالی حذف شد.'})


# ── Notification views ────────────────────────────────────────────────────────

def _notification_payload(n):
    return {
        'id': n.id,
        'kind': n.kind,
        'channel': n.channel,
        'title': n.title,
        'body': n.body,
        'is_read': n.is_read,
        'request_id': n.request_id,
        'tracking_code': n.request.tracking_code if n.request else None,
        'created_at': n.created_at.isoformat(),
    }


class NotificationListView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def get(self, request):
        qs = Notification.objects.filter(user=request.user, channel='in_app').select_related('request')
        if parse_bool(request.GET.get('unread'), False):
            qs = qs.filter(is_read=False)
        payload = paginate(request, qs, _notification_payload)
        payload['unread_count'] = Notification.objects.filter(
            user=request.user, channel='in_app', is_read=False
        ).count()
        return Response(payload)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, channel='in_app', is_read=False).count()
        return Response({'unread_count': count})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_read()
        return Response(_notification_payload(notification))


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def post(self, request):
        updated = Notification.objects.filter(
            user=request.user, channel='in_app', is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({'detail': 'همه اعلان‌ها خوانده شد.', 'updated': updated})


# ── Health check ──────────────────────────────────────────────────────────────

class HealthCheckView(APIView):
    permission_classes = []

    def get(self, request):
        from django.db import connection
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False
        code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({'status': 'ok' if db_ok else 'error', 'db': db_ok}, status=code)


# ── Phase 3.1: Partner Portal ─────────────────────────────────────────────────

class PartnerRequestListView(APIView):
    permission_classes = [IsPartnerUser]

    def get(self, request):
        qs = (
            FinancingRequest.objects
            .filter(match_results__partner=request.partner, match_results__status='assigned')
            .select_related('service', 'current_workflow_step')
            .distinct()
            .order_by('-submitted_at')
        )
        data = [
            {
                'id': r.id,
                'tracking_code': r.tracking_code,
                'service': r.service.title,
                'current_status': r.current_status,
                'submitted_at': r.submitted_at.isoformat(),
                'has_offer': r.partner_offers.filter(partner=request.partner).exists(),
            }
            for r in qs
        ]
        return Response({'results': data})


class PartnerRequestDetailView(APIView):
    permission_classes = [IsPartnerUser]

    def get(self, request, pk):
        try:
            r = (
                FinancingRequest.objects
                .filter(match_results__partner=request.partner, match_results__status='assigned')
                .select_related('service', 'current_workflow_step')
                .get(pk=pk)
            )
        except FinancingRequest.DoesNotExist:
            raise NotFound({'detail': 'درخواست یافت نشد.'})
        field_values = [
            {'label': fv.field.label, 'value': fv.value}
            for fv in r.field_values.select_related('field')
            if fv.field.key not in ('phone_number', 'national_id', 'full_name')
        ]
        offers = PartnerOfferSerializer(
            r.partner_offers.filter(partner=request.partner), many=True
        ).data
        return Response({
            'id': r.id,
            'tracking_code': r.tracking_code,
            'service': r.service.title,
            'current_status': r.current_status,
            'submitted_at': r.submitted_at.isoformat(),
            'field_values': field_values,
            'offers': offers,
        })


class PartnerOfferCreateView(APIView):
    permission_classes = [IsPartnerUser]

    def post(self, request, pk):
        try:
            financing_request = (
                FinancingRequest.objects
                .filter(match_results__partner=request.partner, match_results__status='assigned')
                .get(pk=pk)
            )
        except FinancingRequest.DoesNotExist:
            raise NotFound({'detail': 'درخواست یافت نشد.'})
        ser = PartnerOfferSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        offer = ser.save(request=financing_request, partner=request.partner, submitted_by=request.user)
        return Response({'id': offer.id, 'status': offer.status, 'detail': 'پیشنهاد با موفقیت ثبت شد.'}, status=status.HTTP_201_CREATED)


class PartnerOfferListView(APIView):
    permission_classes = [IsPartnerUser]

    def get(self, request):
        qs = (
            PartnerOffer.objects
            .filter(partner=request.partner)
            .select_related('request', 'request__service')
            .order_by('-created_at')
        )
        data = [
            {
                'id': o.id,
                'request_tracking_code': o.request.tracking_code,
                'service': o.request.service.title,
                'amount': str(o.amount),
                'interest_rate': str(o.interest_rate),
                'duration_months': o.duration_months,
                'status': o.status,
                'created_at': o.created_at.isoformat(),
            }
            for o in qs
        ]
        return Response({'results': data})


# ── Phase 3.2: Admin Matching Views ──────────────────────────────────────────

class AdminMatchingRuleListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = MatchingRule.objects.select_related('partner').all()
        return Response({'results': MatchingRuleSerializer(qs, many=True).data})

    def post(self, request):
        ser = MatchingRuleWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        rule = ser.save()
        return Response({'id': rule.id, 'detail': 'قانون تطبیق ایجاد شد.'}, status=status.HTTP_201_CREATED)


class AdminMatchingRuleDetailView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request, pk):
        rule = get_object_or_404(MatchingRule.objects.select_related('partner'), pk=pk)
        return Response(MatchingRuleSerializer(rule).data)

    def put(self, request, pk):
        rule = get_object_or_404(MatchingRule, pk=pk)
        ser = MatchingRuleWriteSerializer(rule, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response({'detail': 'قانون تطبیق به‌روز شد.'})

    def delete(self, request, pk):
        get_object_or_404(MatchingRule, pk=pk).delete()
        return Response({'detail': 'قانون حذف شد.'})


class AdminRequestMatchView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request, pk):
        financing_request = get_object_or_404(FinancingRequest, pk=pk)
        results = MatchResult.objects.filter(request=financing_request).select_related('partner').order_by('-score')
        return Response({'results': MatchResultSerializer(results, many=True).data})

    def post(self, request, pk):
        from apps.fundzi import matching
        financing_request = get_object_or_404(FinancingRequest, pk=pk)
        matches = matching.run(financing_request)
        return Response({'detail': f'{len(matches)} تطبیق یافت شد.', 'count': len(matches)})


class AdminRequestMatchAssignView(APIView):
    permission_classes = [IsAdminOrOperator]

    def post(self, request, pk, partner_id):
        financing_request = get_object_or_404(FinancingRequest, pk=pk)
        match = get_object_or_404(MatchResult, request=financing_request, partner_id=partner_id)
        if match.status == 'assigned':
            return Response({'detail': 'این درخواست قبلاً به همکار ارسال شده است.'})
        match.status = 'assigned'
        match.assigned_at = timezone.now()
        match.save(update_fields=['status', 'assigned_at'])
        return Response({'detail': 'درخواست با موفقیت به همکار مالی ارسال شد.'})


# ── Phase 3.5: Reports ────────────────────────────────────────────────────────

def _csv_response(filename, headers, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class AdminReportFunnelView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = (
            FinancingRequest.objects
            .values('current_status')
            .annotate(count=Count('id'))
            .order_by('current_status')
        )
        rows = [(r['current_status'] or '—', r['count']) for r in qs]
        if request.query_params.get('export') == 'csv':
            return _csv_response('funnel.csv', ['وضعیت', 'تعداد درخواست'], rows)
        return Response({'results': [{'status': s, 'count': c} for s, c in rows]})


class AdminReportPartnerPerformanceView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        partners = FinancialPartner.objects.filter(is_active=True)
        results = []
        for p in partners:
            assigned = MatchResult.objects.filter(partner=p, status='assigned').count()
            offers_total = PartnerOffer.objects.filter(partner=p).count()
            offers_accepted = PartnerOffer.objects.filter(partner=p, status='accepted').count()
            results.append({
                'partner_id': p.id,
                'partner_name': p.name,
                'assigned_requests': assigned,
                'offers_submitted': offers_total,
                'offers_accepted': offers_accepted,
                'acceptance_rate': round(offers_accepted / offers_total * 100, 1) if offers_total else 0,
            })
        if request.query_params.get('export') == 'csv':
            headers = ['همکار', 'درخواست‌های ارسال‌شده', 'پیشنهادهای ثبت‌شده', 'پیشنهادهای پذیرفته', 'نرخ پذیرش (%)']
            rows = [(r['partner_name'], r['assigned_requests'], r['offers_submitted'], r['offers_accepted'], r['acceptance_rate']) for r in results]
            return _csv_response('partner_performance.csv', headers, rows)
        return Response({'results': results})


class AdminReportMonthlyView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = (
            FinancingRequest.objects
            .annotate(month=TruncMonth('submitted_at'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )
        results = [
            {
                'month': r['month'].strftime('%Y-%m') if r['month'] else '—',
                'total_requests': r['total'],
            }
            for r in qs
        ]
        if request.query_params.get('export') == 'csv':
            rows = [(r['month'], r['total_requests']) for r in results]
            return _csv_response('monthly.csv', ['ماه', 'تعداد درخواست'], rows)
        return Response({'results': results})


# ── Vendor Ecosystem ──────────────────────────────────────────────────────────

class DashboardView(APIView):
    """Returns all data needed to render the user-facing dashboard in one call."""
    permission_classes = []

    def get(self, request):
        investment_services = FinancialService.objects.filter(
            is_active=True, dashboard_section='investment'
        ).order_by('order')
        financing_services = FinancialService.objects.filter(
            is_active=True, dashboard_section='financing'
        ).order_by('order')
        vendor_services = (
            VendorService.objects
            .filter(is_active=True, vendor__is_active=True)
            .select_related('vendor')
            .order_by('vendor__order', 'order')
        )
        return Response({
            'investment': ServiceListSerializer(investment_services, many=True).data,
            'financing': ServiceListSerializer(financing_services, many=True).data,
            'vendor_services': VendorServiceSerializer(vendor_services, many=True).data,
        })


class VendorListView(APIView):
    permission_classes = []

    def get(self, request):
        vendor_type = request.query_params.get('type')
        qs = Vendor.objects.filter(is_active=True).prefetch_related('services').order_by('order', 'name')
        if vendor_type in ('financial', 'non_financial'):
            qs = qs.filter(vendor_type=vendor_type)
        return Response({'results': VendorSerializer(qs, many=True).data})


class VendorDetailView(APIView):
    permission_classes = []

    def get(self, request, slug):
        vendor = get_object_or_404(
            Vendor.objects.prefetch_related('services'),
            slug=slug, is_active=True,
        )
        return Response(VendorSerializer(vendor).data)


class VendorServiceListView(APIView):
    permission_classes = []

    def get(self, request):
        category = request.query_params.get('category')
        vendor_type = request.query_params.get('vendor_type')
        qs = (
            VendorService.objects
            .filter(is_active=True, vendor__is_active=True)
            .select_related('vendor')
            .order_by('vendor__order', 'order')
        )
        if category:
            qs = qs.filter(category=category)
        if vendor_type in ('financial', 'non_financial'):
            qs = qs.filter(vendor__vendor_type=vendor_type)
        return Response({'results': VendorServiceSerializer(qs, many=True).data})


class VendorServiceApplyView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def post(self, request, slug):
        vendor_service = get_object_or_404(VendorService, slug=slug, is_active=True, vendor__is_active=True)
        financing_request_id = request.data.get('financing_request_id')
        financing_request = None
        if financing_request_id:
            financing_request = get_object_or_404(
                FinancingRequest, pk=financing_request_id, user=request.user
            )
        if VendorApplication.objects.filter(
            user=request.user,
            vendor_service=vendor_service,
            status__in=('pending', 'under_review', 'awaiting_info'),
        ).exists():
            raise ValidationError({'detail': 'شما در حال حاضر یک درخواست فعال برای این سرویس دارید.'})
        application = VendorApplication.objects.create(
            user=request.user,
            vendor_service=vendor_service,
            financing_request=financing_request,
            user_notes=request.data.get('user_notes', ''),
        )
        return Response(
            VendorApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )


class UserVendorApplicationListView(APIView):
    permission_classes = [IsAuthenticatedJSON]

    def get(self, request):
        qs = (
            VendorApplication.objects
            .filter(user=request.user)
            .select_related('vendor_service', 'vendor_service__vendor')
            .order_by('-submitted_at')
        )
        return Response({'results': VendorApplicationSerializer(qs, many=True).data})


class AdminVendorApplicationListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = (
            VendorApplication.objects
            .select_related('user', 'vendor_service', 'vendor_service__vendor')
            .order_by('-submitted_at')
        )
        svc_slug = request.query_params.get('vendor_service')
        app_status = request.query_params.get('status')
        if svc_slug:
            qs = qs.filter(vendor_service__slug=svc_slug)
        if app_status:
            qs = qs.filter(status=app_status)
        return Response(paginate(request, qs, lambda a: VendorApplicationSerializer(a).data))

    def patch(self, request, pk=None):
        if pk is None:
            raise ValidationError({'detail': 'pk required'})
        application = get_object_or_404(VendorApplication, pk=pk)
        new_status = request.data.get('status')
        valid = [c[0] for c in VendorApplication.STATUS_CHOICES]
        if new_status and new_status not in valid:
            raise ValidationError({'status': 'وضعیت انتخاب‌شده معتبر نیست.'})
        if new_status:
            application.status = new_status
        if 'vendor_notes' in request.data:
            application.vendor_notes = request.data['vendor_notes']
        if 'result_data' in request.data:
            application.result_data = request.data['result_data']
        application.save()
        return Response(VendorApplicationSerializer(application).data)


class AdminVendorListView(APIView):
    permission_classes = [IsAdminOrOperator]

    def get(self, request):
        qs = Vendor.objects.prefetch_related('services').order_by('order', 'name')
        return Response({'results': VendorSerializer(qs, many=True).data})

    def post(self, request):
        data = request.data
        name = (data.get('name') or '').strip()
        slug = (data.get('slug') or '').strip()
        if not name or not slug:
            raise ValidationError({'name': 'نام و slug الزامی است.'})
        vendor = Vendor.objects.create(
            name=name,
            slug=slug,
            description=data.get('description', ''),
            vendor_type=data.get('vendor_type', 'non_financial'),
            logo_url=data.get('logo_url', ''),
            website=data.get('website', ''),
            is_active=parse_bool(data.get('is_active'), True),
            order=int(data.get('order') or 0),
        )
        return Response(VendorSerializer(vendor).data, status=status.HTTP_201_CREATED)
