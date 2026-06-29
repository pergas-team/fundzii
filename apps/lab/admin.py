from django.contrib import admin
from .models import Laboratory, Experiment, Device, Parameter, Request, Department, LabType, FormResponse, WorkflowStep, \
    Status, Workflow, WorkflowStepButton, RequestResult, ISOVisibility
from apps.lab.tasks import check_and_process_pending_appointment


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_en', 'department', 'lab_type', 'phone_number')
    search_fields = ('name', 'name_en', 'address', 'phone_number')
    list_filter = ('department', 'lab_type', 'device')


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ('laboratory', 'device', 'name', 'name_en')
    search_fields = ('name', 'name_en')
    list_filter = ('laboratory', 'device')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'manufacturer', 'purchase_date', 'status')
    search_fields = ('name', 'model', 'manufacturer')
    list_filter = ('status',)


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'experiment')
    search_fields = ('name', 'experiment')
    list_filter = ('experiment',)


@admin.action(description="pending_appointment")
def pending_appointment(modeladmin, request, queryset):
    for req in queryset:
        check_and_process_pending_appointment.apply_async((req.id,), countdown=10)


@admin.action(description="set_labsnet_create")
def set_labsnet_create(modeladmin, request, queryset):
    for req in queryset:
        if req.lastest_status().step.name == 'در ‌انتظار نمونه':
            if not req.parent_request and not req.labsnet:
                req.labsnet_create()
                req.save()
        if req.lastest_status().step.name == 'در انتظار پرداخت' and (req.labsnet):
            if not req.parent_request:
                req.labsnet_create_grant()
                req.save()


@admin.action(description="set_price")
def set_price(modeladmin, request, queryset):
    for req in queryset:
        req.set_price()


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_number', 'is_completed', 'price', 'labsnet', 'owner', 'is_cancelled', 'experiment', 'created_at', 'updated_at')
    search_fields = ('id', 'request_number')
    list_filter = ('is_completed', 'labsnet', 'created_at', 'updated_at', 'experiment__laboratory', 'request_status__step')
    readonly_fields = ('owner', 'experiment', 'parameter', 'parent_request')
    actions = [pending_appointment, set_labsnet_create, set_price]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(LabType)
class LabTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(FormResponse)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ('request', 'response')
    search_fields = ('request', 'response')


@admin.register(Workflow)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')


@admin.register(WorkflowStep)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'name', 'next_step')
    # search_fields = ('name', 'description')


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('request', 'step', 'complete')
    # search_fields = ('name', 'description')


@admin.register(WorkflowStepButton)
class WorkflowStepButtonAdmin(admin.ModelAdmin):
    list_display = ('title', 'action_slug', 'color')
    # search_fields = ('name', 'description')


@admin.register(RequestResult)
class RequestResultAdmin(admin.ModelAdmin):
    list_display = ('request', 'created_at', 'description')


@admin.register(ISOVisibility)
class ISOVisibilityAdmin(admin.ModelAdmin):
    # pass
    list_display = ('id', 'is_visible_iso')
