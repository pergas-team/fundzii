import datetime
from decimal import Decimal, InvalidOperation
from django.db import models
from django.db.models import Sum
import jdatetime
from apps.account.models import User, GrantRequest, Role, LabsnetCredit
from apps.core.labsnet_func import LabsNetClient
from apps.form.models import Form
import math
from django.core.exceptions import ValidationError
import requests
import json


class Request(models.Model):
    owner = models.ForeignKey(User, blank=True, null=True, related_name='requests', on_delete=models.PROTECT,
                              verbose_name='درخواست کننده')
    experiment = models.ForeignKey('Experiment', on_delete=models.PROTECT, verbose_name='آزمایش')
    parameter = models.ManyToManyField('Parameter', blank=True, verbose_name='پارامتر')
    price_sample_returned = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True,
                                                verbose_name='قیمت ارسال نمونه')
    price_wod = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True,
                                    verbose_name='قیمت بدون تخفیف')
    price = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True, verbose_name='قیمت')
    total_prepayment_amount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True,
                                                  verbose_name='مقدار پیش پرداخت')

    parent_request = models.ForeignKey('self', null=True, blank=True, related_name='child_requests',
                                       on_delete=models.SET_NULL, verbose_name='درخواست مادر')
    has_parent_request = models.BooleanField(default=False, verbose_name='درخواست مادر دارد')

    test_duration = models.PositiveIntegerField(blank=True, null=True, default=0)

    discount = models.PositiveIntegerField(blank=True, null=True, default=0)
    discount_description = models.CharField(max_length=120, blank=True, null=True, verbose_name='توضیحات تخفیف')

    is_urgent = models.BooleanField(default=False)
    is_sample_returned = models.BooleanField(default=False, verbose_name='عودت نمونه')

    delivery_date = models.DateField(blank=True, null=True, verbose_name='تاریخ تحویل')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    subject = models.CharField(max_length=100, blank=True, null=True, verbose_name='موضوع درخواست')
    request_number = models.CharField(max_length=20, blank=True, verbose_name='شماره درخواست')
    is_completed = models.BooleanField(default=False, verbose_name='تکمیل شده')
    is_cancelled = models.BooleanField(default=False, verbose_name='لغو شده')
    sample_check = models.BooleanField(default=False, verbose_name='چک نمونه')

    labsnet_code1 = models.CharField(max_length=100, blank=True, null=True, verbose_name='کد لبزنت ۱')
    labsnet_code2 = models.CharField(max_length=100, blank=True, null=True, verbose_name='کد لبزنت ۲')

    labsnet1 = models.ForeignKey(LabsnetCredit, on_delete=models.SET_NULL, related_name='ln_request1', blank=True,
                                 null=True, verbose_name='کد لبزنت ۱')
    labsnet2 = models.ForeignKey(LabsnetCredit, on_delete=models.SET_NULL, related_name='ln_request2', blank=True,
                                 null=True, verbose_name='کد لبزنت ۲')

    grant_request1 = models.ForeignKey(GrantRequest, on_delete=models.SET_NULL, related_name='gr_request1', blank=True,
                                       null=True)
    grant_request2 = models.ForeignKey(GrantRequest, on_delete=models.SET_NULL, related_name='gr_request2', blank=True,
                                       null=True)
    grant_request_discount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True,
                                                 verbose_name='تخفیف پژوهشی')

    labsnet = models.BooleanField(default=False, verbose_name='اعتبار لبزنت')
    labsnet_discount = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True,
                                           verbose_name='تخفیف لبزنت')
    labsnet_description = models.CharField(max_length=200, blank=True, null=True, verbose_name='توضیحات گرنت لبزنت')
    labsnet_result = models.CharField(max_length=2000, blank=True, null=True, verbose_name='نتیجه ثبت لبزنت')

    is_returned = models.BooleanField(default=False, verbose_name='مبلغ عودت شده')
    has_prepayment = models.BooleanField(default=False, verbose_name='نیاز به پیش پرداخت')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به روز رسانی')

    class Meta:
        verbose_name = 'درخواست'
        verbose_name_plural = 'درخواست‌ها'

    def __str__(self):
        return f'{self.experiment} - {self.request_number}'

    # def clean(self):
    #     if self.parent_request and self.child_requests.exists():
    #         raise ValidationError('یک درخواست فرزند نمی‌تواند فرزندان دیگری داشته باشد.')
    #     if self.parent_request and self.has_parent_request:
    #         raise ValidationError('یک درخواست فرزند نمی‌تواند به عنوان درخواست مادر تنظیم شود.')

    def get_all_child_requests(self):
        return self.child_requests.all()

    def get_full_hierarchy(self):
        child_requests = self.child_requests.all()
        return [self] + [child_request.get_full_hierarchy() for child_request in child_requests]

    def save(self, *args, **kwargs):
        # self.clean()
        super().save(*args, **kwargs)

    def set_first_step(self):
        workflow = Workflow.objects.all().first()
        return Status.objects.create(request=self, step=workflow.first_step())

    def lastest_status(self):
        # if not self.child_requests.exists():  # اگر فرزند ندارد
        if self.request_status.order_by('-created_at').exists():
            return self.request_status.order_by('-created_at').first()
        else:
            return self.set_first_step()
        # else:  # اگر درخواست مادر است
        #     statuses = [child.lastest_status() for child in self.child_requests.all()]
        #     if all(status.is_completed for status in statuses):  # همه فرزندان تکمیل شده‌اند
        #         return self.request_status.order_by('-created_at').first()
        #     else:
        #         return min(statuses, key=lambda x: x.created_at)  # زودترین وضعیت فرزندان

    def step_button_action(self, action, description, action_by, value):
        if action in ['next', 'previous', 'reject']:
            self.change_status(action, description, action_by)
            self.save()
        elif action in ['view_result', 'print_result', 'upload_result']:
            pass
        elif action in ['request_discount']:
            self.discount = value
            self.discount_description = description
            self.save()
            self.set_price()
        else:
            pass

    def change_status(self, action, description, action_by):
        lastest_status = self.lastest_status()
        if self.parent_request:
            if self.parent_request.lastest_status().step != lastest_status.step and lastest_status.step.name != 'در انتظار پرداخت':
                raise ValidationError('وضعیت درخواست نمیتواند بیش از یک وضعیت با فاکتور اختلاف داشته باشد.')

        if not self.parent_request:
            for child in self.child_requests.exclude(request_status__step__name__in=['رد شده']):
                step = child.lastest_status().step
                if step.id != self.lastest_status().step.next_step.id:
                    raise ValidationError('وضعیت فاکتور نمیتواند پیشتر از وضعیت درخواست ها باشد.')

        if action == 'next':
            lastest_status.accept = True
            Status.objects.create(request=lastest_status.request, step=lastest_status.step.next_step)
            self.handle_status_changed(lastest_status.step.next_step, action, lastest_status)
        elif action == 'previous':
            lastest_status.reject = True
            Status.objects.create(request=lastest_status.request, step=lastest_status.step.previous_step)
            self.handle_status_changed(lastest_status.step.previous_step, action, lastest_status)
        elif action == 'reject':
            lastest_status.reject = True
            Status.objects.create(request=lastest_status.request, step=lastest_status.step.reject_step)
            self.handle_status_changed(lastest_status.step.reject_step, action, lastest_status)
        lastest_status.complete = True
        lastest_status.description = description
        lastest_status.action_by = action_by
        lastest_status.save()
        if self.parent_request:
            self.parent_request.change_parent_status(action_by)

    def change_parent_status(self, action_by):
        if self.child_requests.exists():
            child_statuses = [child.lastest_status() for child in self.child_requests.all()]

            current_step = self.lastest_status().step
            if any(child_status.step == current_step for child_status in child_statuses):
                pass
                # raise ValidationError(
                #     'نمی‌توانید وضعیت مادر را تغییر دهید تا زمانی که هیچکدام از فرزندان در وضعیت فعلی مادر نباشند.')
            else:
                all_rejected = all(child_status.step == current_step.reject_step for child_status in child_statuses)
                any_in_next_step = any(child_status.step == current_step.next_step for child_status in child_statuses)

                if any_in_next_step:
                    self.change_status('next', 'تغییر خودکار', action_by)

                elif all_rejected:
                    self.change_status('reject', 'تغییر خودکار', action_by)

                else:
                    pass
                    # raise ValidationError(
                    #     'نمی‌توانید وضعیت مادر را تغییر دهید تا زمانی که تمام فرزندان در وضعیت مناسب قرار نگرفته باشند.')

    def update_parent_status(self):
        if self.child_requests.exists():
            if any(child.is_returned for child in self.child_requests.all()):
                self.is_returned = True
            else:
                self.is_returned = False
            try:
                # self.update_delivery_date()
                latest_delivery_date = max(
                    child.delivery_date for child in self.child_requests.all() if child.delivery_date)
                self.delivery_date = latest_delivery_date
            except:
                pass

            self.save()

    def handle_status_changed(self, new_step, action, lastest_status):
        if action == 'next':
            if new_step.name == 'در ‌انتظار نمونه':
                if not self.parent_request and not self.labsnet:
                    self.labsnet_create()
                    self.save()
            if new_step.name == 'در انتظار پرداخت' and (self.labsnet):
                if not self.parent_request:
                    self.labsnet_create_grant()
                    self.save()
        if new_step.name == 'در حال انجام':
            self.delivery_date = datetime.datetime.now()
            self.save()
        if action == 'reject':
            if self.parent_request:
                self.parent_request.set_price()
            if lastest_status.step.name == 'در حال انجام' or lastest_status.step.name == 'در ‌انتظار نمونه':
                self.is_returned = True
                self.save()
                try:
                    order = self.get_latest_order()
                    order.is_returned = True
                    order.save()
                except:
                    pass
                    # self.description += '\n تگ استرداد برای سفارش با خطا مواجه شد'
                    # self.save()

                try:
                    pr = self.get_latest_order_payment_records().first()
                    self.get_latest_order_payment_records().create(payer=pr.payer, order=pr.order, charged=pr.charged,
                                                                   settlement_type=pr.settlement_type,
                                                                   amount=-1 * self.price, payment_type=pr.payment_type,
                                                                   successful=pr.successful, is_returned=pr.is_returned)
                    payment_records = self.get_latest_order_payment_records().filter(successful=True)
                    payment_records.update(is_returned=True)
                except:
                    pass
                    # self.description += '\n تگ استرداد برای پرداخت با خطا مواجه شد'
                    # self.save()

    def owners(self):
        return [self.owner] + self.experiment.owners()

    def set_price(self):
        old_price = self.price
        if self.parent_request:
            if self.experiment.need_turn:
                self.total_prepayment_amount = self.experiment.prepayment_amount if self.experiment.prepayment_amount else Decimal(
                    0)
            # try:
            params = self.parameter.all()
            formresponses = self.formresponse.filter(is_main=True).aggregate(Sum('response_count'))
            price = 0
            for param in params:
                # if self.experiment.need_turn:
                if self.test_duration > 0:
                    temp = self.test_duration
                else:
                    response_sum = formresponses['response_count__sum'] or 0
                    temp = response_sum / int(param.unit_value)
                    # temp = formresponses['response_count__sum'] / int(param.unit_value)
                    temp = math.ceil(temp)
                if self.owner.is_partner:
                    if self.is_urgent:
                        if param.partner_urgent_price:
                            price += int(param.partner_urgent_price) * int(temp)
                        else:
                            price += int(param.urgent_price) * int(temp)
                    else:
                        if param.partner_price:
                            price += int(param.partner_price) * int(temp)
                        else:
                            price += int(param.price) * int(temp)
                else:
                    if self.is_urgent:
                        price += int(param.urgent_price) * int(temp)
                    else:
                        price += int(param.price) * int(temp)
            self.price_sample_returned = Decimal(0)
            self.price_wod = Decimal(price)
            self.price = (price - (price * int(self.discount) / 100))
            # self.apply_labsnet_credits()
            self.save()
            self.parent_request.set_price()
            # except:
            #     self.price_wod = Decimal(0)
            #     self.price = Decimal(0)
            #     self.save()
            #     self.parent_request.set_price()
            #     self.price_sample_returned = Decimal(0)
        else:
            price = 0
            total_prepayment_amount = 0
            children = self.child_requests.exclude(request_status__step__name__in=['رد شده'])
            for child in children:
                try:
                    price += child.price
                except:
                    pass
                if self.has_prepayment:
                    total_prepayment_amount += child.experiment.prepayment_amount
                    # total_prepayment_amount += child.experiment.prepayment_amount if child.experiment.prepayment_amount else Decimal(
                    #     0)

            self.price_wod = price
            self.price = price
            self.total_prepayment_amount = total_prepayment_amount

            # try:
            # if self.grant_request1 or self.grant_request2:
            #     if self.grant_request1 and self.grant_request1.remaining_amount > 0:
            #         if self.grant_request1.remaining_amount >= self.price:
            #             self.grant_request1.remaining_amount -= self.price
            #             self.price = 0
            #         else:
            #             self.price -= self.grant_request1.remaining_amount
            #             self.grant_request1.remaining_amount = 0
            #         self.grant_request1.save()
            #
            #     if self.grant_request2 and self.price > 0 and self.grant_request2.remaining_amount > 0:
            #         if self.grant_request2.remaining_amount >= self.price:
            #             self.grant_request2.remaining_amount -= self.price
            #             self.price = 0
            #         else:
            #             self.price -= self.grant_request2.remaining_amount
            #             self.grant_request2.remaining_amount = 0
            #         self.grant_request2.save()
            # self.grant_request_discount = self.price_wod - self.price
            # except Exception as e:
            #     print(f"An error occurred: {e}")

            if self.is_sample_returned:
                self.price_sample_returned = Decimal(1250000)
                self.price = self.price + self.price_sample_returned
                # self.price_wod = self.price_wod + self.price_sample_returned
            else:
                self.price_sample_returned = Decimal(0)

            if self.labsnet:
                self.set_labsnet_credits()
                # self.price -= int(self.labsnet_discount)

            self.sync_grants_if_price_changed(old_price)

            self.save()


    def current_month_counter(self):
        now = jdatetime.date.today()
        start_of_month = jdatetime.datetime(now.year, now.month, 1)

        if now.month == 12:
            end_of_month = jdatetime.datetime(now.year + 1, 1, 1) - jdatetime.timedelta(days=1)
        else:
            end_of_month = jdatetime.datetime(now.year, now.month + 1, 1) - jdatetime.timedelta(days=1)

        start_of_month_gregorian = start_of_month.togregorian()
        end_of_month_gregorian = end_of_month.togregorian().replace(hour=23, minute=59, second=59)

        return Request.objects.filter(parent_request__isnull=True,
                                      created_at__range=(start_of_month_gregorian, end_of_month_gregorian)).count()

    def get_latest_order_payment_records(self):
        try:
            return self.get_latest_order().get_payment_records()
        except:
            return []

    def get_latest_order(self):
        try:
            return self.orders.order_by('-created_at').first()
        except:
            return []

    def get_child_form_responses(self):
        children = self.get_all_child_requests()
        return FormResponse.objects.filter(request__in=children)

    def get_child_form_responses_count(self):
        form_responses = self.get_child_form_responses()
        total_response_count = form_responses.aggregate(total=Sum('response_count'))['total'] or 0
        return total_response_count


