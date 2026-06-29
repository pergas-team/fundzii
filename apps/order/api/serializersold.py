from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

# from apps.account.models import Profile
# from apps.account.api.serializers import ProfileSummeryTicketSerializer
# from applications.account.serializers import ProfileSerializer, ProfileSummerySerializer, ProfileSummeryTicketSerializer
from apps.order.models import Order, PromotionCode, Transaction, PaymentRecord, Ticket
# from apps.service.models import EventTicket, Service


class PaymentRecordSerializer(serializers.ModelSerializer):
    # payer = UserSerializer(read_only=True)
    # order_code = serializers.CharField(required=False, write_only=True)
    # related_order = OrderItemSerializer(read_only=True)

    class Meta:
        model = PaymentRecord
        fields = ['amount', 'payer', 'order']
        # fields = ['amount', 'order', 'payer', 'order_code']
        # extra_kwargs = {'amount': {'required': False}, 'order': {'required': False}}
        # extra_kwargs = {'amount': {'required': False}}

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
        fields = ['amount', 'payer', 'order', 'transaction_code', 'payment_order_guid', 'payment_order_id', 'payment_link']


#used
class OrderSerializer(serializers.ModelSerializer):
    use_balance = serializers.BooleanField(default=False, required=False)
    promo_code = serializers.CharField(required=False)

    transaction = serializers.SerializerMethodField(read_only=True, required=False)
    # payment_record = serializers.SerializerMethodField(read_only=True, required=False)
    payment_record = OrderPaymentRecordSerializer(many=True, source='order_payment_records', read_only=True, required=False)

    def get_transaction(self, obj):
        try:
            transaction = obj.transactions.first()
        except:
            transaction = None
        return TransactionSummmerySerializer(transaction, context=self.context).data

    class Meta:
        model = Order
        exclude = ['order_key']

    def create(self, validated_data):
        # validated_data['promotion_code'] = self.promotion_code

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
        try:
            self.transaction = order.transaction
            # self.payment_record = order.get_payment_records()
        except:
            pass
        # validated_data['use_balance'] = use_balance
        return order

    def update(self, instance, validated_data):
        use_balance = validated_data.pop('use_balance', False)
        order = super().update(instance, validated_data)
        order.process(use_balance)
        return order


class OrderBoughtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['order_key']


class OrderDetailSerializer(serializers.ModelSerializer):
    payment_record = OrderPaymentRecordSerializer(many=True, source='order_payment_records', read_only=True, required=False)

    class Meta:
        model = Order
        exclude = ['order_key']


class OrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_status']

    def update(self, instance, validated_data):
        instance.process()
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

    def get_order_obj(self, obj):
        order = obj.order
        return OrderDetailSerializer(order, context=self.context).data

    class Meta:
        model = PaymentRecord
        exclude = ['log_text', 'tref']




class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        exclude = ['order_key']

#
# class TicketsSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(required=False)
#     accepts_coins = serializers.ReadOnlyField()
#
#     class Meta:
#         model = EventTicket
#         exclude = ['service']
#
#     def __init__(self, *args, **kwargs):
#         self.service = kwargs.pop('service', None)
#
#         # kwargs = fix_pk_list(kwargs, 'target_grades')
#         # kwargs = fix_pk_list(kwargs, 'target_states')
#
#         super().__init__(*args, **kwargs)
#
#     def validate(self, attrs):
#         grades = attrs.get("target_grades", [])
#
#         if self.service:
#             for grade in grades:
#                 if not grade in self.service.grades.all():
#                     raise serializers.ValidationError({'target_grades':
#                         "This grade is not in the service target grades, thus, it can't be added to the ticket: %s" % grade})
#
#         attrs['service'] = self.service
#
#         return attrs
#

# class ServiceTicketItemSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(required=False)
#     # target_grades = GradeSerializer(many=True, required=True)
#     # target_states = StateSerializer(many=True, required=True)
#     accepts_coins = serializers.ReadOnlyField()
#
#     class Meta:
#         model = EventTicket
#         exclude = ['service']

