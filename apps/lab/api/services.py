import requests
import jdatetime
import math
from django.db.models import Sum
from apps.lab.models import Request, Status, GrantRequestTransaction

from django.core.exceptions import ValidationError
import datetime
from decimal import Decimal




class RequestService:
    def __init__(self, request_instance):
        self.request = request_instance

    def calculate_price(self):
        if self.request.parent_request:
            return self._calculate_child_price()
        else:
            return self._calculate_parent_price()

    def _calculate_child_price(self):
        experiment = self.request.experiment
        params = self.request.parameter.all()
        formresponses = self.request.formresponse.filter(is_main=True).aggregate(Sum('response_count'))
        price = 0

        for param in params:
            if self.request.test_duration > 0:
                temp = self.request.test_duration
            else:
                response_sum = formresponses['response_count__sum'] or 0
                temp = math.ceil(response_sum / (param.unit_value or 1))

            price += self._calculate_param_price(param, temp)

        self.request.price_wod = Decimal(price)
        self.request.price = price * (1 - self.request.discount / 100)
        self.request.price_sample_returned = Decimal(850000) if self.request.is_sample_returned else Decimal(0)
        self.request.total_prepayment_amount = experiment.prepayment_amount if experiment.need_turn else 0
        self.request.save()

        # Price propagation
        self.request.parent_request.set_price()

    def _calculate_parent_price(self):
        children = self.request.child_requests.exclude(request_status__step__name__in=['رد شده'])
        price = sum((child.price or 0) for child in children)
        prepayment = sum((child.experiment.prepayment_amount or 0) for child in children if self.request.has_prepayment)

        self.request.price = price
        self.request.price_wod = price
        self.request.total_prepayment_amount = prepayment
        self.request.price_sample_returned = Decimal(850000) if self.request.is_sample_returned else Decimal(0)
        self.request.save()

    def _calculate_param_price(self, param, temp):
        if self.request.owner.is_partner:
            return int((param.partner_urgent_price if self.request.is_urgent else param.partner_price or param.price) or 0) * temp
        else:
            return int((param.urgent_price if self.request.is_urgent else param.price) or 0) * temp


class WorkflowService:
    def __init__(self, request_instance):
        self.request = request_instance

    def change_status(self, action, description, action_by):
        lastest_status = self.request.lastest_status()

        if self.request.parent_request:
            parent_status = self.request.parent_request.lastest_status()
            if parent_status.step != lastest_status.step and lastest_status.step.name != 'در انتظار پرداخت':
                raise ValidationError('وضعیت درخواست نمیتواند بیش از یک وضعیت با فاکتور اختلاف داشته باشد.')

        if action == 'next':
            new_step = lastest_status.step.next_step
            lastest_status.accept = True
        elif action == 'previous':
            new_step = lastest_status.step.previous_step
            lastest_status.reject = True
        elif action == 'reject':
            new_step = lastest_status.step.reject_step
            lastest_status.reject = True
        else:
            raise ValidationError('عملیات نامعتبر')

        Status.objects.create(request=self.request, step=new_step)
        self.request.handle_status_changed(new_step, action, lastest_status)

        lastest_status.complete = True
        lastest_status.description = description
        lastest_status.action_by = action_by
        lastest_status.save()

        if self.request.parent_request:
            self.request.parent_request.change_parent_status(action_by)


