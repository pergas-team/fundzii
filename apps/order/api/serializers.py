import datetime
from decimal import Decimal

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

# from apps.account.models import Profile
# from apps.account.api.serializers import ProfileSummeryTicketSerializer
# from applications.account.serializers import ProfileSerializer, ProfileSummerySerializer, ProfileSummeryTicketSerializer
from apps.account.api.serializers import UserProfileSerializer
from apps.lab.api.serializers import UserSummerySerializer, RequestDetailSerializer
from apps.order.models import Order, PromotionCode, Transaction, PaymentRecord, Ticket
# from apps.service.models import EventTicket, Service
from apps.order.sharifpayment import SharifPayment


class TransactionSummmerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        exclude = []


class PaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = ['amount', 'payer', 'order']

    def __init__(self, *args, **kwargs):
        self.related_order = None
        super().__init__(*args, **kwargs)

    def validate_amount(self, amount):
        if amount and amount < 1000:
            raise serializers.ValidationError("You chan't charge less than 1000 tomans.")
        if amount and amount > 9000000:
            raise serializers.ValidationError("You can't charge more than 9000000 tomans.")
        return amount

    def validate_order(self, order):
        if order:
            try:
                self.order = Order.objects.get(buyer_id=self.user.profile, id=order.id)
            except:
                raise serializers.ValidationError("Invalid order code!")

            if not self.order.order_status == 'pending':
                raise serializers.ValidationError("Order is either already completed, or it's canceled!")

        return order

    def validate(self, attrs):
        order = attrs.get('order', None)
        amount = attrs.get('amount', None)
        if (not (order is None or amount is None)) or (order is None and amount is None):
            raise serializers.ValidationError("You should enter one of these: Payment Amount or Order Code.")

        return attrs

    def create(self, validated_data):
        self.order = validated_data['order']
        validated_data['payer'] = self.user.profile
        # order_code = validated_data.pop('order_code', None)
        # if validated_data['order']:
        if self.order:
            # self.order = validated_data['order']
            # self.order = Order.objects.get(buyer=self.user.profile, order_code=order_code)
            # validated_data['order'] = self.order
            validated_data['amount'] = self.order.remaining_amount()
            validated_data['payment_type'] = 'order'
            self.order.updated_at = timezone.now()
            self.order.save()
        else:
            validated_data['payment_type'] = 'account'
        validated_data['payer'] = self.user.profile
        return super(PaymentRecordSerializer, self).create(validated_data)


class OrderPaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = ['id', 'amount', 'settlement_type', 'transaction_code', 'tref', 'successful', 'payer', 'order', 'payment_order_guid', 'payment_order_id', 'is_lock', 'payment_link']

    def validate_tref(self, value):
        if self.instance is None:
            if PaymentRecord.objects.filter(tref=value).exists():
                raise serializers.ValidationError({'کد تراکنش': "کد تراکنش تکراری است."})
        return value

#used
class OrderSerializer(serializers.ModelSerializer):
    use_balance = serializers.BooleanField(default=False, required=False)
    promo_code = serializers.CharField(required=False)

    transaction = TransactionSummmerySerializer(many=True, source='transactions', read_only=True, required=False)
    payment_record = OrderPaymentRecordSerializer(many=True, source='order_payment_records', read_only=True, required=False)

    prepayment_raw = serializers.SerializerMethodField()
    labsnet_discount_prepayment = serializers.SerializerMethodField()
    grant_discount_prepayment = serializers.SerializerMethodField()
    prepayment_final = serializers.SerializerMethodField()


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

    class Meta:
        model = Order
        exclude = ['order_key']

    def create(self, validated_data):
        promo_code = validated_data.pop('promo_code', None)
        order_type = validated_data.pop('order_type', None)
        if order_type == 'expert':
            role = self.context['request'].user.profile.role()
            if role == 'expert':
                validated_data['order_type'] = 'expert'
        if promo_code and validated_data['promotion_code'] is None:
            validated_data['promotion_code'] = get_object_or_404(PromotionCode, code=promo_code)

        use_balance = validated_data.pop('use_balance', False)
        order = super().create(validated_data)
        order.process(use_balance)
        return order

    def update(self, instance, validated_data):
        use_balance = validated_data.pop('use_balance', False)
        order = super().update(instance, validated_data)
        order.process(use_balance)
        return order


class OrderBoughtSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.SerializerMethodField(read_only=True, method_name="remaining_amount_")
    request_number = serializers.SerializerMethodField(read_only=True, method_name="request_number_")

    def request_number_(self, obj):
        return obj.request.request_number

    def remaining_amount_(self, obj):
        return obj.remaining_amount()

    class Meta:
        model = Order
        exclude = ['order_key']


class OrderDetailSerializer(serializers.ModelSerializer):
    payment_record = OrderPaymentRecordSerializer(many=True, source='order_payment_records', read_only=True, required=False)

    class Meta:
        model = Order
        exclude = ['order_key']


class OrderPaymentSerializer(serializers.ModelSerializer):
    payment_record = OrderPaymentRecordSerializer(many=True, source='order_payment_records', read_only=True, required=False)
    class Meta:
        model = Order
        fields = ['order_status', 'payment_record']

    def update(self, instance, validated_data):
        instance.process(pay=True)
        return instance


class OrderPrePaymentSerializer(serializers.ModelSerializer):
    payment_record = OrderPaymentRecordSerializer(many=True, source='order_payment_records', read_only=True, required=False)

    class Meta:
        model = Order
        fields = ['order_status', 'payment_record']

    def update(self, instance, validated_data):
        instance.set_prepayment()
        return instance


class OrderCancelSerializer(serializers.ModelSerializer):
    order_status = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = ['order_status']

    def update(self, instance, validated_data):
        instance.cancel()
        return instance


class PaymentSummarySerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentRecord
        fields = ['payer', 'payment_type', 'amount', 'successful']


class PaymentRecordListSerializer(serializers.ModelSerializer):
    order_obj = serializers.SerializerMethodField(read_only=True)
    payer_obj = UserSummerySerializer(read_only=True, source='payer')
    request_obj = RequestDetailSerializer(read_only=True, source='order.request')

    def get_order_obj(self, obj):
        order = obj.order
        return OrderDetailSerializer(order, context=self.context).data

    class Meta:
        model = PaymentRecord
        exclude = ['log_text']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['order_key']


class PromotionCodeSerializer(serializers.ModelSerializer):
    code = serializers.ReadOnlyField()

    class Meta:
        model = PromotionCode
        fields = ['code']


class PaymentRecordInvoiceSerializer(serializers.ModelSerializer):
    order_obj = serializers.SerializerMethodField(read_only=True)
    payer_obj = UserProfileSerializer(read_only=True, source='payer')
    request_obj = RequestDetailSerializer(read_only=True, source='order.request')

    def get_order_obj(self, obj):
        order = obj.order
        return OrderDetailSerializer(order, context=self.context).data

    class Meta:
        model = PaymentRecord
        exclude = ['log_text']



class AddPromotionCodeSerializer(serializers.ModelSerializer):
    used_count = serializers.ReadOnlyField()

    class Meta:
        model = PromotionCode
        exclude = []
        extra_kwargs = {'percent_off': {'required': True}}

    def validate_percent_off(self, percent_off):

        if percent_off > 100 or percent_off <= 0:
            raise serializers.ValidationError("You should enter a value between 1 to 100!")

        return percent_off

    def validate(self, attrs):
        service = attrs.get('service')
        percent_off = attrs.get('percent_off', 0)

        # self.supervisor = Supervisor.objects.filter(id=self.user.id).first()
        #
        # if self.supervisor:
        #     from applications.exams.models import Exam
        #
        #     if not service:
        #         raise serializers.ValidationError({'service': _("This field is required!")})
        #
        #     event = Exam.objects.filter(id=service.id).first()
        #     if not event or not event.has_agent:
        #         raise serializers.ValidationError({'service': _("Invalid Event Item!")})
        #
        #     if percent_off > event.agent_share:
        #         raise serializers.ValidationError(
        #             {'percent_off': _("Maximum value for the percentage is {0}!").format(event.agent_share)})

        return attrs

    def create(self, validated_data):
        # validated_data['supervisor'] = self.supervisor

        return super().create(validated_data)