#
# class ExtensionSerializer(serializers.ModelSerializer):
#     id = serializers.IntegerField(required=False)
#
#     class Meta:
#         model = TicketExtension
#         exclude = ['service']
#
#     def __init__(self, *args, **kwargs):
#         self.service = kwargs.pop('service', None)
#
#         super().__init__(*args, **kwargs)
#
#     def validate(self, attrs):
#         attrs['service'] = self.service
#
#         return attrs
#
#
# class ServiceAddSerializer(JsonParsingSerializer):
#     json_fields = ['tickets', 'extensions']
#
#     code = serializers.ReadOnlyField()
#     tickets = TicketSerializer(many=True, required=False)
#     extensions = ExtensionSerializer(many=True, required=False)
#     accepts_coins = serializers.ReadOnlyField()
#
#     class Meta:
#         model = Service
#         fields = ['id', 'code', 'grades', 'course_topics', 'title', 'type', 'description', 'ticket_order_description',
#                   'price', 'obsolete_price', 'price_in_coins', 'thumbnail', 'cover', 'tickets', 'extensions',
#                   'featured', 'accepts_coins']
#
#     def __init__(self, **kwargs):
#         self.request = kwargs['context']['request']
#
#         kwargs = fix_pk_list(kwargs, 'course_topics')
#         kwargs = fix_pk_list(kwargs, 'grades')
#
#         super().__init__(**kwargs)
#
#     def validate(self, attrs):
#         tickets = attrs.pop('tickets', [])
#         extensions = attrs.pop('extensions', [])
#
#         if tickets and not self.instance:
#             raise serializers.ValidationError({'tickets': _("You should create the service first.")})
#
#         if extensions and not self.instance:
#             raise serializers.ValidationError({'extensions': _("You should create the service first.")})
#
#         self.tickets = validate_tickets(tickets, self.instance)
#         self.extensions = validate_extensions(extensions, self.instance)
#
#         return attrs
#
#     def save(self, **kwargs):
#         kwargs['owner'] = self.user
#         kwargs['application'] = get_application(self.request)
#
#         service = super(ServiceAddSerializer, self).save(**kwargs)
#
#         for ticket in self.tickets:
#             ticket.save()
#
#         for extension in self.extensions:
#             extension.save()
#
#         return service
#

class PromotionCodeSerializer(serializers.ModelSerializer):
    code = serializers.ReadOnlyField()

    class Meta:
        model = PromotionCode
        fields = ['code']


class AddPromotionCodeSerializer(serializers.ModelSerializer):
    # supervisor = SupervisorSerializer(read_only=True)
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

#
# class ServiceItemSerializer(serializers.ModelSerializer):
#     code = serializers.ReadOnlyField()
#     tickets = serializers.SerializerMethodField()
#     # extensions = ExtensionSerializer(many=True, source='active_extensions')
#     accepts_coins = serializers.ReadOnlyField()
#
#     class Meta:
#         model = Service
#         fields = ['id', 'code', 'grades', 'course_topics', 'title', 'type', 'description', 'ticket_order_description',
#                   'price', 'obsolete_price', 'price_in_coins', 'thumbnail', 'cover', 'tickets', 'extensions',
#                   'featured', 'accepts_coins']
#
#     def __init__(self, *args, **kwargs):
#         context = kwargs.get('context')
#         if context:
#             self.request = context.get('request')
#         else:
#             self.request = None
#
#         self.user = None
#         if self.request:
#             self.user = self.request.user
#
#         super().__init__(*args, **kwargs)
#
#     def get_tickets(self, obj):
#         tickets = obj.active_tickets(self.user)
#
#         return TicketSerializer(tickets, many=True, context=self.context).data
#

