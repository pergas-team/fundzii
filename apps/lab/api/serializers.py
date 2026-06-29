import datetime
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import serializers
import ast
import json

from apps.account.api.serializers import UserSerializer, GrantRecordSerializer, GrantRequestSerializer
from apps.account.api.views import UserDetailAPIView
from apps.account.models import User, LabsnetCredit
from apps.appointment.api.serializers import AppointmentListSerializer, AppointmentSerializer
from apps.form.api.serializers import FormSerializer, FormSummerySerializer
from apps.lab.models import Laboratory, Experiment, Device, Parameter, Request, Department, LabType, FormResponse, \
    Status, Workflow, WorkflowStep, WorkflowStepButton, RequestResult, RequestCertificate, DiscountHistory, \
    ISOVisibility
from apps.order.models import PaymentRecord, Order


class LabsnetCreditSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabsnetCredit
        exclude = []


class UserSummerySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class LaboratorySummarySerializer(serializers.ModelSerializer):
    technical_manager_obj = UserSummerySerializer(read_only=True, source='technical_manager')

    class Meta:
        model = Laboratory
        exclude = ['device']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        exclude = []


class DeviceSerializer(serializers.ModelSerializer):
    lab_name = serializers.SerializerMethodField(read_only=True)

    def get_lab_name(self, obj):
        return obj.laboratory.name

    class Meta:
        model = Device
        exclude = []


class ParameterSerializer(serializers.ModelSerializer):
    exp_name = serializers.SerializerMethodField(read_only=True)

    def get_exp_name(self, obj):
        return obj.experiment.name

    class Meta:
        model = Parameter
        exclude = []


class ExperimentSerializer(serializers.ModelSerializer):
    device_obj = DeviceSerializer(read_only=True, source='device')
    lab_name = serializers.SerializerMethodField(read_only=True)
    form_obj = FormSummerySerializer(read_only=True, source='form')
    laboratory_obj = LaboratorySummarySerializer(read_only=True, source='laboratory')

    def get_lab_name(self, obj):
        return obj.get_lab_name()

    class Meta:
        model = Experiment
        exclude = []


class ExperimentDetailSerializer(serializers.ModelSerializer):
    device_obj = DeviceSerializer(read_only=True, source='device')
    form_obj = FormSerializer(read_only=True, source='form')
    laboratory_obj = LaboratorySummarySerializer(read_only=True, source='laboratory')

    class Meta:
        model = Experiment
        exclude = []


class LaboratorySerializer(serializers.ModelSerializer):
    technical_manager_obj = UserSummerySerializer(read_only=True, source='technical_manager')
    operator_obj = UserSummerySerializer(read_only=True, source='operator')
    operators_obj = UserSummerySerializer(read_only=True, many=True, source='operators')
    department_obj = DepartmentSerializer(read_only=True, source='department')
    device_objs = DeviceSerializer(read_only=True, many=True, source='devices')
    operators = serializers.CharField(write_only=True)
    is_visible_iso = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Laboratory
        exclude = ['device']

    def get_is_visible_iso(self, obj):
        return ISOVisibility.objects.get(pk=1).is_visible_iso

    def to_internal_value(self, data):
        internal_value = super(LaboratorySerializer, self).to_internal_value(data)

        operators_data = data.get('operators', '[]')
        try:
            operator_ids = json.loads(operators_data)
            operators = User.objects.filter(id__in=operator_ids)
            internal_value['operators'] = operators
        except (ValueError, TypeError):
            raise serializers.ValidationError({"operators": "Invalid operators data."})

        return internal_value


class LaboratoryDetailSerializer(serializers.ModelSerializer):
    experiments = ExperimentSerializer(read_only=True, many=True)
    technical_manager_obj = UserSerializer(read_only=True, source='technical_manager')
    operator_obj = UserSerializer(read_only=True, source='operator')
    operators_obj = UserSerializer(read_only=True, many=True, source='operators')
    department_obj = DepartmentSerializer(read_only=True, source='department')
    device_objs = DeviceSerializer(read_only=True, many=True, source='devices')
    operators = serializers.CharField(write_only=True)

    class Meta:
        model = Laboratory
        exclude = ['device']

    def to_internal_value(self, data):
        internal_value = super(LaboratoryDetailSerializer, self).to_internal_value(data)

        # Parse the JSON string for operators and convert it to a list of User instances
        operators_data = data.get('operators', '[]')
        try:
            operator_ids = json.loads(operators_data)
            operators = User.objects.filter(id__in=operator_ids)
            internal_value['operators'] = operators
        except (ValueError, TypeError):
            raise serializers.ValidationError({"operators": "Invalid operators data."})

        return internal_value


