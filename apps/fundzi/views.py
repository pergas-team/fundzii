from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.fundzi.models import FinancialService, FinancingRequest
from apps.fundzi.services import create_financing_request


def service_list_page(request):
    services = FinancialService.objects.filter(is_active=True)
    return render(request, 'fundzi/service_list.html', {'services': services})


def service_detail_page(request, slug):
    service = get_object_or_404(FinancialService, slug=slug, is_active=True)
    contents = service.contents.filter(is_active=True)
    return render(request, 'fundzi/service_detail.html', {'service': service, 'contents': contents})


@login_required
def service_request_page(request, slug):
    service = get_object_or_404(FinancialService, slug=slug, is_active=True)
    form = getattr(service, 'form', None)
    if not form:
        messages.error(request, 'برای این سرویس هنوز فرم تعریف نشده است.')
        return redirect('fundzi-service-page', slug=service.slug)

    fields = form.fields.filter(is_active=True)
    form_data = {}
    field_errors = {}

    if request.method == 'POST':
        form_data = request.POST.dict()
        try:
            financing_request = create_financing_request(service, request.user, form_data, request.FILES)
            messages.success(request, f'درخواست شما با کد پیگیری {financing_request.tracking_code} ثبت شد.')
            return redirect('fundzi-request-page', pk=financing_request.pk)
        except ValidationError as exc:
            if hasattr(exc, 'message_dict'):
                field_errors = exc.message_dict
            else:
                messages.error(request, 'اطلاعات فرم معتبر نیست.')
                field_errors = {'__all__': exc.messages}

    return render(
        request,
        'fundzi/request_form.html',
        {
            'service': service,
            'form': form,
            'fields': fields,
            'form_data': form_data,
            'field_errors': field_errors,
        },
    )


@login_required
def request_dashboard_page(request):
    requests = FinancingRequest.objects.filter(user=request.user).select_related('service', 'current_workflow_step')
    return render(request, 'fundzi/request_dashboard.html', {'requests': requests})


@login_required
def request_detail_page(request, pk):
    financing_request = get_object_or_404(
        FinancingRequest.objects.select_related('service', 'current_workflow_step'),
        pk=pk,
        user=request.user,
    )
    field_values = financing_request.field_values.select_related('field')
    history = financing_request.history.select_related('changed_by')
    return render(
        request,
        'fundzi/request_detail.html',
        {
            'request_obj': financing_request,
            'field_values': field_values,
            'history': history,
        },
    )