# class ServiceFullSerializer(ServiceItemSerializer):
    # grades = GradeSerializer(many=True, read_only=True)
    # course_topics = CourseTopicSerializer(many=True, read_only=True)


class OrderIssueSerializer(serializers.ModelSerializer):
    service_code = serializers.CharField(required=True, write_only=True)
    amount = serializers.ReadOnlyField()
    order_type = serializers.ReadOnlyField()
    # buyer = UserSerializer(read_only=True)
    order_status = serializers.ReadOnlyField()
    service = serializers.SerializerMethodField()
    promo_code = serializers.CharField(required=False)
    promotion_code = PromotionCodeSerializer(read_only=True)
    use_balance = serializers.BooleanField(default=False, required=False)
    #
    # use_coins = serializers.BooleanField(default=False, required=False)
    # ignore_errors = serializers.BooleanField(default=False, required=False)
    # vitrin_link = serializers.ReadOnlyField()
    # service_ticket = serializers.PrimaryKeyRelatedField(queryset=ServiceTicket.objects.all())

    class Meta:
        model = Order
        exclude = ['virtual_order']
        extra_kwargs = {'service_ticket': {'required': False}, 'owners': {'required': False, 'allow_empty': True}}

    def __init__(self, *args, **kwargs):
        request = kwargs['context'].get('request')

        # kwargs = fix_pk_list(kwargs, 'owners')
        # kwargs = fix_pk_list(kwargs, 'extensions')

        if 'data' in kwargs:
            if 'promo_code' in kwargs['data'] and not kwargs['data']['promo_code'].replace(' ', '').replace('\t', ''):
                kwargs['data'].pop('promo_code')

        self.service = None
        self.special_checks = True

        # self.application = get_application(request)
        super().__init__(*args, **kwargs)

    # def validate_service_code(self, service_code):
    #     if not Service.objects.filter(code=service_code).exists():
    #         raise serializers.ValidationError(_("Invalid service code!"))
    #     else:
    #         self.service = Service.objects.get(code=service_code)
    #
    #     if not self.service.enabled:
    #         raise serializers.ValidationError("شما نمیتوانید در این رویداد ثبت‌نام کنید.")
    #
    #     return service_code
    #
    # def validate(self, attrs):
    #     self.promotion_code = None
    #     self.ignore_errors = attrs.pop('ignore_errors', False)
    #     self.use_coins = attrs.pop('use_coins', False)
    #
    #     if self.instance and self.instance.order_status == 'completed':
    #         raise serializers.ValidationError(_("You can't update a completed order!"))
    #
    #     if not attrs.get('owners'):
    #         if self.instance:
    #             attrs['owners'] = self.instance.owners.all()
    #         else:
    #             attrs['owners'] = []
    #
    #     self.profile = get_profile_by_user(self.user)
    #     if not self.profile:
    #         raise serializers.ValidationError(_("The Current user can't make an order!"))
    #
    #     if type(self.profile) == Manager:
    #         if not self.profile or not self.profile.verified:
    #             raise serializers.ValidationError(
    #                 _("Your account needs to be verified in order to make orders!"))
    #
    #         if not (self.profile.verified_phone or self.profile.verified_email):
    #             raise serializers.ValidationError(
    #                 _("You should verify your phone number or email before making any orders!"))
    #
    #     if type(self.profile) == Student:
    #         attrs['owners'] = [self.profile]
    #
    #     if not self.service and self.instance:
    #         self.service = self.instance.service
    #
    #     if self.service:
    #         ticket = attrs.get('service_ticket', [])
    #
    #         if self.instance and self.instance.service_ticket:
    #             ticket = self.instance.service_ticket
    #
    #         if not ticket and self.service.tickets.count() == 1:
    #             ticket = self.service.tickets.first()
    #             attrs['service_ticket'] = ticket
    #
    #         if not ticket:
    #             raise serializers.ValidationError({'service_ticket': _("Field is required!")})
    #
    #         extensions = attrs.get('extensions', [])
    #         owners = attrs.get('owners', [])
    #         promo_code = attrs.get("promo_code", None)
    #
    #         if self.use_coins:
    #             if ticket.price_in_coins == 0:
    #                 raise serializers.ValidationError({'use_coins': _("You can't use coins for this order!")})
    #
    #             if self.profile.coins < ticket.price_in_coins * len(owners):
    #                 raise serializers.ValidationError(_("You don't have enough coins!"))
    #
    #             for extension in extensions:
    #                 if extension.extension_price > 0:
    #                     raise serializers.ValidationError({'use_coins': _(
    #                         "You can't buy this extension with coins: %s.") % extension.extension_title})
    #         else:
    #             if ticket.ticket_price == 0 and ticket.price_in_coins > 0:
    #                 raise serializers.ValidationError(_("You can't buy this ticket without coins!"))
    #
    #         self.promotion_code = PromotionCode.objects.filter(code=promo_code, active=True).filter(
    #             Q(service__isnull=True) | Q(service=self.service)).first()
    #
    #         if promo_code and not self.promotion_code:
    #             raise serializers.ValidationError(_("Invalid promotion code!"))
    #
    #         new_attrs = validate_order_data(buyer=self.profile, service=self.service, owners=owners, ticket=ticket,
    #                                         extensions=extensions, promotion_code=self.promotion_code,
    #                                         instance=self.instance,
    #                                         special_checks=self.special_checks)
    #
    #         for key in new_attrs:
    #             attrs[key] = attrs
    #
    #     return attrs

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
    #
    # def get_service(self, obj):
    #     return ServiceItemSerializer(obj.service, context=self.context).data


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

        # kwargs = fix_pk_list(kwargs, 'owners')
        # kwargs = fix_pk_list(kwargs, 'extensions')

        self.blank_promo = False

        if 'data' in kwargs:
            if 'promo_code' in kwargs['data'] and not kwargs['data']['promo_code'].replace(' ', '').replace('\t', ''):
                kwargs['data'].pop('promo_code')
                self.blank_promo = True

        # self.application = get_application(request)

        self.service = None
        self.order = None

        super().__init__(*args, **kwargs)

    def validate_service_code(self, service_code):
        # self.service = Service.objects.filter(code=service_code).first()

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


