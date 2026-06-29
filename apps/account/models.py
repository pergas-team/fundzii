from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core import validators
from django.utils import timezone
import requests
import json
from django.db import transaction

import logging
from django.conf import settings
from requests.adapters import HTTPAdapter, Retry

logger = logging.getLogger(__name__)

class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name='نام')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')

    class Meta:
        verbose_name = 'دانشکده'
        verbose_name_plural = 'دانشکده ها'

    def __str__(self):
        return self.name


class PhoneValidator(validators.RegexValidator):
    regex = r'^\+\d{1,3}\d{9,12}$'
    message = _('Enter a valid phone number.')


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('staff', _('Staff')),
        ('customer', _('Customer')),
    )

    ACCOUNT_TYPE_CHOICES = (
        ('personal', _('Personal')),
        ('business', _('Business')),
    )

    CUSTOMER_TYPE_CHOICES = (
        (1, 'دانشگاه صنعتی شریف'),
        (2, 'سایر دانشگاه‌ها و موسسات آموزشی'),
        (3, 'صنایع و شرکت'),
        (4, 'سایر'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='personal')
    customer_type = models.IntegerField(max_length=3, choices=CUSTOMER_TYPE_CHOICES, default=4)
    national_id = models.CharField(_("national ID"), max_length=15,
                                   # unique=True,
                                   null=True,
                                   blank=True,
                                   help_text=_("Enter your national ID."),
                                   error_messages={
                                        'required': 'کد ملی اجباری است.',
                                        'blank': 'کد ملی نمی‌تواند خالی باشد.',
                                        'invalid': 'کد ملی وارد شده معتبر نیست.',
                                        'max_length': 'کد ملی باید حداکثر 10 رقم باشد.',
                                        'min_length': 'کد ملی باید حداقل 10 رقم باشد.',
                                        'unique': 'کاربری با این کد ملی وجود دارد.'
                                   }
                                   )

    role = models.ManyToManyField('Role', blank=True)
    access_level = models.ManyToManyField('AccessLevel', blank=True)

    balance = models.BigIntegerField(default=0, verbose_name="اعتبار")

    educational_field = models.ForeignKey(EducationalField, on_delete=models.PROTECT, null=True, blank=True)
    educational_level = models.ForeignKey(EducationalLevel, on_delete=models.PROTECT, null=True, blank=True)
    department = models.ForeignKey('Department', related_name='users', blank=True, null=True, on_delete=models.PROTECT, verbose_name='دپارتمان')

    student_id = models.CharField(_("student ID"), max_length=50, unique=True, null=True, blank=True, help_text=_("Enter your student ID."))
    address = models.CharField(_("address"), max_length=255, null=True, blank=True, help_text=_("Enter your address."))
    telephone = models.CharField(_("telephone"), max_length=255, null=True, blank=True, help_text=_("Enter your company telephone."))

    postal_code = models.CharField(_("postal code"), max_length=20, blank=True, null=True, help_text=_("Enter your postal code."))
    company_national_id = models.CharField(_("company national ID"), max_length=15, unique=True, null=True, blank=True, help_text=_("Enter your company national ID."))
    company_name = models.CharField(_("company name"), max_length=150, null=True, blank=True, help_text=_("Enter your company name."))
    company_economic_number = models.CharField(_("company economic number"), max_length=25, unique=True, null=True, blank=True, help_text=_("Enter your company economic number."))
    # research_grant = models.BigIntegerField(default=0, verbose_name="گرنت پژوهشی")
    # labsnet_grant = models.BigIntegerField(default=0, verbose_name="گرنت لبزنت")

    company_telephone = models.CharField(_("company telephone"), max_length=255, null=True, blank=True, help_text=_("Enter your company telephone."))
    linked_users = models.ManyToManyField('self', symmetrical=False, related_name='linked_to_users', blank=True)

    OTP = models.CharField(max_length=64, null=True, blank=True)
    is_sharif_student = models.BooleanField(default=False, verbose_name='دانشجوی شریف')
    is_partner = models.BooleanField(default=False, verbose_name='شرکت همکار')

    # phone_validator = PhoneValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. Enter a valid phone number. Example: +989123456789"
        ),
        # validators=[phone_validator],
        error_messages={
            'required': 'شماره اجباری است.',
            'blank': 'شماره نمی‌تواند خالی باشد.',
            'invalid': 'شماره وارد شده معتبر نیست.',
            'max_length': 'شماره نباید بیشتر از 150 کاراکتر باشد.',
            'min_length': 'شماره باید حداقل 3 کاراکتر باشد.',
            'unique': 'کاربری با این شماره وجود دارد.'
        },
    )

    class Meta:
        pass
        # unique_together = ("username", "national_id")

    def get_access_levels(self):
        roles = self.role.all()
        access_levels = self.access_level.all()
        for role in roles:
            access_levels = access_levels | role.access_level.all()
        return access_levels.distinct()

    def get_dict_access_level(self):
        dict_access_levels = {}
        access_levels = self.get_access_levels()
        keys = [access_level.access_key.split('_')[2] for access_level in access_levels]
        keys = list(dict.fromkeys(keys))
        for key in keys:
            key_access_level = [access_level.access_key.split('_')[0] for access_level in access_levels if access_level.access_key.split('_')[2] == key]
            key_access_level = list(dict.fromkeys(key_access_level))
            dict_access_levels[key] = key_access_level
        return dict_access_levels

    def owners(self):
        return []

    def set_customer_role(self):
        if self.user_type == 'customer' and self.account_type == 'personal':
            if False:  # todo check if role type is teacher
                self.role.add(Role.objects.get(role_key='teacher'))
            elif self.student_id:
                self.role.add(Role.objects.get(role_key='student'))
            self.role.add(Role.objects.get(role_key='customer'))
        elif self.user_type == 'customer' and self.account_type == 'business':
            if False:
                self.role.add(Role.objects.get(role_key='student'))
            self.role.add(Role.objects.get(role_key='customer'))

        """ def labsnet_list(self):
        import requests
        data = {
            "user_name": "sharif_uni",
            "password": "sharif_uni",
            "national_code": f"{self.national_id}",
            "type": "1",
            "org_id": "343",
            "services[0]": "3839"
        }
        response = requests.post(
            'https://labsnet.ir/api/credit_list',
            data=data,
            verify=False
        )
        response.raise_for_status()
        return response.json() """

    def labsnet_list(self):
        username = "sharif_uni"
        password = "sharif_uni"
        is_personal = (self.account_type == 'personal')
        customer_type = '1' if is_personal else '2'
        national_code = (
            self.national_id
            if is_personal
            else self.company_national_id
        )

        data = {
            'user_name': username,
            'password': password,
            'type': customer_type,
            'org_id': "343",  # settings.LABSNET_ORG_ID,
            'national_code': national_code,
            'services[0]': "3839"  # Just to pull the credit list
        }

        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=['POST']
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))

        try:
            resp = session.post(
                'https://labsnet.ir/api/credit_list',
                data=data,
                timeout=(5, 15),  # (connect timeout, read timeout)
                verify=False
            )
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            logger.error(f"Failed to call Labsnet credit_list: {e}")
            return {}

        if "credits" not in result:
            logger.warning(f"Labsnet returned unexpected payload: {result!r}")
            return {}

        return result

    def sync_labsnet_credits(self, labsnet_result: dict):
        from apps.core.functions import safe_jalali_to_gregorian
        if "credits" not in labsnet_result:
            return

        active_ids = set()
        for credit in labsnet_result["credits"]:
            try:
                start_date = safe_jalali_to_gregorian(credit["start_date"])
                end_date = safe_jalali_to_gregorian(credit["end_date"])

                obj, _ = LabsnetCredit.objects.update_or_create(
                    labsnet_id=credit["id"],
                    defaults={
                        "user": self,
                        "amount": credit["amount"],
                        "start_date": start_date,
                        "end_date": end_date,
                        "remain": credit["remain"],
                        "percent": credit["percent"],
                        "title": credit["title"],
                    },
                )
                active_ids.add(obj.labsnet_id)
            except Exception as e:
                logger.warning(f"Error processing Labsnet credit: {credit}. Error: {e}")

        LabsnetCredit.objects.filter(user=self).exclude(labsnet_id__in=active_ids).update(remain=0)