class RequestExperimentSerializer(serializers.ModelSerializer):
    laboratory_obj = LaboratorySerializer(read_only=True, source='laboratory')

    class Meta:
        model = Experiment
        exclude = []


class RequestListFormResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = FormResponse
        exclude = ['response', 'response_json']


class RequestDetailFormResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormResponse
        exclude = ['response']


class RequestListMainFormResponseSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = FormResponse
        exclude = ['response', 'response_json']

    def get_children(self, obj):
        return RequestListMainFormResponseSerializer(
            FormResponse.objects.filter(parent=obj), many=True
        ).data


class RequestDetailMainFormResponseSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = FormResponse
        exclude = ['response']

    def get_children(self, obj):
        return RequestDetailMainFormResponseSerializer(
            FormResponse.objects.filter(parent=obj), many=True
        ).data


class WorkflowStepButtonSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowStepButton
        exclude = []

class WorkflowStepSerializer(serializers.ModelSerializer):
    request_count = serializers.SerializerMethodField(read_only=True)
    buttons = WorkflowStepButtonSerializer(many=True, read_only=True, source='button')

    def get_request_count(self, obj):
        step_status = obj.step_status.filter(accept=False, reject=False)
        return step_status.count()

    class Meta:
        model = WorkflowStep
        exclude = []


class WorkflowSerializer(serializers.ModelSerializer):
    # steps_objs = WorkflowStepSerializer(read_only=True, source='steps', many=True)
    steps_objs = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        exclude = []

    def get_steps_objs(self, obj):
        ordered_steps = obj.get_ordered_steps()
        return WorkflowStepSerializer(ordered_steps, many=True).data


class StatusSerializer(serializers.ModelSerializer):
    step_obj = WorkflowStepSerializer(read_only=True, source='step')
    action_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Status
        exclude = []

    def get_action_by_name(self, obj):
        try:
            return f"{obj.action_by.first_name} {obj.action_by.last_name}"
        except:
            return ""

class RequestButtonActionSerializer(serializers.ModelSerializer):
    action = serializers.CharField(write_only=True)
    description = serializers.CharField(max_length=100, write_only=True, required=False)
    value = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Request
        fields = ['description', 'action', 'value']

    def update(self, instance, validated_data):
        action_by = self.context['request'].user
        description = validated_data.pop('description', None)
        action = validated_data.pop('action', None)
        value = validated_data.pop('value', None)

        instance.step_button_action(action, description, action_by, value)

        return RequestDetailSerializer(instance)


class RequestChangeStatusSerializer(serializers.ModelSerializer):
    action = serializers.ChoiceField(choices=['next', 'previous', 'reject'], write_only=True)
    description = serializers.CharField(max_length=100, write_only=True)
    # action_by = UserSerializer(write_only=True)

    class Meta:
        model = Request
        # fields = ['description', 'action', 'action_by']
        fields = ['description', 'action']

    def update(self, instance, validated_data):
        # validated_data['action_by'] = self.context['request'].user
        # validated_data['action_by'] = User.objects.get(id=1)
        # action_by = User.objects.get(id=1)
        action_by = self.context['request'].user
        description = validated_data.pop('description', None)
        action = validated_data.pop('action', None)
        # obj = super().update(instance, validated_data)

        instance.change_status(action, description, action_by)
        instance.save()
        # obj.change_status(action)
        # obj.save()
        return RequestDetailSerializer(instance)


class RequestDetailResultSerializer(serializers.ModelSerializer):
    result_by_obj = UserSummerySerializer(read_only=True, source='result_by')

    class Meta:
        model = RequestResult
        exclude = []