class TransactionOrderSerializer(serializers.ModelSerializer):
    vitrin_link = serializers.ReadOnlyField()

    class Meta:
        model = Order
        exclude = ['order_key']

#
# class TicketSerializer(serializers.ModelSerializer):
#     def get_profile_obj(self, obj):
#         profile = obj.profile
#         return ProfileSummeryTicketSerializer(profile, context=self.context).data
#
#     def get_order_obj(self, obj):
#         order = obj.order
#         return OrderSerializer(order, context=self.context).data
#
#     order_obj = serializers.SerializerMethodField()
#     profile_obj = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Ticket
#         exclude = []
#
#
# class SubscriptionSerializer(serializers.ModelSerializer):
#     def get_profile_obj(self, obj):
#         profile = obj.profile
#         return ProfileSummeryTicketSerializer(profile, context=self.context).data
#
#     def get_order_obj(self, obj):
#         order = obj.order
#         return OrderSerializer(order, context=self.context).data
#
#     order_obj = serializers.SerializerMethodField()
#     profile_obj = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Ticket
#         exclude = []


class TransactionSerializer(serializers.ModelSerializer):
    # user = UserSerializer(read_only=True)
    order = TransactionOrderSerializer(read_only=True)

    class Meta:
        model = Transaction
        exclude = []


class TransactionSummmerySerializer(serializers.ModelSerializer):
    # user = UserSerializer(read_only=True)
    # order = TransactionOrderSerializer(read_only=True)

    class Meta:
        model = Transaction
        exclude = []