class Role(models.Model):
    name = models.CharField(_("name"), max_length=100)
    access_level = models.ManyToManyField('AccessLevel', blank=True)
    role_key = models.CharField(_("Key"), max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class AccessLevel(models.Model):
    name = models.CharField(_("name"), max_length=100)
    access_key = models.CharField(_("Key"), max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name


class LabsnetCredit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="labsnet_credits", verbose_name="کاربر")
    labsnet_id = models.CharField(max_length=255, unique=True, verbose_name="شناسه لبزنت")
    amount = models.CharField(max_length=255, verbose_name="مبلغ کل")
    start_date = models.DateField(verbose_name="تاریخ شروع")
    end_date = models.DateField(verbose_name="تاریخ پایان")
    remain = models.CharField(max_length=255, verbose_name="مبلغ باقی‌مانده")
    percent = models.CharField(max_length=10, verbose_name="درصد استفاده‌شده")
    title = models.TextField(verbose_name="عنوان اعتبار")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "اعتبار لبزنت"
        verbose_name_plural = "اعتبارهای لبزنت"

    def __str__(self):
        return f"{self.title} ({self.labsnet_id})"


class GrantTransaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions', verbose_name="فرستنده")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions', verbose_name="گیرنده")
    grant_record = models.ForeignKey('GrantRecord', on_delete=models.PROTECT, null=True, blank=True)
    amount = models.BigIntegerField(default=0, verbose_name="مقدار", help_text='مقدار به ریال')
    datetime = models.DateTimeField(default=timezone.now, verbose_name="زمان")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="انقضا")
    STATUS_CHOICES = (
        ('unknown', 'Unknown'),
        ('success', 'Success'),
        ('failure', 'Failure'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unknown')

    def __str__(self):
        return str(self.sender) + " -> " + str(self.receiver) + " : " + str(self.amount) + " : " + str(self.datetime) + " : " + str(self.expiration_date)

    def pay(self):
        self.status = 'success'
        self.save()

    def owners(self):
        return [self.sender, self.receiver]


class GrantRecord(models.Model):
    title = models.CharField(max_length=255)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_records', verbose_name="گیرنده")
    amount = models.BigIntegerField(default=0, verbose_name="مقدار", help_text='مقدار به ریال')
    expiration_date = models.DateField(null=True, blank=True, verbose_name="انقضا")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="زمان")

    def __str__(self):
        return str(self.receiver) + " : " + str(self.amount) + " : " + str(self.expiration_date)

    def get_total_transactions(self):
        return self.granttransaction_set.aggregate(total_amount=models.Sum('amount'))['total_amount'] or 0

    def has_sufficient_funds(self, amount):
        total_transactions = self.get_total_transactions()
        return self.amount >= total_transactions + amount

    def remaining_grant(self):
        total_transactions = self.get_total_transactions()
        return self.amount - total_transactions

    # def pay(self):
    #     try:
    #         if self.check_amount(self.amount):
    #             self.sender.research_grant -= self.amount
    #             self.receiver.research_grant += self.amount
    #             self.status = 'success'
    #             self.sender.save()
    #             self.receiver.save()
    #             self.save()
    #         else:
    #             self.status = 'failure'
    #             self.save()
    #     except:
    #         self.status = 'failure'
    #         self.save()

    def owners(self):
        return [self.receiver]


class GrantRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests', verbose_name="فرستنده")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests', verbose_name="گیرنده")
    approved_grant_record = models.ForeignKey(GrantRecord, on_delete=models.PROTECT, null=True, blank=True)
    approved_amount = models.BigIntegerField(default=0, null=True, blank=True, verbose_name="مقدار دریافتی", help_text='مقدار به ریال')
    approved_datetime = models.DateTimeField(null=True, blank=True, verbose_name="زمان تایید")

    remaining_amount = models.BigIntegerField(default=0, null=True, blank=True, verbose_name="مقدار باقی مانده", help_text='مقدار به ریال')

    requested_amount = models.BigIntegerField(default=0, verbose_name="مقدار درخواستی", help_text='مقدار به ریال')
    datetime = models.DateTimeField(default=timezone.now, verbose_name="زمان")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="انقضا")
    transaction = models.ForeignKey(GrantTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='grant_request', verbose_name="گرنت تراکنش")
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('seen', 'Seen'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')

    def __str__(self):
        return str(self.sender) + " -> " + str(self.receiver) + " : " + str(self.requested_amount) + " : " + str(self.approved_amount) + " : " + str(self.datetime) + " : " + str(self.expiration_date) + " : " + str(self.status)

    def approve(self, approved_amount, expiration_date, approved_grant_record):
        try:
            expiration_date = approved_grant_record.expiration_date
            with transaction.atomic():
                if approved_grant_record.expiration_date and approved_grant_record.expiration_date < timezone.now().date():
                    raise ValueError("GrantRecord has expired and cannot be used for this request.")

                if not approved_grant_record.has_sufficient_funds(approved_amount):
                    raise ValueError("GrantRecord does not have sufficient funds.")

                self.approved_amount = approved_amount
                self.remaining_amount = approved_amount
                self.expiration_date = expiration_date
                self.approved_grant_record = approved_grant_record
                self.approved_datetime = timezone.now()

                if self.transaction:
                    self.transaction.amount = approved_amount
                else:
                    self.transaction = GrantTransaction.objects.create(
                        sender=self.receiver,
                        receiver=self.sender,
                        amount=self.approved_amount,
                        expiration_date=expiration_date,
                        grant_record=approved_grant_record
                    )

                self.transaction.pay()
                self.status = 'approved'
                self.save()
        except Exception as e:
            self.status = 'failed'
            self.save()
            print(f"Error in approve: {e}")

    def revoke(self):
        self.approved_amount -= self.remaining_amount
        self.transaction.amount -= self.remaining_amount
        self.remaining_amount = 0
        self.save()
        self.transaction.save()

    #
    # def approve(self, approved_amount, expiration_date):
    #     try:
    #         expiration_date = self.approved_grant_record.expiration_date
    #         self.approved_amount = approved_amount
    #         self.expiration_date = expiration_date
    #         self.approved_datetime = timezone.now()
    #         if self.transaction:
    #             self.transaction.amount = approved_amount
    #         else:
    #             self.transaction = GrantTransaction.objects.create(sender=self.receiver, receiver=self.sender,
    #                                                                amount=self.approved_amount,
    #                                                                expiration_date=expiration_date,
    #                                                                grant_record=self.approved_grant_record)
    #         self.transaction.pay()
    #         self.status = 'approved'
    #         self.save()
    #     except:
    #         pass

    def owners(self):
        return [self.sender, self.receiver]


class OTPserver(models.Model):
    username = models.CharField(max_length=64, null=True, blank=True)
    password = models.CharField(max_length=64, null=True, blank=True)
    token_expiration = models.DateTimeField(null=True, blank=True)
    token = models.CharField(max_length=512, null=True, blank=True)
    base_url = models.URLField(null=True, blank=True)  #  https://sms.sharif.ir/api

    def send_quick_message(self, phone_numbers, message):
        if self.check_token():
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}
            data = {"Mobile": phone_numbers, "Message": message}
            response = requests.post(f'{self.base_url}/sms/send', data=json.dumps(data), headers=headers)
            # if response.status_code == 200:
            return json.loads(response.text)

    def get_new_token(self):
        headers = {"Content-Type": "application/json"}
        data = {"Username": self.username, "Password": self.password}
        response = requests.post(f'{self.base_url}/system/Authenticate', data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            result = json.loads(response.text)
            self.token = result['token']
            self.token_expiration = result['expiration']
            self.save()
        else:
            pass

    def check_token(self):
        if self.token_expiration:
            if self.token_expiration < timezone.now():  # datetime.datetime.now()
                self.get_new_token()
                return True
            else:
                return True
        else:
            self.get_new_token()
            return True


class Notification(models.Model):
    TYPE_CHOICES = (
        ('danger', 'هشدار'),
        ('warning', 'اخطار'),
        ('success', 'موفقیت'),
        ('info', 'اطلاعات'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="نوع")
    title = models.CharField(blank=True, null=True, max_length=100, verbose_name="عنوان")
    content = models.TextField(verbose_name="محتوا")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")

    read_at = models.DateTimeField(blank=True, null=True, verbose_name="تاریخ خوانده شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"

    def __str__(self):
        return '{} ({}...)'.format(self.title, self.content[:30])

    def owners(self):
        return [self.user]