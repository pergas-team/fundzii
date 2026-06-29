from django_filters import rest_framework as filters
from apps.appointment.models import Queue, Appointment


class QueueFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = Queue
        fields = ['experiment', 'start_date', 'end_date']


class AppointmentFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="queue__date", lookup_expr="gte")
    end_date = filters.DateFilter(field_name="queue__date", lookup_expr="lte")
    status = filters.CharFilter(method="filter_status")
    experiment_id = filters.NumberFilter(field_name="queue__experiment_id")

    class Meta:
        model = Appointment
        fields = ['start_date', 'end_date', 'status', 'experiment_id']

    def filter_status(self, queryset, name, value):
        if value == "reserved":
            return queryset.filter(status="reserved")
        elif value == "free":
            return queryset.none()
        return queryset