class PromotionCodeSerializer(serializers.ModelSerializer):
    available_count = serializers.FloatField(read_only=True)

    def get_available_count(self, obj):
        return obj.usable_count - obj.used_count

    class Meta:
        model = PromotionCode
        exclude = []


class PromotionCodeStrSerializer(serializers.ModelSerializer):
    available_count = serializers.SerializerMethodField(read_only=True)

    def get_available_count(self, obj):
        return int(obj.usable_count - obj.used_count)

    class Meta:
        model = PromotionCode
        fields = ['id', 'code', 'percent_off', 'available_count', 'active']

#
# class SubscriptionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Subscription
#         exclude = []
#         # fields = ['id', 'code', 'percent_off', 'available_count', 'active']

# def validate_tickets(tickets_data, service):
#     tickets_errors = []
#     tickets = []
#
#     if tickets_data:
#         for ticket in tickets_data:
#             id = ticket.pop('id', None)
#
#             ticket['target_states'] = [state.id for state in ticket.get('target_states', [])]
#             ticket['target_grades'] = [grade.id for grade in ticket.get('target_grades', [])]
#
#             ticket_instance = None
#             if id:
#                 pass
#                 # ticket_instance = ServiceTicket.objects.filter(service=service, id=id).first()
#
#             ticket_serializer = TicketSerializer(instance=ticket_instance, service=service, data=ticket)
#
#             if ticket_serializer.is_valid(raise_exception=False):
#                 tickets.append(ticket_serializer)
#             else:
#                 tickets_errors.append(ticket_serializer.errors)
#
#         if tickets_errors:
#             raise serializers.ValidationError({'tickets': tickets_errors})
#
#     return tickets