class OrderIssueSerializer(serializers.ModelSerializer):
    service_code = serializers.CharField(required=True, write_only=True)
    amount = serializers.ReadOnlyField()
    order_type = serializers.ReadOnlyField()
    order_status = serializers.ReadOnlyField()
    service = serializers.SerializerMethodField()
    promo_code = serializers.CharField(required=False)
    promotion_code = PromotionCodeSerializer(read_only=True)
    use_balance = serializers.BooleanField(default=False, required=False)


    class Meta:
        model = Order
        exclude = ['virtual_order']
        extra_kwargs = {'service_ticket': {'required': False}, 'owners': {'required': False, 'allow_empty': True}}

    def __init__(self, *args, **kwargs):
        request = kwargs['context'].get('request')

        if 'data' in kwargs:
            if 'promo_code' in kwargs['data'] and not kwargs['data']['promo_code'].replace(' ', '').replace('\t', ''):
                kwargs['data'].pop('promo_code')

        self.service = None
        self.special_checks = True

        super().__init__(*args, **kwargs)


    def create(self, validated_data):
        validated_data['buyer'] = self.user
        validated_data['service'] = self.service
        validated_data['promotion_code'] = self.promotion_code
        validated_data.pop('service_code', None)
        validated_data.pop('promo_code', None)

        use_balance = validated_data.pop('use_balance', False)
        order = super().create(validated_data)
        order.process(use_balance, self.use_coins)

        return order

    def update(self, instance, validated_data):
        validated_data['promotion_code'] = self.promotion_code
        validated_data.pop('service_code', None)
        validated_data.pop('promo_code', None)

        use_balance = validated_data.pop('use_balance', False)

        order = super().update(instance, validated_data)
        order.process(use_balance, self.use_coins)

        return order

class CheckOrderSerializer(serializers.ModelSerializer):
    service_code = serializers.CharField(required=False, write_only=True)
    order_code = serializers.CharField(required=False, write_only=True)
    old_price = serializers.SerializerMethodField()
    amount = serializers.ReadOnlyField()
    # service = ServiceItemSerializer(read_only=True)
    promo_code = serializers.CharField(required=False)
    promotion_code = serializers.SerializerMethodField()
    vitrin_link = serializers.ReadOnlyField()

    class Meta:
        model = Order
        exclude = ['order_type', 'order_status', 'buyer', 'id', 'description',
                   'created_at', 'updated_at', 'virtual_order', 'order_key']
        extra_kwargs = {'service_ticket': {'required': False}, 'owners': {'required': False, 'allow_empty': True}}

    def __init__(self, *args, **kwargs):
        request = kwargs['context'].get('request')


        self.blank_promo = False

        if 'data' in kwargs:
            if 'promo_code' in kwargs['data'] and not kwargs['data']['promo_code'].replace(' ', '').replace('\t', ''):
                kwargs['data'].pop('promo_code')
                self.blank_promo = True

        self.service = None
        self.order = None

        super().__init__(*args, **kwargs)

    def validate_service_code(self, service_code):
        if not self.service:
            raise serializers.ValidationError("Invalid service code!")

        return service_code

    def validate_order_code(self, order_code):
        self.order = Order.objects.filter(order_code=order_code).first()

        if not self.order:
            raise serializers.ValidationError("Invalid order code!")

        self.check_pending_orders = True

        return order_code

    def validate(self, attrs):
        self.promotion_code = None
        self.event_group = None

        if not self.service and self.order:
            self.service = self.order.service

        if not attrs.get('owners'):
            attrs['owners'] = []
            if self.order:
                attrs['owners'] = self.order.owners.all()

        if not attrs.get('extensions'):
            attrs['extensions'] = []
            if self.order:
                attrs['extensions'] = self.order.extensions.all()

        if not attrs.get('service_ticket'):
            if self.order:
                attrs['service_ticket'] = self.order.service_ticket

            elif self.service:
                if self.service.tickets.count() == 1:
                    attrs['service_ticket'] = self.service.tickets.first()
            else:
                raise serializers.ValidationError({'service_ticket': "Field is required!"})

        # self.profile = get_profile_by_user(self.user)
        # self.profile = self.request.user.profile
        #
        # if not type(self.profile) == Manager:
        #     if not self.profile or not self.profile.verified:
        #         raise serializers.ValidationError(
        #             _("Your account needs to be verified in order to make orders!"))
        #
        #     if not self.profile or not (self.profile.verified_phone or self.profile.verified_email):
        #         raise serializers.ValidationError(
        #             _("You should verify your phone number or email before making any orders!"))

        if self.service:
            ticket = attrs.get('service_ticket', [])
            extensions = attrs.get('extensions', [])
            owners = attrs.get('owners', [])
            promo_code = attrs.get("promo_code", None)

            self.promotion_code = PromotionCode.objects.filter(code=promo_code, active=True).filter(
                Q(service__isnull=True) | Q(service=self.service)).first()

            if promo_code and not self.promotion_code:
                raise serializers.ValidationError("Invalid promotion code!")

            # validate_order_data(buyer=self.profile, service=self.service, owners=owners, ticket=ticket,
            #                     extensions=extensions, promotion_code=self.promotion_code, instance=self.order,
            #                     check_pending_orders=self.check_pending_orders)

            if self.blank_promo:
                raise serializers.ValidationError("Invalid promotion code!")

        return attrs

    def create(self, validated_data):
        validated_data['buyer'] = self.user
        validated_data['service'] = self.service

        # validated_data['promotion_code'] = self.promotion_code
        validated_data.pop('service_code', None)
        validated_data.pop('promo_code', None)

        extensions = validated_data.pop('extensions', [])
        owners = validated_data.pop('owners', [])

        order = Order(**validated_data)

        self.old_price = Order.get_amount(ticket=order.service_ticket, extensions=extensions, owners=owners)

        order.amount = Order.get_amount(ticket=order.service_ticket, extensions=extensions, owners=owners,
                                        promotion_code=self.promotion_code)

        return order

    def get_old_price(self, obj):
        return self.old_price

    def get_promotion_code(self, obj):
        return PromotionCodeSerializer(self.promotion_code, context=self.context, read_only=True).data

    @property
    def data(self):
        data = super().data

        data['order_code'] = self.order.order_code

        return data


