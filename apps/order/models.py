from django.db import models
import binascii
import datetime
import os
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from jdatetime import GregorianToJalali

import string

from apps.order.sharifpayment import SharifPayment

ORDER_KEY_LENGTH = 12
SLUG_CHARACTERS = string.digits + string.ascii_letters + string.ascii_lowercase

from apps.account.models import User, Notification, GrantRequest
from apps.lab.models import Request


class PromotionCode(models.Model):
    code = models.CharField(max_length=255, verbose_name="کد")
    percent_off = models.PositiveSmallIntegerField(default=0, verbose_name="درصد تخفیف")
    usable_count = models.PositiveIntegerField(verbose_name="تعداد")
    used_count = models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده شده")

    active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"

    def save(self, **kwargs):
        if self.percent_off > 100:
            self.percent_off = 100

        try:
            self.used_count = self.get_used_count()
        except ValueError:
            pass

        return super(PromotionCode, self).save()

    def get_used_count(self, instance=None):
        orders = self.orders.filter(order_status__in=['completed', 'pending'])

        if instance:
            orders = orders.exclude(id=instance.id)

        used_count = orders.count()

        if not used_count:
            used_count = 0

        return used_count

    def get_used_amount(self, instance=None):
        orders = self.orders.filter(order_status__in=['completed', 'pending'])

        if instance:
            orders = orders.exclude(id=instance.id)

        total_orders_amount = orders.aggregate(Sum('amount')).get('amount__sum', 0)

        if not total_orders_amount:
            total_orders_amount = 0

        used_amount = int(total_orders_amount * (float(self.percent_off) / 100))

        return used_amount