class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name='نام')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')

    # manager = models.ForeignKey('Personnel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مدیر')

    class Meta:
        verbose_name = 'دپارتمان'
        verbose_name_plural = 'دپارتمان‌ها'

    def __str__(self):
        return self.name


class FormResponse(models.Model):
    request = models.ForeignKey('Request', on_delete=models.CASCADE, related_name='formresponse',
                                verbose_name='درخواست')
    form_number = models.CharField(max_length=20, blank=True, verbose_name='شماره نمونه')

    response = models.TextField(blank=True, null=True, verbose_name='پاسخ')
    response_json = models.JSONField(blank=True, null=True, verbose_name='پاسخ')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به روز رسانی')

    copy_check = models.BooleanField(default=False, blank=True, null=True, verbose_name='چک کپی')
    is_main = models.BooleanField(default=False, blank=True, null=True, verbose_name='اصلی')
    response_count = models.IntegerField(default=1, verbose_name='تعداد پاسخ‌ها')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='child_form_response',
                               on_delete=models.SET_NULL, verbose_name='نمونه مادر')

    class Meta:
        verbose_name = 'پاسخ فرم'
        verbose_name_plural = 'پاسخ فرم‌ها'

    def __str__(self):
        return f'{self.request}'

    def owners(self):
        return self.request.owners()

    def set_form_number(self):
        request_formresponses = self.request.formresponse.all().order_by('id')
        counter = 1
        for request_formresponse in request_formresponses:
            request_formresponse.form_number = f'{self.request.request_number.replace("-", "")}{counter:03d}'
            request_formresponse.save()
            counter += 1


