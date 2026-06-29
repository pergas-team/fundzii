import django_filters

from apps.order.models import PaymentRecord


class PaymentRecordFilter(django_filters.FilterSet):
    experiment_name = django_filters.CharFilter(field_name='order__request__experiment__name', lookup_expr='icontains', label='filter by experiment name')  # lookup_expr='icontains',
    experiment_name_en = django_filters.CharFilter(field_name='order__request__experiment__name_en', lookup_expr='icontains', label='filter by experiment name en')  # lookup_expr='icontains',
    experiment_id = django_filters.CharFilter(field_name='order__request__experiment_id', lookup_expr='exact', label='filter by experiment name en')  # lookup_expr='icontains',
    laboratory_id = django_filters.CharFilter(field_name='order__request__experiment__laboratory_id', lookup_expr='exact', label='filter by experiment name en')  # lookup_expr='icontains',
    request_number = django_filters.CharFilter(field_name='order__request__request_number', lookup_expr='exact', label='filter by request number')  # lookup_expr='icontains',
    request_id = django_filters.CharFilter(field_name='order__request_id', lookup_expr='exact', label='filter by request number')  # lookup_expr='icontains',

    payer_first_name = django_filters.CharFilter(field_name='payer__first_name', lookup_expr='icontains', label='filter by owner first name')  # lookup_expr='icontains',
    payer_last_name = django_filters.CharFilter(field_name='payer__last_name', lookup_expr='icontains', label='filter by owner last name')  # lookup_expr='icontains',
    payer_national_id = django_filters.CharFilter(field_name='payer__national_id', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',
    payer_company_national_id = django_filters.CharFilter(field_name='payer__company_national_id', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',
    payer_company_name = django_filters.CharFilter(field_name='payer__company_name', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',
    payer_company_economic_number = django_filters.CharFilter(field_name='payer__company_economic_number', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',


    start_date = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label='filter by created_at')  # lookup_expr='icontains',
    end_date = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label='filter by created_at')  # lookup_expr='icontains',

    # search = django_filters.CharFilter(method='request_search')

    class Meta:
        model = PaymentRecord
        fields = ['start_date', 'end_date']