class LabsnetService:
    def __init__(self, request_instance):
        self.request = request_instance

    def create(self):
        if self.request.labsnet_status == 2:
            return self.request

        session = requests.Session()
        user = self.request.owner
        is_personal = user.account_type == 'personal'
        national_code = user.national_id if is_personal else user.company_national_id

        data = {
            "user_name": "sharif_uni",
            "password": "sharif_uni",
            "national_code": f"{national_code}",
            "type": '1' if is_personal else '2',
            "org_id": "343",
            "name": user.first_name if is_personal else user.company_name,
            "family": user.last_name if is_personal else "",
            "mobile": user.username.replace('+98', '0'),
        }

        for i, child in enumerate(self.request.child_requests.exclude(request_status__step__name__in=['رد شده'])):
            jalali_date = jdatetime.date.today()
            date_str = f"{jalali_date.year}/{jalali_date.month:02}/{jalali_date.day:02}"

            if child.experiment.test_unit_type == 'time':
                duration = child.test_duration or 1
                unit_price = int(child.price) // duration
                data.update({
                    f"services[{i}][tariffs_basis]": 1,
                    f"services[{i}][test_count]": 1,
                    f"services[{i}][time_execute]": duration,
                    f"services[{i}][price]": unit_price,
                })
            else:
                count = child.formresponse.filter(is_main=True).aggregate(Sum('response_count'))['response_count__sum'] or 1
                unit_price = int(child.price) // count
                data.update({
                    f"services[{i}][tariffs_basis]": 2,
                    f"services[{i}][test_count]": count,
                    f"services[{i}][price]": unit_price,
                })

            data[f"services[{i}][test_code]"] = child.experiment.labsnet_experiment_id
            data[f"services[{i}][type_credit]"] = 2
            data[f"services[{i}][date]"] = date_str

        self.request.labsnet_result = f'data={str(data)}'
        try:
            response = session.post('https://labsnet.ir/api/add_service', data=data, verify=False)
            response.raise_for_status()
            res_json = response.json()
            self.request.labsnet_result += f' + res={str(res_json)} + error={res_json.get("error", "unknown")}'
            self.request.labsnet_status = 2 if res_json.get('error') == 0 else 3
        except Exception as e:
            self.request.labsnet_result += f' + exception={e}'
            self.request.labsnet_status = 3

        self.request.save()
        return self.request


class CreditService:
    def __init__(self, request_instance):
        self.request = request_instance

    def apply_labsnet_credits(self):
        today = datetime.date.today()
        original_price = Decimal(self.request.price or 0)

        def apply_credit(labsnet):
            nonlocal original_price
            if not labsnet or labsnet.end_date < today:
                return Decimal(0)

            try:
                max_discount_amount = Decimal(labsnet.remain.replace(',', ''))
                max_discount_percent = Decimal(labsnet.percent) / Decimal(100)
                max_allowed_discount = original_price * max_discount_percent
                applied_discount = min(max_allowed_discount, max_discount_amount, original_price)
                original_price -= applied_discount
                return Decimal(applied_discount)
            except:
                return Decimal(0)

        credits = []
        if self.request.parent_request:
            credits = [ln for ln in [self.request.parent_request.labsnet1, self.request.parent_request.labsnet2] if ln]
        else:
            credits = [ln for ln in [self.request.labsnet1, self.request.labsnet2] if ln]

        credits = sorted(credits, key=lambda l: int(l.labsnet_id))
        total_discount = sum(apply_credit(ln) for ln in credits)
        return total_discount

    def apply_grant_requests(self):
        start_price = self.request.price
        if self.request.grant_request1:
            self._apply_grant(self.request.grant_request1)
        if self.request.grant_request2:
            self._apply_grant(self.request.grant_request2)

        self.request.grant_request_discount = start_price - self.request.price
        self.request.save()

    def _apply_grant(self, grant_request):
        used_amount = min(grant_request.remaining_amount, self.request.price)
        grant_request.remaining_amount -= used_amount
        self.request.price -= used_amount
        grant_request.save()
        self._grant_transaction(grant_request, used_amount, 'use')

    def revoke_grant_usage(self):
        transactions = GrantRequestTransaction.objects.filter(request=self.request, transaction_type='use')
        for tx in transactions:
            tx.grant_request.remaining_amount += tx.used_amount
            tx.grant_request.save()
            self._grant_transaction(tx.grant_request, tx.used_amount, 'revoke')

    def _grant_transaction(self, grant_request, amount, tx_type):
        GrantRequestTransaction.objects.create(
            grant_request=grant_request,
            request=self.request,
            used_amount=amount,
            remaining_amount_before=grant_request.remaining_amount,
            remaining_amount_after=(
                grant_request.remaining_amount - amount
                if tx_type == 'use'
                else grant_request.remaining_amount + amount
            ),
            transaction_type=tx_type
        )