class Order(models.Model):
    TYPES = (('user', 'کاربر'), ('expert', 'کارشناس'))
    STATUSES = (
        ('new', 'جدید'), ('pending', 'در انتظار'), ('completed', 'تکمیل شده'), ('canceled', 'لغو شده'))

    request = models.ForeignKey(Request, related_name='orders', on_delete=models.PROTECT, verbose_name="درخواست", blank=True, null=True)

    buyer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bought_orders', verbose_name="خریدار", blank=True, null=True)

    order_type = models.CharField(max_length=31, choices=TYPES, default='user', verbose_name="نوع سفارش",
                                  help_text="Choices: ['user', 'expert']")
    order_status = models.CharField(max_length=31, choices=STATUSES, default='new', verbose_name="وضعیت سفارش",
                                    help_text="Choices: ['new', 'pending', 'completed', 'canceled']")
    amount_wo_pc = models.PositiveIntegerField(default=0, verbose_name="مقدار بدون تخفیف")
    amount = models.PositiveIntegerField(default=0, verbose_name="مقدار")
    paid = models.PositiveIntegerField(default=0, verbose_name="میزان پرداختی")

    description = models.TextField(verbose_name="توضیحات", blank=True, null=True)

    order_code = models.CharField(max_length=255, unique=True, verbose_name="کد سفارش", blank=True, null=True)
    order_key = models.CharField(max_length=31, unique=True, verbose_name="کلید سفارش", blank=True, null=True)

    promotion_code = models.ForeignKey(PromotionCode, on_delete=models.SET_NULL, related_name='orders', verbose_name="کد تخفیف", blank=True, null=True)

    grant_request1 = models.ForeignKey(GrantRequest, on_delete=models.SET_NULL, related_name='gr_order1', blank=True, null=True)
    grant_request2 = models.ForeignKey(GrantRequest, on_delete=models.SET_NULL, related_name='gr_order2', blank=True, null=True)

    is_returned = models.BooleanField(default=False, verbose_name='مبلغ عودت شده')

    final_prepayment_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ نهایی پیش‌پرداخت پس از تخفیف")
    grant_discount_prepayment_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ کسر شده از گرنت")
    labsnet_discount_prepayment_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ کسر شده از لبزنت")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش ها"

    def save(self, *args, **kwargs):
        if not self.order_code:
            self.order_code = binascii.hexlify(os.urandom(6)).decode()

        if not self.order_key:
            self.order_key = ''.join(random.SystemRandom().choice(SLUG_CHARACTERS) for _ in range(ORDER_KEY_LENGTH))

        return super().save(*args, **kwargs)

    def calculate_price(self):
        amount = 0
        if self.request:
            amount = self.request.price
            self.amount_wo_pc = self.request.price_wod

        if self.promotion_code:
            amount -= amount * self.promotion_code.percent_off / 100
            self.promotion_code.used_count += 1
            self.promotion_code.save()

        try:
            if self.grant_request1 or self.grant_request2:
                grants_amount = (self.grant_request1.remaining_amount or 0) + (self.grant_request2.remaining_amount or 0)
                if grants_amount <= amount:
                    amount -= grants_amount
                    self.grant_request1.remaining_amount = 0
                    self.grant_request2.remaining_amount = 0

                if grants_amount > amount:
                    if self.grant_request1 and self.grant_request1.remaining_amount <= amount:
                        amount -= self.grant_request1.remaining_amount
                        self.grant_request1.remaining_amount = 0
                        if self.grant_request2 and amount != 0 and self.grant_request2.remaining_amount <= amount:
                            amount -= self.grant_request2.remaining_amount
                            self.grant_request2.remaining_amount = 0
                        elif self.grant_request2 and amount != 0 and  amount < self.grant_request2.remaining_amount:
                            self.grant_request2.remaining_amount -= amount
                            amount = 0
                    elif self.grant_request1 and amount < self.grant_request1.remaining_amount:
                        self.grant_request1.remaining_amount -= amount
                        amount = 0
        except:
            pass


        # if self.request.discount != 0:
        #     amount -= amount * self.request.discount / 100
            # price = amount * self.request.discount / 100

        self.amount = amount

    def process(self, use_balance=False, pay=False):
        self.calculate_price()
        if self.amount == 0:
            if not self.request.has_prepayment:
                self.order_status = 'completed'
        # elif self.order_type == 'expert':
        #     self.order_status = 'completed'
        #     self.paid = self.amount
        else:
            if use_balance:
                buyer_profile = self.buyer
                if buyer_profile:
                    if buyer_profile.balance >= self.amount:
                        buyer_profile.balance -= self.amount
                        self.paid = self.amount
                        buyer_profile.save()
                        self.transaction = Transaction.objects.create(profile=self.buyer, order=self, amount=self.paid)
                        self.order_status = 'completed'
                    else:
                        self.paid = buyer_profile.balance
                        buyer_profile.balance = 0
                        buyer_profile.save()
                        self.transaction = Transaction.objects.create(profile=self.buyer, order=self, amount=self.paid)
                        self.order_status = 'pending'
            else:
                self.paid = 0
                # self.transaction = Transaction.objects.create(profile=self.buyer, order=self, amount=self.paid)
                self.order_status = 'pending'

        self.save()

        if self.order_status == 'completed':
            self.request.change_status('next', 'Successfully paid', self.request.owner)
        else:
            if self.request.has_prepayment:
                self.set_prepayment()
                # user = (self.buyer if self.buyer.account_type == "personal" else self.request.owner.linked_users.all().first())
                # payment_record, created = PaymentRecord.objects.get_or_create(payment_type='prepayment', order=self, amount=int(self.request.total_prepayment_amount),
                #                                               payer=self.buyer)
                # if created:
                #     success, response = SharifPayment().pay_request(user=user, payment_record=payment_record)
                #     if success:
                #         pass
                #     else:
                #         return response
            if pay:
                # payment_record = self.get_payment_records()
                # if not payment_record.exists():
                user = (self.buyer if self.buyer.account_type == "personal" else self.request.owner.linked_users.all().first())
                payment_record = PaymentRecord.objects.create(order=self, amount=self.remaining_amount(), payer=self.buyer)
                success, response = SharifPayment().pay_request(user=user, payment_record=payment_record)
                if success:
                    pass
                else:
                    return response

    def calculate_raw_prepayment_amount(self):
        return Decimal(self.request.total_prepayment_amount or 0)

    def calculate_labsnet_discount(self, base_amount):
        today = datetime.date.today()
        original = Decimal(base_amount)

        def apply_credit(labsnet):
            if not labsnet or labsnet.end_date < today:
                return Decimal(0)
            try:
                max_discount = Decimal(labsnet.remain.replace(',', ''))
                percent = Decimal(labsnet.percent) / Decimal(100)
                return min(original * percent, max_discount, original)
            except:
                return Decimal(0)

        if self.request.parent_request:
            ln1, ln2 = self.request.parent_request.labsnet1, self.request.parent_request.labsnet2
        else:
            ln1, ln2 = self.request.labsnet1, self.request.labsnet2

        if ln1 and ln2 and ln1 == ln2:
            ln2 = None

        credits = [ln for ln in [ln1, ln2] if ln and ln.end_date >= today]
        credits = sorted(credits, key=lambda l: (-Decimal(l.percent), -Decimal(l.remain.replace(',', ''))))

        used = Decimal(0)
        for c in credits:
            d = apply_credit(c)
            used += d
            original -= d
        return used

    def calculate_grant_discount(self, remaining):
        remaining = Decimal(remaining)
        used = Decimal(0)

        for grant in [self.request.grant_request1, self.request.grant_request2]:
            if grant and remaining > 0:
                amt = min(grant.remaining_amount, remaining)
                used += amt
                remaining -= amt
        return used

    def process_prepayment_payment(self, final_amount):
        if final_amount <= 0:
            self.request.prepayment_payed()
            return
        user = (
            self.buyer
            if self.buyer.account_type == "personal"
            else self.request.owner.linked_users.all().first()
        )
        payment_record, created = PaymentRecord.objects.get_or_create(
            payment_type='prepayment',
            order=self,
            amount=int(final_amount),
            payer=self.buyer
        )
        if created:
            success, response = SharifPayment().pay_request(user=user, payment_record=payment_record)
            if not success:
                return response

    def set_prepayment(self):
        self.description = f"set_prepayment: has_prepayment:{self.request.has_prepayment} order_status:{self.order_status} is_completed:{self.request.is_completed}"
        self.save()
        if not (self.request.has_prepayment and self.request.is_completed):
            return

        raw = self.calculate_raw_prepayment_amount()
        labsnet = self.calculate_labsnet_discount(raw)
        grant = self.calculate_grant_discount(raw - labsnet)
        final = max(raw - labsnet - grant, 0)

        self.final_prepayment_amount = Decimal(final)
        self.labsnet_discount_amount = Decimal(labsnet)
        self.grant_discount_amount = Decimal(grant)
        self.description += f"raw:{raw} - labsnet:{labsnet} - grant:{grant} - final:{final}"
        self.save()

        self.process_prepayment_payment(final)


    def set_ticket(self):
        if not Ticket.objects.filter(profile_id=self.buyer.id, order=self).exists():
            Ticket.objects.create(profile_id=self.buyer.id, order=self)

    def set_completed(self, payment_record):
        if self.order_status == 'pending':
            self.paid += payment_record.amount
            self.order_status = 'completed'
            self.save()
            # self.request.change_status('next', 'Successfully paid', self.request.owner)
            for child in self.request.child_requests.all():
                try:
                    child.change_status('next', 'Successfully paid', self.request.owner)
                except:
                    pass

    def cancel(self):
        if self.order_status == 'pending':

            try:
                buyer = self.buyer
                if buyer:
                    buyer.balance += self.paid
                    buyer.save()
                    self.paid = 0
                    self.transactions.all().update(returned=True)
            except:
                pass

            if self.request:
                try:
                   self.request.revoke_grant_usage()
                except Exception:
                    pass

            self.order_status = 'canceled'
            self.save()

            try:
                if self.promotion_code:
                    self.promotion_code.save()
            except:
                pass

    @staticmethod
    def get_amount(ticket, extensions, owners, promotion_code=None):
        amount = ticket.price

        if promotion_code:
            amount -= amount * promotion_code.percent_off / 100
        return amount


    def get_payment_records(self):
        return self.order_payment_records.all()

    def __str__(self):
        if self.buyer:
            if self.request:
                return "%s : %s" % (self.buyer.get_full_name(), self.request)
        else:
            return self.order_code

    def buyer_full_name(self):
        return self.buyer.get_full_name()

    buyer_full_name.short_description = "Buyer Full Name"

    def remaining_amount(self):
        # if pay:
        payment_records = self.get_payment_records().filter(successful=True)
        total_paid = payment_records.aggregate(total_amount=models.Sum('amount'))['total_amount'] or 0
        # return (self.amount - self.paid) - total_paid
        price = self.request.price or 0
        if price == total_paid:
            return 0
        return (price - total_paid)
        # return self.amount - self.paid

    # def set_event_ticket(self):
    #     if not self.event_ticket:
    #         self.event_ticket = self.event.get_default_ticket()
    #         self.save()
    #     return self.event_ticket


