from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
import datetime
from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from django.db.models import Prefetch
from datetime import datetime, timedelta

from apps.account.api.serializers import UserSummerySerializer
from apps.appointment.api.filters import QueueFilter, AppointmentFilter
from apps.appointment.models import Queue, Appointment
from apps.appointment.api.serializers import QueueSerializer, AppointmentSerializer, AppointmentListSerializer
from apps.lab.api.serializers import StatusSerializer
from apps.lab.tasks import check_pending_appointment
from apps.lab.models import Status as LabStatus

class QueueListCreateView(ListCreateAPIView):
    # queryset = Queue.objects.all()
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = QueueFilter

    def get_queryset(self):
        return Queue.objects.select_related('experiment').prefetch_related(
            Prefetch('appointments',
                queryset=Appointment.objects.select_related('reserved_by'),
                to_attr='prefetched_appointments'
            )
        )

class QueueDetailView(RetrieveUpdateDestroyAPIView):
    # queryset = Queue.objects.all()
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Queue.objects.select_related('experiment').prefetch_related(
            Prefetch(
                'appointments',
                queryset=Appointment.objects.select_related('reserved_by'),
                to_attr='prefetched_appointments'
            )
        )

class OwnedAppointmentListView(ListAPIView):
    # queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    # pagination_class = DefaultPagination

    def get_queryset(self):
        qs = (
            Appointment.objects.filter(request__owner=self.request.user)
            | Appointment.objects.filter(reserved_by=self.request.user)
        )
        return qs.distinct().select_related(
                  'reserved_by',
                  'queue',
                  'queue__experiment',
                  'request',
                  'request__parent_request',
              ).prefetch_related(
                  'request__request_status__step',
              ).order_by('-id')


class AppointmentListCreateView(ListCreateAPIView):
    #queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.select_related(
                    'reserved_by',
                    'queue',
                    'queue__experiment',
                    'request',
                    'request__parent_request',
                ).prefetch_related(
                    'request__request_status__step',
                )

    def perform_create(self, serializer):
        queue = serializer.validated_data['queue']
        start_time = serializer.validated_data['start_time']

        if queue.status != 'active':
            raise ValidationError("این صف فعال نیست و نمی‌توان نوبت رزرو کرد.")

        if not queue.is_time_valid(start_time):
            raise ValidationError("زمان درخواست شده با بازه زمانی صف هماهنگ نیست.")

        serializer = serializer.save()
        check_pending_appointment.apply_async((serializer.id,), countdown=30 * 60)


class AppointmentDetailView(RetrieveUpdateDestroyAPIView):
    # queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.select_related(
                    'reserved_by',
                    'queue',
                    'queue__experiment',
                    'request',
                    'request__parent_request',
                ).prefetch_related(
                    'request__request_status__step',
                )

class AvailableAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AppointmentFilter

    def get(self, request):
        filterset = AppointmentFilter(request.GET, queryset=Appointment.objects.all())
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        experiment_id = request.query_params.get('experiment_id')

        if not start_date or not end_date:
            return Response({"error": "start_date و end_date الزامی هستند."}, status=400)

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # queues = Queue.objects.filter(date__range=[start_date, end_date])
        queues = Queue.objects.filter(date__range=[start_date, end_date]).select_related('experiment')

        if experiment_id:
            queues = queues.filter(experiment_id=experiment_id)

        # reserved_appointments = Appointment.objects.filter(queue__in=queues).select_related('reserved_by', 'request')
        reserved_appointments = (
            Appointment.objects.filter(queue__in=queues)
              .select_related(
                  'reserved_by',
                  'request',
                  'queue__experiment',
                  'request__parent_request',
              )
              .prefetch_related(
                  Prefetch(
                    'request__request_status',
                    queryset=LabStatus.objects.select_related('step').order_by('created_at'),
                    to_attr='all_statuses'
                  )
              )
        )

        reserved_map = {(appt.queue_id, appt.start_time): appt for appt in reserved_appointments}
        all_appointments = []

        for queue in queues:
            current_time = queue.start_time
            while current_time < queue.end_time:
                end_time = (datetime.combine(datetime.today(), current_time) +
                            timedelta(minutes=queue.time_unit)).time()

                is_in_break_time = False
                if queue.break_start and queue.break_end:
                    if not (end_time <= queue.break_start or current_time >= queue.break_end):
                        is_in_break_time = True

                appt = reserved_map.get((queue.id, current_time))
                if appt:
                    last_status = appt.request.all_statuses[-1] if appt.request and hasattr(appt.request, 'all_statuses') and appt.request.all_statuses else None
                    request_status = StatusSerializer(last_status).data if last_status else None
                    request = appt.request
                    request_id = request.id
                    request_number = request.request_number
                    parent = request.parent_request
                    request_parent_number = parent.request_number if parent else None
                    appointment_id = appt.id
                    reserved_by = appt.reserved_by.id if appt.reserved_by else None
                    reserved_by_obj = UserSummerySerializer(appt.reserved_by).data if appt.reserved_by else None
                    status = appt.status
                else:
                    request_status = None
                    request_id = None
                    request_number = None
                    request_parent_number = None
                    appointment_id = None
                    reserved_by = None
                    reserved_by_obj = None
                    status = "free"

                if not is_in_break_time:
                    all_appointments.append({
                        "appointment_id": appointment_id,
                        "queue_id": queue.id,
                        "date": queue.date,
                        "request_id": request_id,
                        'request_number': request_number,
                        'request_parent_number': request_parent_number,
                        "request_status": request_status,
                        "experiment_name": queue.experiment.name,
                        "start_time": current_time,
                        "end_time": end_time,
                        "status": status,
                        "reserved_by": reserved_by,
                        "reserved_by_obj": reserved_by_obj
                    })

                current_time = end_time

        return Response(all_appointments)


class CancelAppointmentView(APIView):
    def post(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(id=appointment_id)

            if appointment.status in ['reserved', 'canceled']:
                return Response({"error": "این نوبت قابل لغو نیست یا قبلاً لغو شده است."},
                                status=status.HTTP_400_BAD_REQUEST)

            appointment.status = 'canceled'
            appointment.save()

            return Response({"success": "نوبت شما با موفقیت لغو شد."}, status=status.HTTP_200_OK)

        except Appointment.DoesNotExist:
            return Response({"error": "نوبت مورد نظر یافت نشد."}, status=status.HTTP_404_NOT_FOUND)