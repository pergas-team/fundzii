from django.contrib import admin

from apps.fundzi.models import (
    DynamicForm,
    FinancialPartner,
    FinancialService,
    FinancingRequest,
    FormField,
    InternalNote,
    RequestAttachment,
    RequestFieldValue,
    RequestHistory,
    ServiceContent,
    Workflow,
    WorkflowStep,
)


class ServiceContentInline(admin.TabularInline):
    model = ServiceContent
    extra = 0


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    fields = ('label', 'key', 'field_type', 'required', 'options', 'validation_config', 'order', 'is_active')


class WorkflowStepInline(admin.TabularInline):
    model = WorkflowStep
    extra = 0
    fields = ('title', 'key', 'order', 'is_initial', 'is_terminal', 'is_active')


@admin.register(FinancialService)
class FinancialServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'service_type', 'is_active', 'order', 'updated_at')
    list_filter = ('service_type', 'is_active', 'created_at')
    search_fields = ('title', 'slug', 'short_description', 'full_description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ServiceContentInline]


@admin.register(ServiceContent)
class ServiceContentAdmin(admin.ModelAdmin):
    list_display = ('service', 'content_type', 'title', 'order', 'is_active')
    list_filter = ('content_type', 'is_active', 'service')
    search_fields = ('service__title', 'title', 'body')


@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):
    list_display = ('title', 'service', 'is_active', 'updated_at')
    list_filter = ('is_active', 'service')
    search_fields = ('title', 'service__title', 'service__slug')
    inlines = [FormFieldInline]


@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ('label', 'key', 'form', 'field_type', 'required', 'order', 'is_active')
    list_filter = ('field_type', 'required', 'is_active', 'form__service')
    search_fields = ('label', 'key', 'form__title', 'form__service__title')


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'is_active', 'updated_at')
    list_filter = ('is_active', 'service')
    search_fields = ('name', 'service__title', 'service__slug')
    inlines = [WorkflowStepInline]


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ('title', 'key', 'workflow', 'order', 'is_initial', 'is_terminal', 'is_active')
    list_filter = ('workflow__service', 'is_initial', 'is_terminal', 'is_active')
    search_fields = ('title', 'key', 'workflow__name')


class RequestFieldValueInline(admin.TabularInline):
    model = RequestFieldValue
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class RequestAttachmentInline(admin.TabularInline):
    model = RequestAttachment
    extra = 0
    readonly_fields = ('created_at',)


class RequestHistoryInline(admin.TabularInline):
    model = RequestHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'note', 'created_at')
    can_delete = False


class InternalNoteInline(admin.TabularInline):
    model = InternalNote
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(FinancingRequest)
class FinancingRequestAdmin(admin.ModelAdmin):
    list_display = (
        'tracking_code',
        'service',
        'user',
        'current_status',
        'admin_assignee',
        'submitted_at',
        'is_archived',
    )
    list_filter = ('service', 'current_status', 'admin_assignee', 'is_archived', 'submitted_at')
    search_fields = (
        'tracking_code',
        'service__title',
        'service__slug',
        'user__username',
        'user__first_name',
        'user__last_name',
    )
    readonly_fields = ('tracking_code', 'submitted_at', 'updated_at')
    inlines = [RequestFieldValueInline, RequestAttachmentInline, RequestHistoryInline, InternalNoteInline]

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous = FinancingRequest.objects.filter(pk=obj.pk).first()
            previous_status = previous.current_status if previous else None
        super().save_model(request, obj, form, change)
        obj.refresh_from_db()
        if change and previous_status != obj.current_status:
            RequestHistory.objects.create(
                request=obj,
                from_status=previous_status,
                to_status=obj.current_status,
                changed_by=request.user,
                note='تغییر وضعیت از پنل مدیریت',
            )


@admin.register(RequestFieldValue)
class RequestFieldValueAdmin(admin.ModelAdmin):
    list_display = ('request', 'field', 'value_text', 'value_number', 'updated_at')
    list_filter = ('field__form__service', 'field__field_type')
    search_fields = ('request__tracking_code', 'field__key', 'field__label', 'value_text')


@admin.register(RequestAttachment)
class RequestAttachmentAdmin(admin.ModelAdmin):
    list_display = ('request', 'document_type', 'title', 'uploaded_by', 'created_at')
    list_filter = ('document_type', 'created_at')
    search_fields = ('request__tracking_code', 'document_type', 'title')


@admin.register(RequestHistory)
class RequestHistoryAdmin(admin.ModelAdmin):
    list_display = ('request', 'from_status', 'to_status', 'changed_by', 'created_at')
    list_filter = ('to_status', 'created_at')
    search_fields = ('request__tracking_code', 'from_status', 'to_status', 'note')


@admin.register(InternalNote)
class InternalNoteAdmin(admin.ModelAdmin):
    list_display = ('request', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('request__tracking_code', 'body')


@admin.register(FinancialPartner)
class FinancialPartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'min_amount', 'max_amount', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'description')