class PaymentRecord(models.Model):
    TYPES = (('order', 'پرداخت سفارش'), ('account', 'شارژ اکانت'), ('prepayment', 'پیش پرداخت'))
    SETTLEMENT_TYPES = (('pos', 'کارتخوان'),
                        ('iopay', 'درگاه پرداخت شریف'),
                        ('bank', 'پرداخت بانکی'),
                        ('eopay', 'درگاه خارجی'),
                        ('cash', 'نقدی'))

    payer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payer_payment_records', verbose_name='پرداخت کننده', blank=True, null=True)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='order_payment_records', verbose_name="سفارش",
                                      help_text="The order we want to pay for.", blank=True, null=True)
    payment_type = models.CharField(max_length=31, choices=TYPES, default='order', verbose_name='نوع پرداخت',
                                    help_text="Choices: ['شارژ اکانت', 'پرداخت سفارش', 'پیش پرداخت']")
    settlement_type = models.CharField(max_length=31, choices=SETTLEMENT_TYPES, default='iopay', verbose_name='نوع تسویه',
                                    help_text="Choices: ['درگاه', 'کارتخوان']")
    amount = models.BigIntegerField(default=0, verbose_name='مقدار')
    successful = models.BooleanField(default=False, verbose_name='موفق')
    charged = models.BooleanField(default=False, verbose_name='شارژ شده')
    transaction_code = models.CharField(max_length=255, verbose_name='کد تراکنش', blank=True, null=True)
    tref = models.CharField(max_length=255, verbose_name='کد مرجع بانک', blank=True, null=True)

    payment_order_guid = models.CharField(max_length=255, verbose_name='کد درگاه', blank=True, null=True)
    payment_order_id = models.CharField(max_length=255, verbose_name='کد سفارش درگاه', blank=True, null=True)
    payment_link = models.CharField(max_length=255, verbose_name='لینک درگاه', blank=True, null=True)

    called_back = models.BooleanField(default=False, verbose_name='برگشت')

    is_returned = models.BooleanField(default=False, verbose_name='مبلغ عودت شده')
    is_lock = models.BooleanField(default=False, verbose_name='قفل شده')

    log_text = models.TextField(default="", verbose_name="Log Text", blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name="Paid at")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")


    class Meta:
        verbose_name = 'تراکنش پرداخت'
        verbose_name_plural = 'تراکنش های پرداخت'

    def __str__(self):
        return " %s: %s" % (self.payer.get_full_name(), self.amount)

    def save(self, *args, **kwargs):
        if not self.transaction_code:
            self.transaction_code = ''.join(random.SystemRandom().choice(string.digits) for _ in range(10))
        super(PaymentRecord, self).save(*args, **kwargs)

    def change_to_account_type(self):
        self.payment_type = 'account'
        self.order = None
        self.save()

    def payment_type_check(self):
        if self.payment_type == 'order':
            if self.order.amount == self.amount + self.order.paid and self.order.order_status == 'pending':
                return True
            else:
                return False
        elif self.payment_type == 'account':
            return True


    def set_payed(self):
        self.successful = True

        # if not self.payment_type_check():
        #     self.change_to_account_type()

        try:
            if self.order and self.order.order_status == 'pending':
                if self.payment_type == "prepayment":
                    self.order.request.prepayment_payed()
                    self.charged = True

                else:
                    self.order.set_completed(self)
                    self.charged = True
                profile = self.order.buyer
            else:
                profile = self.payer
                if profile:
                    profile.balance += self.amount
                    profile.save()
                    self.charged = True
        #
        #     send_sms_to_user(profile.user.username, 'پرداخت شما با موفقیت انجام شد')
            notification = Notification.objects.create(
                user=profile,
                type='success',
                title='پرداخت موفق',
                content='پرداخت شما با موفقیت انجام شد.',
            )
        except:
            # pass  # todo handle exception
            notification = Notification.objects.create(
                user=self.payer,
                type='danger',
                title='پرداخت ناموفق',
                content='پرداخت شما ناموفق بود.',
            )

        self.save()

    def add_log(self, log):
        self.log_text += "\n%s" % log

        self.save()

    def payer_full_name(self):
        return self.payer.get_full_name()

    payer_full_name.short_description = "Payer"

    def service_name(self):
        if self.order:
            return self.order.request.subject
        else:
            return "Credit Payment"

    service_name.short_description = "Event"

    def payer_code(self):
        code = "-"
        code = self.payer.username
        return code

    payer_code.short_description = "Phone Number"

    def confirm_payment(self):
        # only for special occasions where zarrinpal fails us!
        if not self.successful and self.tref:
            # from applications.order.zarrinpal import ZarrinPalConfirmSerializer
            self.related_order = None
            self.save()

            # payment_serializer = ZarrinPalConfirmSerializer(data={'Authority': self.tref, 'Status': 'OK'})
            # if payment_serializer.is_valid(raise_exception=False):
            #     return True

        return False



