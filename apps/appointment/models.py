from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta, time

from apps.account.models import User
from apps.lab.models import Experiment, Request


class Queue(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name="queues", verbose_name='آزمون')
    date = models.DateField(verbose_name="تاریخ")
    start_time = models.TimeField(verbose_name="زمان شروع صف")
    end_time = models.TimeField(verbose_name="زمان پایان صف")
    break_start = models.TimeField(null=True, blank=True, verbose_name="زمان شروع استراحت")
    break_end = models.TimeField(null=True, blank=True, verbose_name="زمان پایان استراحت")
    time_unit = models.IntegerField(verbose_name="مدت زمان نوبت (دقیقه)")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="وضعیت صف")

    def __str__(self):
        return f'{self.experiment}, {self.date}'

    def is_time_valid(self, requested_start):
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        requested_minutes = requested_start.hour * 60 + requested_start.minute
        return (requested_minutes - start_minutes) % self.time_unit == 0

    def get_available_slots(self):
        slots = []
        current_time = datetime.combine(datetime.today(), self.start_time)
        end_time = datetime.combine(datetime.today(), self.end_time)

        appointments = self.appointments.order_by('start_time')
        for appointment in appointments:
            appointment_start = datetime.combine(datetime.today(), appointment.start_time)
            if current_time < appointment_start:
                slots.append((current_time.time(), appointment_start.time()))
            current_time = appointment_start + timedelta(minutes=self.time_unit)

        if current_time < end_time:
            slots.append((current_time.time(), end_time.time()))

        return slots


class Appointment(models.Model):
    queue = models.ForeignKey(Queue, related_name="appointments", on_delete=models.CASCADE, verbose_name="صف")
    request = models.ForeignKey(Request, related_name="appointments", on_delete=models.CASCADE, null=True, blank=True, verbose_name="درخواست")
    start_time = models.TimeField(verbose_name="زمان شروع نوبت")
    status = models.CharField(max_length=50, default="free", verbose_name="وضعیت نوبت",
                              choices=[("free", "آزاد"), ("reserved", "رزرو شده"), ("pending", "در انتظار پرداخت"), ("canceled", "لغو شده")])
    reserved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments", verbose_name="رزرو شده توسط"
    )
    reserved_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="زمان ایجاد")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True,  verbose_name="زمان به‌روزرسانی")


    def end_time(self):
        total_minutes = self.start_time.hour * 60 + self.start_time.minute + self.queue.time_unit
        hours, minutes = divmod(total_minutes, 60)
        hours = hours % 24
        return time(hour=hours, minute=minutes)

    def date(self):
        return self.queue.date
