from rest_framework import serializers

from apps.fundzi.models import (
    FinancialPartner,
    FinancialService,
    FinancingRequest,
    FormField,
    InternalNote,
    MatchingRule,
    MatchResult,
    Notification,
    PartnerOffer,
    RequestAttachment,
    RequestHistory,
    ServiceContent,
    Vendor,
    VendorApplication,
    VendorService,
    WorkflowStep,
)


# ── Auth ──────────────────────────────────────────────────────────────────────

class SendOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate(self, data):
        # Accept legacy 'username' key too
        return data


class VerifyOtpSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(required=False, allow_blank=True, default='')


class PasswordLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


# ── Users ─────────────────────────────────────────────────────────────────────

class UserSerializer(serializers.Serializer):
    """Read-only user representation shared across views."""
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone_number = serializers.CharField(source='username')
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()


class UserAdminSerializer(UserSerializer):
    is_active = serializers.BooleanField()
    date_joined = serializers.DateTimeField()
    groups = serializers.SerializerMethodField()
    requests_count = serializers.SerializerMethodField()

    def get_groups(self, obj):
        return list(obj.groups.values_list('name', flat=True))

    def get_requests_count(self, obj):
        return getattr(obj, 'requests_count', obj.fundzi_requests.count())


# ── Services ──────────────────────────────────────────────────────────────────

class ServiceContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceContent
        fields = ['id', 'content_type', 'title', 'body', 'order', 'is_active', 'metadata']


class FormFieldSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='field_type', read_only=True)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FormField
        fields = [
            'id', 'label', 'key', 'type', 'field_type',
            'required', 'placeholder', 'help_text',
            'options', 'validation_config', 'order', 'is_active',
            'parent', 'group_option',
        ]
        extra_kwargs = {'field_type': {'write_only': True}}


class ServiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialService
        fields = [
            'id', 'slug', 'title', 'short_description', 'full_description',
            'service_type', 'is_active', 'order', 'rules_config', 'metadata',
        ]


class ServiceDetailSerializer(ServiceListSerializer):
    contents = serializers.SerializerMethodField()

    class Meta(ServiceListSerializer.Meta):
        fields = ServiceListSerializer.Meta.fields + ['contents']

    def get_contents(self, obj):
        qs = obj.contents.filter(is_active=True)
        return ServiceContentSerializer(qs, many=True).data


class DynamicFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormField  # placeholder — we use to_representation directly
        fields = []

    def to_representation(self, form):
        return {
            'id': form.id,
            'title': form.title,
            'description': form.description,
            'is_active': form.is_active,
            'metadata': form.metadata,
            'fields': FormFieldSerializer(
                form.fields.filter(is_active=True).order_by('order', 'id'),
                many=True,
            ).data,
        }


class FormSchemaSerializer(serializers.Serializer):
    """Schema for the public /services/<slug>/form/ endpoint."""

    def to_representation(self, form):
        return {
            'id': form.id,
            'title': form.title,
            'description': form.description,
            'fields': FormFieldSerializer(
                form.fields.filter(is_active=True).order_by('order', 'id'),
                many=True,
            ).data,
        }


class WorkflowStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStep
        fields = ['id', 'key', 'title', 'description', 'order', 'is_initial', 'is_terminal', 'is_active', 'metadata']


class WorkflowSerializer(serializers.Serializer):
    def to_representation(self, workflow):
        return {
            'id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'is_active': workflow.is_active,
            'steps': WorkflowStepSerializer(workflow.steps.all(), many=True).data,
        }


class AdminServiceSerializer(serializers.Serializer):
    """Full service representation for admin views."""

    def to_representation(self, service):
        from apps.fundzi.api.serializers import (
            DynamicFormSerializer, ServiceContentSerializer, WorkflowSerializer,
        )
        data = ServiceListSerializer(service).data
        data['contents'] = ServiceContentSerializer(service.contents.all(), many=True).data
        form = getattr(service, 'form', None)
        data['form'] = DynamicFormSerializer().to_representation(form) if form else None
        workflow = getattr(service, 'workflow', None)
        data['workflow'] = WorkflowSerializer().to_representation(workflow) if workflow else None
        return data


# ── Requests ──────────────────────────────────────────────────────────────────

class RequestFieldValueSerializer(serializers.Serializer):
    def to_representation(self, fv):
        return {
            'field': fv.field.key,
            'label': fv.field.label,
            'type': fv.field.field_type,
            'value': fv.value,
            'file': fv.file.url if fv.file else None,
        }


class RequestHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.SerializerMethodField()

    class Meta:
        model = RequestHistory
        fields = ['id', 'from_status', 'to_status', 'changed_by', 'note', 'created_at']

    def get_changed_by(self, obj):
        return obj.changed_by.get_username() if obj.changed_by else None


class WorkflowStepMinimalSerializer(serializers.Serializer):
    def to_representation(self, step):
        if step is None:
            return {'id': None, 'key': None, 'title': None}
        return {'id': step.id, 'key': step.key, 'title': step.title}


class FinancingRequestSerializer(serializers.ModelSerializer):
    service = ServiceListSerializer(read_only=True)
    current_workflow_step = WorkflowStepMinimalSerializer(read_only=True)
    user = serializers.SerializerMethodField()
    admin_assignee = serializers.SerializerMethodField()

    class Meta:
        model = FinancingRequest
        fields = [
            'id', 'tracking_code', 'service', 'current_status',
            'current_workflow_step', 'submitted_at', 'updated_at',
            'is_archived', 'user', 'admin_assignee',
        ]

    def get_user(self, obj):
        return _user_payload(obj.user)

    def get_admin_assignee(self, obj):
        return _user_payload(obj.admin_assignee) if obj.admin_assignee else None