# class TransactionOrderSerializer(serializers.ModelSerializer):
#     vitrin_link = serializers.ReadOnlyField()
#
#     class Meta:
#         model = Order
#         exclude = ['order_key']
#
#
# class TransactionSerializer(serializers.ModelSerializer):
#     # user = UserSerializer(read_only=True)
#     order = TransactionOrderSerializer(read_only=True)
#
#     class Meta:
#         model = Transaction
#         exclude = []


# class PromotionCodeSerializer(serializers.ModelSerializer):
#     available_count = serializers.FloatField(read_only=True)
#
#     def get_available_count(self, obj):
#         return obj.usable_count - obj.used_count
#
#     class Meta:
#         model = PromotionCode
#         exclude = []

#
# class PromotionCodeStrSerializer(serializers.ModelSerializer):
#     available_count = serializers.SerializerMethodField(read_only=True)
#
#     def get_available_count(self, obj):
#         return int(obj.usable_count - obj.used_count)
#
#     class Meta:
#         model = PromotionCode
#         fields = ['id', 'code', 'percent_off', 'available_count', 'active']
#

class PaymentRecordConfirmSerializer(serializers.ModelSerializer):
    id2 = serializers.CharField(write_only=True, required=True)
    result = serializers.IntegerField(write_only=True, required=True)
    orderid = serializers.CharField(write_only=True, required=False)
    orderguid = serializers.CharField(write_only=True, required=False)

    payer_obj = UserSummerySerializer(source='payer', read_only=True)
    order_obj = OrderBoughtSerializer(source='order', read_only=True)
    amount = serializers.ReadOnlyField()
    successful = serializers.ReadOnlyField()
    charged = serializers.ReadOnlyField()
    called_back = serializers.ReadOnlyField()

    class Meta:
        model = PaymentRecord
        fields = ['amount', 'successful', 'charged', 'called_back', 'payer_obj', 'order_obj', 'id2', 'result', 'orderid', 'orderguid']

    # def update(self, validated_data):
    def update(self, instance, validated_data):
        if instance.successful is not True or instance.charged is not True:
            try:
                if instance.payment_order_id == validated_data['orderid'] and instance.payment_order_guid == validated_data['orderguid']:
                    payment_successfull = SharifPayment().pay_confirm(instance, validated_data['result'])
                    if payment_successfull:
                        self.confirm_status = True
                        self.message = 'پرداخت موفق بود'
                        return PaymentRecord.objects.get(id=instance.id)
                    else:
                        self.confirm_status = False
                        self.message = 'پرداخت ناموفق بود'
                        return PaymentRecord.objects.get(id=instance.id)
            except:
                return instance
        return instance


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()