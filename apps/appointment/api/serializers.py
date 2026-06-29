from rest_framework import serializers
import jdatetime
from django.db.models import Prefetch

from apps.account.api.serializers import UserSummerySerializer
from apps.appointment.models import Queue, Appointment
from datetime import datetime, timedelta, time

from apps.lab.models import WorkflowStep


class AppointmentSerializerLite(serializers.ModelSerializer):
    reserved_by_obj = UserSummerySerializer(read_only=True, source='reserved_by')

    class Meta:
        model = Appointment
        fields = ['start_time', 'status', 'reserved_by', 'reserved_by_obj']


class QueueSerializer(serializers.ModelSerializer):
    appointments = AppointmentSerializerLite(many=True, read_only=True, source='prefetched_appointments')

    class Meta:
        model = Queue
        fields = '__all__'


class AppointmentListSerializer(serializers.Serializer):
    queue_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    status = serializers.CharField()
    request_id = serializers.IntegerField(allow_null=True)
    request_status = serializers.CharField()
    reserved_by = serializers.IntegerField(allow_null=True)
    reserved_by_obj = UserSummerySerializer(allow_null=True)


class WorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ["id", "name", "description", "step_color"]


class AppointmentSerializer(serializers.ModelSerializer):
    reserved_by_obj = UserSummerySerializer(read_only=True, source='reserved_by')
    extra_fields = serializers.SerializerMethodField(read_only=True)
    end_time = serializers.SerializerMethodField(read_only=True)
    date = serializers.SerializerMethodField(read_only=True)
    request_status = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'

    def validate(self, data):
        queue = data['queue']
        start_time = data['start_time']
        reserved_by = data['reserved_by']
        experiment = queue.experiment
        request = data['request']

        if queue.status != 'active':
            raise serializers.ValidationError({"queue": "این صف فعال نیست و نمی‌توان نوبت رزرو کرد."})

        if experiment.appointment_limit_hours > 0:
            today_jalali = jdatetime.date.today()
            start_jalali = jdatetime.date(today_jalali.year, today_jalali.month, 1)
            if today_jalali.month == 12:
                end_jalali = jdatetime.date(today_jalali.year + 1, 1, 1) - jdatetime.timedelta(days=1)
            else:
                end_jalali = jdatetime.date(today_jalali.year, today_jalali.month + 1, 1) - jdatetime.timedelta(days=1)

            start_gregorian = start_jalali.togregorian()
            end_gregorian = end_jalali.togregorian()

            previous_appointments = Appointment.objects.filter(
                queue__experiment=experiment,
                reserved_by=reserved_by,
                queue__date__gte=start_gregorian,
                queue__date__lte=end_gregorian,
                status='reserved'
            )

            total_reserved_minutes = sum(app.queue.time_unit for app in previous_appointments)
            total_reserved_hours = total_reserved_minutes / 60

            if total_reserved_hours >= experiment.appointment_limit_hours:
                raise serializers.ValidationError({
                    "error": f"شما نمی‌توانید بیشتر از {experiment.appointment_limit_hours} ساعت نوبت برای این آزمایش در ۳۰ روز گذشته داشته باشید. (مجموع نوبت شما {total_reserved_hours} ساعت)"
                })

        total_minutes = start_time.hour * 60 + start_time.minute + queue.time_unit
        hours, minutes = divmod(total_minutes, 60)
        hours = hours % 24
        new_end_time = time(hour=hours, minute=minutes)

        conflicting_appointments = Appointment.objects.filter(queue=queue)
        if self.instance:
            conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)

        for appointment in conflicting_appointments:
            appointment_end_time = (datetime.combine(datetime.today(), appointment.start_time) +
                                    timedelta(minutes=queue.time_unit)).time()
            if not (new_end_time <= appointment.start_time or start_time >= appointment_end_time):
                raise serializers.ValidationError(
                    {"time": f"این بازه زمانی قبلاً رزرو شده است: {appointment.start_time} تا {appointment_end_time}"}
                )

        if experiment.need_turn and experiment.prepayment_amount > 0:
            data['status'] = 'pending'
            request.has_prepayment = True
            request.save()
            request.parent_request.has_prepayment = True
            request.parent_request.save()
        else:
            data['status'] = 'reserved'

        return data

    def get_request_status(self, obj):
        # last = obj.all_statuses.all().order_by('-id').first()
        last = getattr(obj, 'all_statuses', [])
        if last:
            # return WorkflowStepSerializer(last.step).data
            return WorkflowStepSerializer(last[-1].step).data
        return None

    def get_end_time(self, obj):
        return obj.end_time()

    def get_date(self, obj):
        return obj.date()

    def get_extra_fields(self, obj):
        req = obj.request
        if req:
            req_id = req.id
            req_num = req.request_number
            parent = req.parent_request
            parent_num = parent.request_number if parent else None
        else:
            req_id = req_num = parent_num = None
        exp_name = obj.queue.experiment.name if obj.queue.experiment else None
        return {
            'request_id': req_id,
            'request_number': req_num,
            'request_parent_number': parent_num,
            'experiment_name': exp_name,
            'queue_status': obj.queue.status,
        }