class Transaction(models.Model):
    profile = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions', verbose_name="کاربر")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, blank=True, null=True, related_name='transactions', verbose_name="سفارش")

    amount = models.BigIntegerField(default=0, verbose_name="مقدار")

    returned = models.BooleanField(default=False, verbose_name="بازگشت اعتبار",
                                   help_text="Shows if the money is returned to user profile. (When order is canceled)")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "Transaction Record"
        verbose_name_plural = "Transaction Records"

    def __str__(self):
        return "%s : %s" % (self.order, self.amount)

    def user_full_name(self):
        return self.profile.get_full_name()


class Ticket(models.Model):
    profile = models.ForeignKey(User, on_delete=models.PROTECT, related_name='tickets', verbose_name="پروفایل")
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='tickets', verbose_name="سفارش")

    # seat_number = models.CharField(max_length=4, verbose_name="Seat Number", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")

    class Meta:
        verbose_name = "بلیت"
        verbose_name_plural = "بلیت ها"

    def __str__(self):
        return "%s - %s" % (self.profile, self.order.request)


#
# class BalanceRecord(models.Model):
#     STATUSES = (
#         ('requested', 'درخواست شده'), ('payed', 'پرداخت شده'), ('rejected', 'رد شده'))
#
#     receiver = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name='requested_balances', verbose_name="دریافت کننده")
#     payer = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name='payed_balances', verbose_name="پرداخت کننده", blank=True, null=True)
#
#     balance_status = models.CharField(max_length=31, choices=STATUSES, default='requested',
#                                       verbose_name="وضعیت",
#                                       help_text="Choices: ['درخواست شده', 'پرداخت شده', 'رد شده']")
#     amount = models.BigIntegerField(default=0, verbose_name="مقدار")
#     requester_message = models.TextField(verbose_name="پیام درخواست دهنده", blank=True, null=True)
#     payer_message = models.TextField(verbose_name="پیام پرداخت کننده", blank=True, null=True)
#
#     issued_at = models.DateTimeField(auto_now_add=True, verbose_name="Issued at")
#     answered_at = models.DateTimeField(verbose_name="Answered at", blank=True, null=True)
#
#     class Meta:
#         verbose_name = "Balance Record"
#         verbose_name_plural = "Balance Records"
#
#     def __str__(self):
#         return "%s : %s" % (self.receiver.get_full_name(), self.amount)
#
#     def receiver_full_name(self):
#         return self.receiver.get_full_name()