class ChildRequestListSerializer(serializers.ModelSerializer):
    result_objs = RequestDetailResultSerializer(read_only=True, source='request_results', many=True)
    owner_obj = UserSerializer(read_only=True, source='owner')
    experiment_obj = RequestExperimentSerializer(read_only=True, source='experiment')
    parameter_obj = ParameterSerializer(many=True, read_only=True, source='parameter')

    status_objs = StatusSerializer(read_only=True, source='request_status', many=True)
    # latest_status_obj = serializers.SerializerMethodField(source='get_get_request_status_obj') #
    latest_status_obj = StatusSerializer(read_only=True, source='lastest_status')

    # forms = RequestListFormResponseSerializer(many=True, read_only=True, source='formresponse')
    forms = serializers.SerializerMethodField()
    appointments_obj = AppointmentSerializer(source='appointments', many=True, read_only=True)

    # def latest_status_obj_(self, obj):
    #     lastest_status = obj.lastest_status()
    #     return StatusSerializer(instance=lastest_status)
    #     # return obj.lastest_status()

    class Meta:
        model = Request
        exclude = []

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    def get_forms(self, obj):
        return RequestListMainFormResponseSerializer(
            FormResponse.objects.filter(request=obj, is_main=True), many=True
        ).data


class OrderPaymentRecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentRecord
        fields = ['id', 'settlement_type', 'is_lock', 'amount', 'transaction_code', 'tref', 'successful', 'payment_link', 'payment_type', 'created_at']


class RequestOrderDetailSerializer(serializers.ModelSerializer):
    payment_record = OrderPaymentRecordSerializer(many=True, source='order_payment_records', read_only=True, required=False)
    remaining_amount = serializers.SerializerMethodField(read_only=True, method_name="remaining_amount_")

    prepayment_raw = serializers.SerializerMethodField()
    labsnet_discount_prepayment = serializers.SerializerMethodField()
    grant_discount_prepayment = serializers.SerializerMethodField()
    prepayment_final = serializers.SerializerMethodField()

    class Meta:
        model = Order
        exclude = ['order_key']

    def remaining_amount_(self, obj):
        return obj.remaining_amount()

    def get_prepayment_raw(self, obj):
        return int(obj.request.total_prepayment_amount or 0)

    def get_labsnet_discount_prepayment(self, obj):
        today = datetime.date.today()
        request = obj.request
        base_amount = Decimal(request.total_prepayment_amount or 0)

        def apply_credit(credit):
            if not credit or credit.end_date < today:
                return Decimal(0)
            try:
                remain = Decimal(credit.remain.replace(',', ''))
                percent = Decimal(credit.percent) / Decimal(100)
                return min(base_amount * percent, remain, base_amount)
            except:
                return Decimal(0)

        if request.parent_request:
            ln1, ln2 = request.parent_request.labsnet1, request.parent_request.labsnet2
        else:
            ln1, ln2 = request.labsnet1, request.labsnet2

        if ln1 and ln2 and ln1 == ln2:
            ln2 = None

        credits = [ln for ln in [ln1, ln2] if ln and ln.end_date >= today]
        credits = sorted(credits, key=lambda l: (-Decimal(l.percent), -Decimal(l.remain.replace(',', ''))))

        used = Decimal(0)
        for c in credits:
            d = apply_credit(c)
            used += d
            base_amount -= d
        return int(used)

    def get_grant_discount_prepayment(self, obj):
        from decimal import Decimal
        request = obj.request
        base_amount = Decimal(request.total_prepayment_amount or 0)
        labsnet_used = Decimal(self.get_labsnet_discount_prepayment(obj))
        remaining = base_amount - labsnet_used

        grant_discount = Decimal(0)
        for grant in [request.grant_request1, request.grant_request2]:
            if grant and remaining > 0:
                used = min(grant.remaining_amount, remaining)
                grant_discount += used
                remaining -= used
        return int(grant_discount)

    def get_prepayment_final(self, obj):
        raw = Decimal(self.get_prepayment_raw(obj))
        labsnet = Decimal(self.get_labsnet_discount_prepayment(obj))
        grant = Decimal(self.get_grant_discount_prepayment(obj))
        return int(max(raw - labsnet - grant, 0))


class RequestListSerializer(serializers.ModelSerializer):
    result_objs = RequestDetailResultSerializer(read_only=True, source='request_results', many=True)
    owner_obj = UserSerializer(read_only=True, source='owner')
    experiment_obj = RequestExperimentSerializer(read_only=True, source='experiment')
    parameter_obj = ParameterSerializer(many=True, read_only=True, source='parameter')
    child_requests = ChildRequestListSerializer(many=True, read_only=True)

    status_objs = StatusSerializer(read_only=True, source='request_status',many=True)
    # latest_status_obj = serializers.SerializerMethodField(source='get_get_request_status_obj') #
    latest_status_obj = StatusSerializer(read_only=True, source='lastest_status')

    # forms = RequestListFormResponseSerializer(many=True, read_only=True, source='formresponse')
    forms = serializers.SerializerMethodField()
    order_obj = RequestOrderDetailSerializer(read_only=True, many=True, source='orders')
    grant_request1_obj = GrantRequestSerializer(source='grant_request1', read_only=True, required=False)
    grant_request2_obj = GrantRequestSerializer(source='grant_request2', read_only=True, required=False)
    labsnet1_obj = LabsnetCreditSerializer(source='labsnet1', read_only=True, required=False)
    labsnet2_obj = LabsnetCreditSerializer(source='labsnet2', read_only=True, required=False)

    appointments_obj = AppointmentSerializer(source='appointments', many=True, read_only=True)


    # def latest_status_obj_(self, obj):
    #     lastest_status = obj.lastest_status()
    #     return StatusSerializer(instance=lastest_status)
    #     # return obj.lastest_status()

    class Meta:
        model = Request
        exclude = []

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

    def get_forms(self, obj):
        return RequestListMainFormResponseSerializer(
            FormResponse.objects.filter(request=obj, is_main=True), many=True
        ).data


class DiscountHistorySerializer(serializers.ModelSerializer):
    action_by_obj = UserSummerySerializer(source='action_by')

    class Meta:
        model = DiscountHistory
        exclude = []

class ChildRequestDetailSerializer(serializers.ModelSerializer):
    result_objs = RequestDetailResultSerializer(read_only=True, source='request_results', many=True)
    owner_obj = UserSerializer(read_only=True, source='owner')
    experiment_obj = RequestExperimentSerializer(read_only=True, source='experiment')
    parameter_obj = ParameterSerializer(many=True, read_only=True, source='parameter')

    status_objs = StatusSerializer(read_only=True, source='request_status', many=True)

    # forms = RequestDetailFormResponseSerializer(many=True, read_only=True, source='formresponse')
    forms = serializers.SerializerMethodField()
    latest_status_obj = StatusSerializer(read_only=True, source='lastest_status')
    payment_record_objs = OrderPaymentRecordSerializer(many=True, source='get_latest_order_payment_records')
    discount_history_objs = DiscountHistorySerializer(many=True, source='request_discounts')
    appointments_obj = AppointmentSerializer(source='appointments', many=True, read_only=True)

    class Meta:
        model = Request
        exclude = []

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        # if 'parameter' in validated_data:
        instance.save()
        if not instance.has_parent_request:
            instance.update_parent_status()
        instance.set_price()
        return instance

    def get_forms(self, obj):
        return RequestDetailMainFormResponseSerializer(
            FormResponse.objects.filter(request=obj, is_main=True), many=True
        ).data