class FinancingRequestDetailSerializer(FinancingRequestSerializer):
    field_values = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()

    class Meta(FinancingRequestSerializer.Meta):
        fields = FinancingRequestSerializer.Meta.fields + ['field_values', 'history']

    def get_field_values(self, obj):
        return RequestFieldValueSerializer(
            obj.field_values.select_related('field'), many=True
        ).data

    def get_history(self, obj):
        return RequestHistorySerializer(
            obj.history.select_related('changed_by'), many=True
        ).data


class AdminRequestDetailSerializer(FinancingRequestDetailSerializer):
    attachments = serializers.SerializerMethodField()
    internal_notes = serializers.SerializerMethodField()
    workflow_steps = serializers.SerializerMethodField()

    class Meta(FinancingRequestDetailSerializer.Meta):
        fields = FinancingRequestDetailSerializer.Meta.fields + [
            'attachments', 'internal_notes', 'workflow_steps'
        ]

    def get_attachments(self, obj):
        return [
            {
                'id': a.id,
                'title': a.title,
                'document_type': a.document_type,
                'file': a.file.url if a.file else None,
                'created_at': a.created_at.isoformat(),
            }
            for a in obj.attachments.all()
        ]

    def get_internal_notes(self, obj):
        return [
            {
                'id': n.id,
                'body': n.body,
                'author': n.author.get_username() if n.author else None,
                'created_at': n.created_at.isoformat(),
            }
            for n in obj.internal_notes.select_related('author')
        ]

    def get_workflow_steps(self, obj):
        try:
            steps = obj.service.workflow.steps.filter(is_active=True)
            return [{'id': s.id, 'key': s.key, 'title': s.title, 'order': s.order} for s in steps]
        except Exception:
            return []


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'kind', 'channel', 'title', 'body', 'status', 'is_read', 'created_at', 'read_at']


# ── Partner Portal (3.1) ──────────────────────────────────────────────────────

class PartnerOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartnerOffer
        fields = ['id', 'amount', 'interest_rate', 'duration_months', 'conditions', 'expires_at', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('مبلغ پیشنهادی باید بزرگ‌تر از صفر باشد.')
        return value

    def validate_interest_rate(self, value):
        if value < 0:
            raise serializers.ValidationError('نرخ سود نمی‌تواند منفی باشد.')
        return value

    def validate_duration_months(self, value):
        if value <= 0:
            raise serializers.ValidationError('مدت باید عدد مثبت باشد.')
        return value


# ── Matching Engine (3.2) ──────────────────────────────────────────────────────

class MatchingRuleSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)

    class Meta:
        model = MatchingRule
        fields = ['id', 'partner', 'partner_name', 'priority', 'conditions', 'is_active']


class MatchingRuleWriteSerializer(serializers.ModelSerializer):
    partner_id = serializers.PrimaryKeyRelatedField(
        queryset=FinancialPartner.objects.filter(is_active=True),
        source='partner',
    )

    class Meta:
        model = MatchingRule
        fields = ['partner_id', 'priority', 'conditions', 'is_active']


class MatchResultSerializer(serializers.ModelSerializer):
    partner_name = serializers.CharField(source='partner.name', read_only=True)

    class Meta:
        model = MatchResult
        fields = ['partner_id', 'partner_name', 'score', 'status', 'matched_at', 'assigned_at']


# ── Partners (admin) ──────────────────────────────────────────────────────────

class FinancialPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialPartner
        fields = [
            'id', 'name', 'type', 'service_categories',
            'min_amount', 'max_amount', 'accepted_collateral_types',
            'is_active', 'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


# ── Vendor Ecosystem ──────────────────────────────────────────────────────────

class VendorServiceSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_type = serializers.CharField(source='vendor.vendor_type', read_only=True)

    class Meta:
        model = VendorService
        fields = [
            'id', 'slug', 'title', 'description', 'category',
            'vendor_name', 'vendor_type',
            'price_display', 'duration_display', 'tags',
            'is_active', 'order',
        ]


class VendorSerializer(serializers.ModelSerializer):
    services = VendorServiceSerializer(many=True, read_only=True)

    class Meta:
        model = Vendor
        fields = [
            'id', 'slug', 'name', 'description', 'vendor_type',
            'logo_url', 'website', 'is_active', 'order', 'services',
        ]


class VendorApplicationSerializer(serializers.ModelSerializer):
    vendor_service_title = serializers.CharField(source='vendor_service.title', read_only=True)
    vendor_name = serializers.CharField(source='vendor_service.vendor.name', read_only=True)

    class Meta:
        model = VendorApplication
        fields = [
            'id', 'vendor_service', 'vendor_service_title', 'vendor_name',
            'financing_request', 'status', 'user_notes', 'vendor_notes',
            'result_data', 'submitted_at', 'updated_at',
        ]
        read_only_fields = ['status', 'vendor_notes', 'result_data', 'submitted_at', 'updated_at']


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_payload(user):
    if not user or not user.is_authenticated:
        return None
    from apps.fundzi.api.views import user_role
    return {
        'id': user.id,
        'username': user.get_username(),
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.get_username(),
        'role': user_role(user),
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }
