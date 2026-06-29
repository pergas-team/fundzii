
import pytest
from decimal import Decimal
from django.utils import timezone
from apps.lab.models import Request, GrantRequest, Parameter, Experiment, User
from apps.lab.models import GrantRequestTransaction, FormResponse

@pytest.mark.django_db
class TestRequestMethods:

    def setup_method(self):
        self.user = User.objects.create(username='+989123456789', user_type='customer', account_type='personal')
        self.experiment = Experiment.objects.create(name='Test Exp', name_en='Test', laboratory_id=1)
        self.request = Request.objects.create(owner=self.user, experiment=self.experiment)

    def test_set_price_without_params(self):
        self.request.set_price()
        assert self.request.price is not None

    def test_apply_grant_requests(self):
        grant = GrantRequest.objects.create(
            sender=self.user, receiver=self.user,
            requested_amount=1000000,
            approved_amount=1000000,
            remaining_amount=1000000,
            status='approved'
        )
        self.request.price = 500000
        self.request.grant_request1 = grant
        self.request.apply_grant_requests()

        assert self.request.price == 0
        assert self.request.grant_request_discount == 500000
        assert grant.remaining_amount == 500000

    def test_revoke_grant_usage(self):
        grant = GrantRequest.objects.create(
            sender=self.user, receiver=self.user,
            requested_amount=1000000,
            approved_amount=1000000,
            remaining_amount=1000000,
            status='approved'
        )
        self.request.price = 500000
        self.request.grant_request1 = grant
        self.request.apply_grant_requests()
        self.request.revoke_grant_usage()

        assert grant.remaining_amount == 1000000
        assert GrantRequestTransaction.objects.filter(request=self.request).count() == 2  # use + revoke

    def test_change_status_reject(self):
        self.request.set_first_step()
        self.request.change_status(action='reject', description='test reject', action_by=self.user)

        status = self.request.request_status.last()
        assert status.reject is True
        assert status.complete is True

    def test_get_latest_order_empty(self):
        assert self.request.get_latest_order() is None or self.request.get_latest_order() == []

    def test_current_month_counter(self):
        count = self.request.current_month_counter()
        assert isinstance(count, int)

    def test_owners(self):
        owners = self.request.owners()
        assert self.user in owners