class RequestDetailSerializer(serializers.ModelSerializer):
    result_objs = RequestDetailResultSerializer(read_only=True, source='request_results', many=True)
    owner_obj = UserSerializer(read_only=True, source='owner')
    experiment_obj = RequestExperimentSerializer(read_only=True, source='experiment')
    parameter_obj = ParameterSerializer(many=True, read_only=True, source='parameter')
    child_requests = ChildRequestDetailSerializer(many=True, read_only=True)

    status_objs = StatusSerializer(read_only=True, source='request_status', many=True)

    # forms = RequestDetailFormResponseSerializer(many=True, read_only=True, source='formresponse')
    forms = serializers.SerializerMethodField()
    latest_status_obj = StatusSerializer(read_only=True, source='lastest_status')
    payment_record_objs = OrderPaymentRecordSerializer(read_only=True, many=True, source='get_latest_order_payment_records')
    # order_objs = RequestOrderDetailSerializer(read_only=True, many=True, source='get_latest_order')
    order_obj = RequestOrderDetailSerializer(read_only=True, many=True, source='orders')
    discount_history_objs = DiscountHistorySerializer(read_only=True, many=True, source='request_discounts')
    grant_request1_obj = GrantRequestSerializer(source='grant_request1', read_only=True, required=False)
    grant_request2_obj = GrantRequestSerializer(source='grant_request2', read_only=True, required=False)
    labsnet1_obj = LabsnetCreditSerializer(source='labsnet1', read_only=True, required=False)
    labsnet2_obj = LabsnetCreditSerializer(source='labsnet2', read_only=True, required=False)

    appointments_obj = AppointmentSerializer(source='appointments', many=True, read_only=True)

    class Meta:
        model = Request
        exclude = []

    def update(self, instance, validated_data):
        if instance.has_parent_request:
            parent_instance = instance.parent_request
        else:
            parent_instance = None
        super().update(instance, validated_data)
        # if 'parameter' in validated_data:
        instance.save()
        if not instance.has_parent_request:
            instance.update_parent_status()
        instance.set_price()
        if parent_instance and not instance.has_parent_request:
            parent_instance.set_price()
        return instance

    def get_forms(self, obj):
        return RequestDetailMainFormResponseSerializer(
            FormResponse.objects.filter(request=obj, is_main=True), many=True
        ).data


class RequestUpdateSerializer(serializers.ModelSerializer):
    labsnet1_id = serializers.CharField(write_only=True, required=False)
    labsnet2_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Request
        fields = ["labsnet1_id", "labsnet2_id"]

    def update(self, instance, validated_data):
        labsnet1_id = validated_data.get("labsnet1_id")
        labsnet2_id = validated_data.get("labsnet2_id")

        if labsnet1_id:
            labsnet1 = get_object_or_404(LabsnetCredit, labsnet_id=labsnet1_id)
            instance.labsnet1 = labsnet1

        if labsnet2_id:
            labsnet2 = get_object_or_404(LabsnetCredit, labsnet_id=labsnet2_id)
            instance.labsnet2 = labsnet2

        instance.save()
        instance.apply_labsnet_credits()
        return instance


class CertificateSerializer(serializers.ModelSerializer):

    class Meta:
        model = RequestCertificate
        exclude = []


class RequestCertificateSerializer(serializers.ModelSerializer):
    owner_obj = UserSerializer(read_only=True, source='owner')
    experiment_obj = RequestExperimentSerializer(read_only=True, source='experiment')
    parameter_obj = ParameterSerializer(many=True, read_only=True, source='parameter')
    certificate_obj = CertificateSerializer(read_only=True, source='certificate')
    dates = serializers.SerializerMethodField(read_only=True, method_name='cert_dates')

    def cert_dates(self, obj):
        try:
            sample_date = obj.request_status.filter(step__name='در ‌انتظار نمونه').first().updated_at
            result_date = obj.request_status.filter(step__name='تکمیل شده').first().updated_at
        except:
            return {
               'sample_date': None,
               'result_date': None,
            }
        return {
            'sample_date': sample_date,
            'result_date': result_date,
        }

    class Meta:
        model = Request
        exclude = []



class LabTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabType
        exclude = []


class FormResponseRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = Request
        exclude = []


class FormResponseSerializer(serializers.ModelSerializer):
    request_obj = FormResponseRequestSerializer(read_only=True, source='request')

    class Meta:
        model = FormResponse
        exclude = []

    # def create(self, validated_data):
    #     instance = super().create(validated_data)
    #     instance.request.set_price()
    #     return instance

    #
    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     ret['response_'] = ast.literal_eval(ret['response'])
    #     return ret

class RequestResultSerializer(serializers.ModelSerializer):
    # request_obj = FormResponseRequestSerializer(read_only=True, source='request')
    result_by_obj = UserSummerySerializer(read_only=True, source='result_by')

    class Meta:
        model = RequestResult
        exclude = []

    def create(self, validated_data):
        validated_data['result_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['result_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class UpdateLaboratoryISOSerializer(serializers.Serializer):
    is_visible_iso = serializers.BooleanField(required=True)


class ISOVisibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ISOVisibility
        fields = ['is_visible_iso']