class Workflow(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام گردش کار')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال بودن')

    class Meta:
        verbose_name = 'گردش کار'
        verbose_name_plural = 'گردش کارها'

    def __str__(self):
        return self.name

    def first_step(self):
        try:
            return self.steps.filter(is_first_step=True).first()
        except:
            return None

    def get_ordered_steps(self):
        ordered_steps = []
        reject_steps_set = set()

        step = self.first_step()
        while step:
            if step not in ordered_steps:
                ordered_steps.append(step)
            step = step.next_step

        for step in ordered_steps:
            reject_step = step.reject_step
            while reject_step and reject_step not in reject_steps_set:
                reject_steps_set.add(reject_step)
                reject_step = reject_step.reject_step

        ordered_steps.extend(reject_steps_set)

        return ordered_steps


class WorkflowStep(models.Model):
    COLOR_CHOICES = (
        ('info', 'Info'),
        ('paper', 'Paper'),
        ('secondary', 'Secondary'),
        ('secondary_light', 'Secondary_light'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('primary', 'Primary'),
        ('black', 'Black'),
    )

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='steps', verbose_name='گردش کار')
    name = models.CharField(max_length=100, verbose_name='نام مرحله')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    next_step = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='previous_step', verbose_name='مرحله بعدی')
    previous_step = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='previous_step', verbose_name='مرحله قبلی')
    reject_step = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='مرحله رد')
    step_color = models.CharField(max_length=20, default='info', choices=COLOR_CHOICES,
                                  verbose_name='رنگ دکمه تایید')
    is_first_step = models.BooleanField(default=False, verbose_name='مرحله اول')
    has_next_step = models.BooleanField(default=False, verbose_name='مرحله بعد دارد')
    has_previous_step = models.BooleanField(default=False, verbose_name='مرحله قبل دارد')
    has_reject_step = models.BooleanField(default=False, verbose_name='رد شدن دارد')

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='کاربر اختصاص یافته')
    role_assigned_to = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True,
                                         verbose_name='نقش موثر')
    progress = models.IntegerField(default=0, verbose_name='پیشرفت')

    button = models.ManyToManyField('WorkflowStepButton', verbose_name='دکمه')

    # conditions = models.TextField(blank=True, verbose_name='شرایط')
    # comments = models.TextField(blank=True, verbose_name='نظرات')
    # deadline = models.DateTimeField(null=True, blank=True, verbose_name='مهلت')
    # users = models.ManyToManyField(User, verbose_name='کاربران مرتبط با مرحله', blank=True)
    # duration = models.DurationField(null=True, blank=True, verbose_name='مدت زمان')
    # required_approvals = models.PositiveIntegerField(default=1, verbose_name='تأیید‌های مورد نیاز')
    # attachments = models.FileField(upload_to='workflow_attachments/', null=True, blank=True, verbose_name='پیوست‌ها')
    # completed = models.BooleanField(default=False, verbose_name='اتمام شده')

    class Meta:
        verbose_name = 'مرحله گردش کار'
        verbose_name_plural = 'مراحل گردش کار'

    def __str__(self):
        return self.name


