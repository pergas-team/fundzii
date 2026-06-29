import django_filters
from django.db.models import Q

from apps.lab.models import Parameter, FormResponse, Laboratory, Request, Device, Experiment


class ParameterFilter(django_filters.FilterSet):
    experiment = django_filters.CharFilter(field_name='experiment__id', lookup_expr='exact', label='filter by experiment id')  # lookup_expr='icontains',

    search = django_filters.CharFilter(method='parameter_search')

    class Meta:
        model = Parameter
        fields = ['experiment', 'search']

    def parameter_search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value))


class FormResponseFilter(django_filters.FilterSet):
    request = django_filters.CharFilter(field_name='request_id', lookup_expr='exact', label='filter by experiment id')

    class Meta:
        model = FormResponse
        fields = ['request']


class LaboratoryFilter(django_filters.FilterSet):
    department = django_filters.CharFilter(field_name='department_id', lookup_expr='exact')
    search_department = django_filters.CharFilter(field_name='department_id', lookup_expr='exact')

    search = django_filters.CharFilter(method='lab_search')

    class Meta:
        model = Laboratory
        fields = ['department', 'search_department', 'search']

    def lab_search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(name_en__icontains=value) |
                               Q(description__icontains=value) | Q(experiments__name__icontains=value) |
                               Q(experiments__name_en__icontains=value)).distinct()


class RequestFilter(django_filters.FilterSet):
    experiment_name = django_filters.CharFilter(field_name='experiment__name', lookup_expr='icontains', label='filter by experiment name')  # lookup_expr='icontains',
    experiment_name_en = django_filters.CharFilter(field_name='experiment__name_en', lookup_expr='icontains', label='filter by experiment name en')  # lookup_expr='icontains',
    experiment_id = django_filters.CharFilter(field_name='experiment_id', lookup_expr='exact', label='filter by experiment name en')  # lookup_expr='icontains',
    laboratory_id = django_filters.CharFilter(field_name='experiment__laboratory_id', lookup_expr='exact', label='filter by experiment name en')  # lookup_expr='icontains',
    request_number = django_filters.CharFilter(field_name='request_number', lookup_expr='exact', label='filter by request number')  # lookup_expr='icontains',

    owner_first_name = django_filters.CharFilter(field_name='owner__first_name', lookup_expr='icontains', label='filter by owner first name')  # lookup_expr='icontains',
    owner_last_name = django_filters.CharFilter(field_name='owner__last_name', lookup_expr='icontains', label='filter by owner last name')  # lookup_expr='icontains',
    owner_national_id = django_filters.CharFilter(field_name='owner__national_id', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',
    owner_company_national_id = django_filters.CharFilter(field_name='owner__company_national_id', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',
    owner_company_name = django_filters.CharFilter(field_name='owner__company_name', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',
    owner_company_economic_number = django_filters.CharFilter(field_name='owner__company_economic_number', lookup_expr='icontains', label='filter by owner national id')  # lookup_expr='icontains',

    start_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='filter by created_at')  # lookup_expr='icontains',
    end_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='filter by created_at')  # lookup_expr='icontains',

    owner_fullname = django_filters.CharFilter(method='owner_fullname_search')
    search = django_filters.CharFilter(method='request_search')

    request_status = django_filters.CharFilter(method="request_status_field")

    def request_status_field(self, queryset, name, value):
        return queryset.filter(request_status__step__id=value, request_status__complete=False)

    class Meta:
        model = Request
        fields = ['experiment', 'search', 'experiment_name', 'experiment_name_en', 'request_number', 'owner_first_name',
                  'owner_last_name', 'owner_fullname', 'owner_national_id', 'request_status']

    def owner_fullname_search(self, queryset, name, value):
        qs = None
        for val in value.split(' '):
            qs_filter = queryset
            if qs is None:
                qs = qs_filter.filter(Q(owner__first_name__icontains=val) | Q(owner__last_name__icontains=val))
            else:
                qs = qs | qs_filter.filter(Q(owner__first_name__icontains=val) | Q(owner__last_name__icontains=val))
        return qs.distinct()
        # return queryset.filter(Q(owner__first_name__icontains=value) | Q(owner__last_name__icontains=value))

    def request_search(self, queryset, name, value):
        return queryset.filter(Q(experiment__name__icontains=value) | Q(request_number__exact=value))


class DeviceFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='device_search')

    class Meta:
        model = Device
        fields = ['search']

    def device_search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class ExperimentFilter(django_filters.FilterSet):
    department_id = django_filters.CharFilter(field_name='laboratory__department_id', lookup_expr='exact', label='filter by department_id')  # lookup_expr='icontains',
    laboratory_id = django_filters.CharFilter(field_name='laboratory_id', lookup_expr='exact', label='filter by laboratory_id')  # lookup_expr='icontains',
    search = django_filters.CharFilter(method='experiment_search')

    class Meta:
        model = Experiment
        fields = ['search']

    def experiment_search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(name_en__icontains=value))