#
# def validate_extensions(extentsions_data, service):
#     extensions_errors = []
#     extensions = []
#
#     if extentsions_data:
#         for extension in extentsions_data:
#             id = extension.pop('id', None)
#
#             extension_instance = None
#             if id:
#                 extension_instance = TicketExtension.objects.filter(service=service, id=id).first()
#
#             extension_serializer = ExtensionSerializer(instance=extension_instance, service=service, data=extension)
#
#             if extension_serializer.is_valid(raise_exception=False):
#                 extensions.append(extension_serializer)
#             else:
#                 extensions_errors.append(extension_serializer.errors)
#
#         if extensions_errors:
#             raise serializers.ValidationError({'extensions': extensions_errors})
#
#     return extensions
#
#
# def validate_order_data(buyer, service, owners, ticket=None, extensions=None, promotion_code=None, instance=None,
#                         special_checks=True, ignore_errors=False, check_pending_orders=True):
#     if type(buyer) == School:
#         if special_checks:
#             if not buyer.gender_group:
#                 raise serializers.ValidationError(
#                     _("You should set your gender_group before you can make an order!"))
#
#     elif type(buyer) == Student:
#         if special_checks:
#             if not buyer.grade:
#                 raise serializers.ValidationError(_("You should set your grade before you can make an order!"))
#             if not buyer.district:
#                 raise serializers.ValidationError(_("You should set your district before you can make an order!"))
#             if not buyer.gender:
#                 raise serializers.ValidationError(_("You should set your gender before you can make an order!"))
#
#     attrs = []
#
#     student_conflict = []
#     grade_conflict = []
#     register_conflict = []
#     gender_conflict = []
#     is_pending = []
#
#     conflicted = []
#
#     for owner in owners:
#         student = Student.objects.filter(id=owner.id).first()
#
#         if not student:
#             student_conflict.append(owner)
#
#         else:
#             if not service.can_take(owner.id) or \
#                     (ticket and ticket.target_grades.exists() and not student.grade in ticket.target_grades.all()):
#                 grade_conflict.append(owner.username)
#
#                 conflicted.append(owner)
#
#             if not service.can_student_register(student.username):
#                 register_conflict.append(student.username)
#                 conflicted.append(owner)
#
#             if special_checks:
#                 if not student.gender:
#                     gender_conflict.append(student.username)
#                     conflicted.append(owner)
#
#             if check_pending_orders and service.has_order(owner.id, statuses=['new', 'pending'], instance=instance):
#                 is_pending.append(owner.username)
#                 conflicted.append(owner)
#
#     if not ignore_errors:
#         if grade_conflict:
#             raise serializers.ValidationError(
#                 _("User: %s cant't take this service!") % ', '.join(grade_conflict))
#
#         if register_conflict:
#             raise serializers.ValidationError(
#                 _("User: %s cant't register for this service!") % ', '.join(register_conflict))
#
#         if gender_conflict:
#             raise serializers.ValidationError(_(
#                 "The gender of these students is undefined. you should define it by uploading an excel including their data."))
#
#         if is_pending:
#             raise serializers.ValidationError(_(
#                 "User: {0} has a pending order for the service. If you made the order, you can update it in orders list in menu.").format(
#                 ', '.join(is_pending)))
#     else:
#         new_owners = []
#         for owner in owners:
#             if not owner in conflicted:
#                 new_owners.append(owner)
#
#         if not new_owners:
#             raise serializers.ValidationError(_("List of students is empty!"))
#
#         attrs['owners'] = new_owners
#         owners = new_owners
#
#     if ticket:
#         if not ticket.service.id == service.id or not ticket.active:
#             raise serializers.ValidationError({'service_ticket': _("Invalid Ticket!")})
#         if ticket.ticket_stock_count and len(owners) + ticket.bought_count > ticket.ticket_stock_count:
#             raise serializers.ValidationError({'service_ticket': _("Ticket out of stock!")})
#
#         if type(buyer) in [Student, School]:
#             if ticket.target_states.exists() and not buyer.district.state in ticket.target_states.all():
#                 raise serializers.ValidationError({'service_ticket': _("Invalid ticket for your state!")})
#
#             if ticket.target_user_type == 'school' and type(buyer) != School or \
#                                     ticket.target_user_type == 'student' and type(buyer) != Student:
#                 raise serializers.ValidationError({'service_ticket': _("Invalid ticket for your user group!")})
#
#         if len(owners) and len(owners) < ticket.min_order_count:
#             can_buy = Order.objects.filter(buyer=buyer, service_ticket=ticket, order_status='completed').exists()
#
#             if not can_buy and ticket.for_hosts:
#                 from applications.exams.models import Exam
#                 event = Exam.objects.filter(id=ticket.service.id).first()
#
#                 if event:
#                     can_buy = event.is_host(buyer)
#
#             if not can_buy:
#                 raise serializers.ValidationError({'service_ticket': _(
#                     "You can't use this ticket for orders with less than {} students!").format(ticket.min_order_count)})
#
#     if extensions:
#         for extension in extensions:
#             if not extension.service.id == service.id or not extension.active:
#                 raise serializers.ValidationError({'extensions': _("Invalid extension: %s") % extension})
#
#             if extension.extension_stock_count and len(
#                     owners) + extension.bought_count > extension.extension_stock_count:
#                 raise serializers.ValidationError({'extensions': _("Extension out of stock: %s") % extension})
#
#             if len(owners) and len(owners) < extension.min_order_count:
#                 if not Order.objects.filter(buyer=buyer, extensions=extension, order_status='completed').exists():
#                     raise serializers.ValidationError({'extensions': _(
#                         "You can't use this extension for orders with less than {} students!").format(
#                         extension.min_order_count)})
#
#     if promotion_code:
#         if promotion_code.get_used_count(instance) + len(owners) > promotion_code.usable_count:
#             raise serializers.ValidationError(_("Promotion code is not available!"))
#
#         if promotion_code.target_user_type not in ['both', get_group(buyer)]:
#             raise serializers.ValidationError(_("Promotion code is not available!"))
#
#     return attrs