class WorkflowStepButton(models.Model):
    COLOR_CHOICES = (
        ('info', 'Info'),
        ('paper', 'Paper'),
        ('secondary', 'Secondary'),
        ('secondary_light', 'Secondary_light'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('primary', 'Primary'),
        ('black', 'Black'),
    )
    ACTION_CHOICES = (
        ('next_step', 'Next Step'),
        ('previous_step', 'Previous Step'),
        ('reject_step', 'Reject Step'),
        ('view_result', 'View Result'),
        ('print_result', 'Print Result'),
        ('upload_result', 'Upload Result'),
        ('request_discount', 'Request Discount'),
    )

    action_slug = models.CharField(max_length=20, default='print_result', choices=ACTION_CHOICES,
                                   verbose_name='کد عملگر')
    title = models.CharField(max_length=100, default='نام دکمه', verbose_name='نام دکمه')
    color = models.CharField(max_length=20, default='info', choices=COLOR_CHOICES, verbose_name='رنگ دکمه')

    def __str__(self):
        return f'{self.title} ({self.color})'

    class Meta:
        verbose_name = 'دکمه مرحله گردش کار'
        verbose_name_plural = 'دکمه های مرحله گردش کار'


class Status(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='request_status',
                                verbose_name='درخواست')
    step = models.ForeignKey(WorkflowStep, on_delete=models.PROTECT, related_name='step_status')
    description = models.TextField(blank=True, verbose_name='توضیحات')

    seen = models.BooleanField(default=False, null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان مشاهده')
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='کاربر')

    complete = models.BooleanField(default=False, null=True, blank=True)
    accept = models.BooleanField(default=False, null=True, blank=True)
    reject = models.BooleanField(default=False, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به روز رسانی')

    def __str__(self):
        return f'{self.request.subject}, {self.step.name}, {self.description}'

    class Meta:
        verbose_name = 'وضعیت درخواست'
        verbose_name_plural = 'وضعیت های درخواست'
        ordering = ['created_at']

