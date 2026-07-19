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
        ('crowdfunding', 'Crowdfunding'),
        ('other', 'Other'),
    )
    DASHBOARD_SECTIONS = (
        ('investment', 'سرمایه‌گذاری'),
        ('financing', 'تامین مالی'),
    )

    title = models.CharField(max_length=255, verbose_name='عنوان')
    slug = models.SlugField(max_length=120, unique=True)
    short_description = models.TextField(blank=True, verbose_name='توضیح کوتاه')
    full_description = models.TextField(blank=True, verbose_name='توضیح کامل')
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, default='other')
    dashboard_section = models.CharField(
        max_length=30, choices=DASHBOARD_SECTIONS, default='financing',
        verbose_name='بخش داشبورد',
    )
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
    # Conditional group: this field is only shown/validated when the parent
    # (a select/multi_select field of the same form) has `group_option` selected.
    parent = models.ForeignKey(
        'self',
        related_name='children',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='فیلد والد (گروه)',
    )
    group_option = models.CharField(max_length=255, blank=True, verbose_name='گزینه فعال‌کننده گروه')
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


class Notification(models.Model):
    KIND_CHOICES = (
        ('request_submitted', 'Request submitted'),
        ('status_changed', 'Status changed'),
        ('general', 'General'),
    )
    CHANNEL_CHOICES = (
        ('in_app', 'In-app'),
        ('sms', 'SMS'),
        ('email', 'Email'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='fundzi_notifications', on_delete=models.CASCADE)
    request = models.ForeignKey(
        FinancingRequest,
        related_name='notifications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=40, choices=KIND_CHOICES, default='general')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='in_app')
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'اعلان'
        verbose_name_plural = 'اعلان‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f'{self.user} - {self.title}'

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


# ── Phase 3.1: Partner Portal ─────────────────────────────────────────────────

class PartnerUser(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('analyst', 'Analyst'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='partner_memberships',
        on_delete=models.CASCADE,
    )
    partner = models.ForeignKey(
        FinancialPartner,
        related_name='members',
        on_delete=models.CASCADE,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyst')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'partner')
        verbose_name = 'کاربر همکار'
        verbose_name_plural = 'کاربران همکار'

    def __str__(self):
        return f'{self.user} @ {self.partner} ({self.role})'


class PartnerOffer(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    )
    request = models.ForeignKey(
        FinancingRequest,
        related_name='partner_offers',
        on_delete=models.CASCADE,
    )
    partner = models.ForeignKey(
        FinancialPartner,
        related_name='offers',
        on_delete=models.CASCADE,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='submitted_offers',
        on_delete=models.SET_NULL,
        null=True,
    )
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    conditions = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'پیشنهاد همکار'
        verbose_name_plural = 'پیشنهادهای همکار'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.partner} → {self.request} ({self.status})'


# ── Phase 3.2: Matching Engine ────────────────────────────────────────────────

class MatchingRule(models.Model):
    partner = models.ForeignKey(
        FinancialPartner,
        related_name='matching_rules',
        on_delete=models.CASCADE,
    )
    priority = models.PositiveIntegerField(default=0)
    # Supported keys: service_slug, min_amount, max_amount
    conditions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority']
        verbose_name = 'قانون تطبیق'
        verbose_name_plural = 'قوانین تطبیق'

    def __str__(self):
        return f'{self.partner} — priority {self.priority}'


class MatchResult(models.Model):
    STATUS_CHOICES = (
        ('matched', 'Matched'),
        ('assigned', 'Assigned'),
        ('rejected', 'Rejected'),
    )
    request = models.ForeignKey(
        FinancingRequest,
        related_name='match_results',
        on_delete=models.CASCADE,
    )
    partner = models.ForeignKey(
        FinancialPartner,
        related_name='match_results',
        on_delete=models.CASCADE,
    )
    score = models.PositiveIntegerField(default=0)
    matched_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='matched')
    assigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('request', 'partner')
        ordering = ['-score']
        verbose_name = 'نتیجه تطبیق'
        verbose_name_plural = 'نتایج تطبیق'

    def __str__(self):
        return f'{self.request} ↔ {self.partner} (score={self.score})'


# ── Vendor Ecosystem ─────────────────────────────────────────────────────────

class Vendor(models.Model):
    VENDOR_TYPE_CHOICES = (
        ('financial', 'مالی'),
        ('non_financial', 'غیرمالی'),
    )

    name = models.CharField(max_length=255, verbose_name='نام')
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, verbose_name='توضیحات')
    vendor_type = models.CharField(max_length=30, choices=VENDOR_TYPE_CHOICES, verbose_name='نوع')
    logo_url = models.URLField(blank=True, verbose_name='لوگو')
    website = models.URLField(blank=True, verbose_name='وب‌سایت')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'وندور'
        verbose_name_plural = 'وندورها'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class VendorService(models.Model):
    CATEGORY_CHOICES = (
        ('crowdfunding', 'تامین مالی جمعی'),
        ('business_consulting', 'مشاوره کسب‌وکار'),
        ('legal', 'خدمات حقوقی'),
        ('credit_scoring', 'اعتبارسنجی و رتبه‌بندی'),
        ('accounting', 'حسابداری و مالی'),
        ('valuation', 'ارزیابی دارایی'),
        ('other', 'سایر'),
    )

    vendor = models.ForeignKey(Vendor, related_name='services', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='عنوان')
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, verbose_name='توضیحات')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name='دسته‌بندی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    price_display = models.CharField(max_length=100, blank=True, verbose_name='نمایش قیمت')
    duration_display = models.CharField(max_length=100, blank=True, verbose_name='زمان تحویل')
    tags = models.JSONField(default=list, blank=True, verbose_name='برچسب‌ها')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'سرویس وندور'
        verbose_name_plural = 'سرویس‌های وندور'
        ordering = ['order', 'title']

    def __str__(self):
        return f'{self.vendor.name} — {self.title}'


class VendorApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'در انتظار بررسی'),
        ('under_review', 'در حال بررسی'),
        ('awaiting_info', 'نیاز به اطلاعات بیشتر'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
        ('cancelled', 'لغو شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='vendor_applications',
        on_delete=models.CASCADE,
    )
    vendor_service = models.ForeignKey(
        VendorService,
        related_name='applications',
        on_delete=models.CASCADE,
    )
    financing_request = models.ForeignKey(
        FinancingRequest,
        related_name='vendor_applications',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    user_notes = models.TextField(blank=True, verbose_name='توضیحات متقاضی')
    vendor_notes = models.TextField(blank=True, verbose_name='یادداشت وندور')
    result_data = models.JSONField(default=dict, blank=True, verbose_name='خروجی')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'درخواست وندور'
        verbose_name_plural = 'درخواست‌های وندور'
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.user} → {self.vendor_service}'


def decimal_from_payload(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(str(value).replace(',', ''))
    except (InvalidOperation, TypeError):
        raise ValidationError('عدد وارد شده معتبر نیست.')
