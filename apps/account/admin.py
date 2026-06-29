from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UAdmin
from django.core.exceptions import PermissionDenied
from .models import User, EducationalField, EducationalLevel, AccessLevel, Role, GrantRequest, GrantTransaction, \
    OTPserver, Notification, GrantRecord, Department, LabsnetCredit
# from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
import re
import jdatetime

from ..core.functions import safe_jalali_to_gregorian

from rest_framework.authtoken.models import Token, TokenProxy


class TokenAdmin(admin.ModelAdmin):
    search_fields = ['key', 'user__username', 'user__email', 'user__first_name', 'user__last_name']
    list_display = ['key', 'user', 'created']

admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, TokenAdmin)

@admin.action(description='Set role role_key=customer for users without any role')
def set_default_role(modeladmin, request, queryset):
    """
    Admin action to assign role with role_key=customer to users who have no role.
    """
    default_role = Role.objects.filter(role_key='customer').first()
    if not default_role:
        modeladmin.message_user(request, "Role with role_key=customer does not exist.", level='error')
        return

    updated_users = 0
    for user in queryset:
        if user.role.count() == 0:
            user.role.add(default_role)
            updated_users += 1

    modeladmin.message_user(request, f"{updated_users} users updated with role role_key=customer.")

@admin.action(description='Set Labsnet')
def set_labsnet(modeladmin, request, queryset):
    for user in queryset:

        if not user.national_id:
            raise PermissionDenied("User does not have a valid national ID.")

        # try:
        labsnet_result = user.labsnet_list()

        user.sync_labsnet_credits(labsnet_result)
        #
        #     modeladmin.message_user(request, f"action {obj}")
        # except Exception as e:
        #     modeladmin.message_user(request, f"{credit}  Error: {e}")
        #     print(f"Error processing credit: {credit}. Error: {e}")

        # return Response({"labsnet_result": labsnet_result})
        modeladmin.message_user(request, f"{labsnet_result}")
    modeladmin.message_user(request, f"Nothing")

class UserAdmin(UAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password", "OTP")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "user_type",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("All fields"), {"fields": ("account_type", "national_id", "role", "access_level",
                                      "educational_field", "educational_level", "student_id", "address", "postal_code", "company_economic_number",
                                      "company_national_id", "company_telephone", "company_name", "linked_users", "balance", 'is_partner')})
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    list_display = ("username", "national_id", "email", "first_name", "last_name", "is_staff", "user_type", "account_type", "role_str")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "user_type", "account_type")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    actions = [set_default_role, set_labsnet]
    # readonly_fields = ('research_grant', 'labsnet_grant')
    model = User

    @admin.display(description='Role')
    def role_str(self, obj):
        return ", ".join([str(x) for x in obj.role.all()])

# class GroupAdmin(GroupAdmin):
#     model = Group

# admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
# admin.site.register(Group, GroupAdmin)


@admin.register(EducationalField)
class LabTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)


@admin.register(EducationalLevel)
class FormResponseAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)


def access_level_generator(modeladmin, request, queryset):
    keys = ['User', 'GrantTransaction', 'GrantRequest', 'Notification', 'GrantRecord',  # account
            'Form',  # form
            'Laboratory', 'Experiment', 'Device', 'Parameter', 'Request', 'FormResponse',  # lab
            'PromotionCode', 'Order', 'PaymentRecord', 'Transaction',  # order
            ]

    for key in keys:
        snake_key = re.sub(r'(?<!^)(?=[A-Z])', '', key).lower()
        AccessLevel.objects.get_or_create(name=f'Create All {key}', access_key=f'create_all_{snake_key}')
        for i in ['view', 'update', 'delete']:
            for j in ['all', 'owner']:
                AccessLevel.objects.get_or_create(name=f'{i.capitalize()} {j.capitalize()} {key}', access_key=f'{i}_{j}_{snake_key}')

    modeladmin.message_user(request, "Access levels have been successfully generated.", messages.SUCCESS)

access_level_generator.short_description = "Generate access levels from keys"


@admin.register(AccessLevel)
class AccessLevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'access_key')
    actions = [access_level_generator]
    # ordering = ('order',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_key')
    # ordering = ('order',)


@admin.register(GrantTransaction)
class GrantTransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'amount', 'datetime', 'expiration_date')
    # ordering = ('order',)

@admin.register(GrantRecord)
class GrantRecordAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'amount', 'created_at', 'expiration_date')
    # ordering = ('order',)

@admin.register(GrantRequest)
class GrantRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'requested_amount', 'approved_amount', 'datetime', 'expiration_date')
    # ordering = ('order',)


@admin.register(OTPserver)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('base_url', 'token_expiration', 'token')
    # ordering = ('order',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']


@admin.register(LabsnetCredit)
class LabsnetCreditAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'remain', 'amount', 'end_date', 'labsnet_id', 'percent']
    search_fields = ['user__national_id', 'user__username', 'title', 'labsnet_id']