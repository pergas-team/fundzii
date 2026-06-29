import django_filters
from django.db.models import Q

from apps.form.models import Form


class FormFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='form_search')

    class Meta:
        model = Form
        fields = ['search']

    def form_search(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value))