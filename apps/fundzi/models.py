import random
import string
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class FinancialService(models.Model):
    SERVICE_TYPES = (
        ('gold_backed', 'Gold-backed financing'),
        ('property_backed', 'Property-backed financing'),
        ('other', 'Other'),
    )

    title = models.CharField(max_length=255, verbose_name='عنوان')
    slug = models.SlugField(max_length=120, unique=True)
    short_description = models.TextField(blank=True, verbose_name='توضیح کوتاه')
    full_description = models.TextField(blank=True, verbose_name='توضیح کامل')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, default='other')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    rules_config = models.JSONField(default=dict, blank=True, verbose_name='تنظیمات و قواعد')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سرویس مالی'
        verbose_name_plural = 'سرویس‌های مالی'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def first_workflow_step(self):
        workflow = getattr(self, 'workflow', None)
        if not workflow:
            return None
        return workflow.steps.filter(is_initial=True, is_active=True).order_by('order', 'id').first()


class ServiceContent(models.Model):
    CONTENT_TYPES = (
        ('introduction', 'Introduction'),
        ('conditions', 'Conditions'),
        ('required_documents', 'Required documents'),
        ('process_steps', 'Process steps'),
        ('faq', 'FAQ'),
        ('warning', 'Warning'),
        ('help_text', 'Help text'),
    )

    service = models.ForeignKey(FinancialService, related_name='contents', on_delete=models.CASCADE)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPES)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'محتوای سرویس'
        verbose_name_plural = 'محتوای سرویس‌ها'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.service} - {self.content_type}'


class DynamicForm(models.Model):
    service = models.OneToOneField(FinancialService, related_name='form', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فرم پویا'
        verbose_name_plural = 'فرم‌های پویا'

    def __str__(self):
        return self.title


class FormField(models.Model):
    FIELD_TYPES = (
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('number', 'Number'),
        ('select', 'Select'),
        ('multi_select', 'Multi select'),
        ('boolean', 'Boolean'),
        ('date', 'Date'),
        ('file', 'File'),
        ('money', 'Money'),
        ('percentage', 'Percentage'),
    )

    form = models.ForeignKey(DynamicForm, related_name='fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    key = models.SlugField(max_length=120)
    field_type = models.CharField(max_length=30, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.TextField(blank=True)
    options = models.JSONField(default=list, blank=True)
    validation_config = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'فیلد فرم'
        verbose_name_plural = 'فیلدهای فرم'
        ordering = ['order', 'id']
        unique_together = ('form', 'key')

    def __str__(self):
        return f'{self.form} - {self.label}'


class Workflow(models.Model):
    service = models.OneToOneField(FinancialService, related_name='workflow', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'گردش کار فندزی'
        verbose_name_plural = 'گردش کارهای فندزی'

    def __str__(self):
        return self.name


class WorkflowStep(models.Model):
    workflow = models.ForeignKey(Workflow, related_name='steps', on_delete=models.CASCADE)
    key = models.SlugField(max_length=120)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_initial = models.BooleanField(default=False)
    is_terminal = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مرحله گردش کار فندزی'
        verbose_name_plural = 'مراحل گردش کار فندزی'
        ordering = ['order', 'id']
        unique_together = ('workflow', 'key')

    def __str__(self):
        return self.title


class FinancingRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='fundzi_requests', on_delete=models.PROTECT)
    service = models.ForeignKey(FinancialService, related_name='requests', on_delete=models.PROTECT)
    current_workflow_step = models.ForeignKey(
        WorkflowStep,
        related_name='current_requests',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    current_status = models.CharField(max_length=120, blank=True)
    tracking_code = models.CharField(max_length=32, unique=True, blank=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    admin_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='assigned_fundzi_requests',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'درخواست تأمین مالی'
        verbose_name_plural = 'درخواست‌های تأمین مالی'
        ordering = ['-submitted_at']

    def __str__(self):
        return self.tracking_code or f'{self.service} #{self.pk}'

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            self.tracking_code = self.generate_tracking_code()
        if not self.current_workflow_step:
            self.current_workflow_step = self.service.first_workflow_step()
        if self.current_workflow_step:
            self.current_status = self.current_workflow_step.key
        super().save(*args, **kwargs)

    @classmethod
    def generate_tracking_code(cls):
        today = timezone.localdate().strftime('%Y%m%d')
        alphabet = string.ascii_uppercase + string.digits
        while True:
            suffix = ''.join(random.SystemRandom().choice(alphabet) for _ in range(4))
            code = f'FNDZ-{today}-{suffix}'
            if not cls.objects.filter(tracking_code=code).exists():
                return code

    def change_status(self, step, changed_by=None, note=''):
        if step.workflow_id != self.service.workflow.id:
            raise ValidationError('مرحله انتخاب‌شده متعلق به گردش کار این سرویس نیست.')
        previous = self.current_status
        self.current_workflow_step = step
        self.current_status = step.key
        self.save(update_fields=['current_workflow_step', 'current_status', 'updated_at'])
        return RequestHistory.objects.create(
            request=self,
            from_status=previous,
            to_status=step.key,
            changed_by=changed_by,
            note=note,
        )


class RequestFieldValue(models.Model):
    request = models.ForeignKey(FinancingRequest, related_name='field_values', on_delete=models.CASCADE)
    field = models.ForeignKey(FormField, related_name='values', on_delete=models.PROTECT)
    value_text = models.TextField(blank=True)
    value_number = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    value_json = models.JSONField(null=True, blank=True)
    file = models.FileField(upload_to='fundzi/field-values/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مقدار فیلد درخواست'
        verbose_name_plural = 'مقادیر فیلدهای درخواست'
        unique_together = ('request', 'field')

    def __str__(self):
        return f'{self.request} - {self.field.key}'

    @property
    def value(self):
        if self.value_json is not None:
            return self.value_json
        if self.value_number is not None:
            return self.value_number
        return self.value_text


class RequestAttachment(models.Model):
    request = models.ForeignKey(FinancingRequest, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='fundzi/attachments/')
    document_type = models.CharField(max_length=120, blank=True)
    title = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'پیوست درخواست'
        verbose_name_plural = 'پیوست‌های درخواست'

    def __str__(self):
        return self.title or self.document_type or str(self.request)


class RequestHistory(models.Model):
    request = models.ForeignKey(FinancingRequest, related_name='history', on_delete=models.CASCADE)
    from_status = models.CharField(max_length=120, blank=True, null=True)
    to_status = models.CharField(max_length=120)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تاریخچه درخواست'
        verbose_name_plural = 'تاریخچه درخواست‌ها'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.request}: {self.from_status} -> {self.to_status}'


class InternalNote(models.Model):
    request = models.ForeignKey(FinancingRequest, related_name='internal_notes', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'یادداشت داخلی'
        verbose_name_plural = 'یادداشت‌های داخلی'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.request} - {self.created_at:%Y-%m-%d}'


class FinancialPartner(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=120, blank=True)
    service_categories = models.JSONField(default=list, blank=True)
    min_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    max_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    accepted_collateral_types = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'همکار مالی'
        verbose_name_plural = 'همکاران مالی'

    def __str__(self):
        return self.name


def decimal_from_payload(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value).replace(',', ''))
    except (InvalidOperation, TypeError):
        raise ValidationError('عدد وارد شده معتبر نیست.')
