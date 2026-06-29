import django_filters
from apps.account.models import User, GrantRecord, GrantRequest


class UserFilter(django_filters.FilterSet):
    user_type = django_filters.CharFilter(field_name='user_type', lookup_expr='exact', label='filter by user type (staff/customer)')  # lookup_expr='icontains',
    account_type = django_filters.CharFilter(field_name='account_type', lookup_expr='exact', label='filter by account type (personal/business)')  # lookup_expr='icontains',
    role = django_filters.CharFilter(field_name='role__id', lookup_expr='exact', label='filter by role id')  # lookup_expr='icontains',
    national_id = django_filters.CharFilter(field_name='national_id', lookup_expr='icontains', label='filter by national id')  # lookup_expr='icontains',
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains', label='filter by username')  # lookup_expr='icontains',
    company_national_id = django_filters.CharFilter(field_name='company_national_id', lookup_expr='icontains', label='filter by company_national_id')  # lookup_expr='icontains',
    company_name = django_filters.CharFilter(field_name='company_name', lookup_expr='icontains', label='filter by company_name')  # lookup_expr='icontains',
    company_economic_number = django_filters.CharFilter(field_name='company_economic_number', lookup_expr='icontains', label='filter by company_economic_number')  # lookup_expr='icontains',

    start_date = django_filters.DateFilter(field_name='date_joined', lookup_expr='gte', label='filter by created_at')  # lookup_expr='icontains',
    end_date = django_filters.DateFilter(field_name='date_joined', lookup_expr='lte', label='filter by created_at')  # lookup_expr='icontains',

    class Meta:
        model = User
        fields = ['user_type', 'account_type', 'national_id', 'role']


class GrantRecordFilter(django_filters.FilterSet):

    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='filter by created_at')  # lookup_expr='icontains',
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='filter by created_at')  # lookup_expr='icontains',

    class Meta:
        model = GrantRecord
        fields = ['start_date', 'end_date']


class GrantRequestFilter(django_filters.FilterSet):

    start_date = django_filters.DateFilter(field_name='datetime', lookup_expr='gte', label='filter by created_at')  # lookup_expr='icontains',
    end_date = django_filters.DateFilter(field_name='datetime', lookup_expr='lte', label='filter by created_at')  # lookup_expr='icontains',

    class Meta:
        model = GrantRequest
        fields = ['start_date', 'end_date']