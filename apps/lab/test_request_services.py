
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.lab.models import Request, Experiment, Parameter, GrantRequest, GrantRequestTransaction
from apps.lab.services.request_service import RequestService
from apps.lab.services.workflow_service import WorkflowService
from apps.lab.services.labsnet_service import LabsnetService
from apps.lab.services.credit_service import CreditService

User = get_user_model()

@pytest.mark.django_db
def test_calculate_price_for_parent_request(django_user_model):
    user = django_user_model.objects.create(username='+989123456789')
    parent_request = Request.objects.create(owner=user)
    child1 = Request.objects.create(owner=user, parent_request=parent_request, price=100000)
    child2 = Request.objects.create(owner=user, parent_request=parent_request, price=150000)

    service = RequestService(parent_request)
    service.calculate_price()

    assert parent_request.price == 250000

@pytest.mark.django_db
def test_change_status_next_step(status_factory, request_factory):
    request = request_factory()
    status_factory(request=request, step__is_first_step=True)

    WorkflowService(request).change_status('next', 'test progress', request.owner)
    assert request.request_status.count() == 2

@pytest.mark.django_db
def test_labsnet_create_sets_status(request_factory):
    request = request_factory(labsnet_status=1)
    result = LabsnetService(request).create()
    assert result.labsnet_status in [2, 3]

@pytest.mark.django_db
def test_apply_labsnet_credits_returns_discount(labsnet_credit_factory, request_factory):
    request = request_factory(price=Decimal('100000'))
    credit = labsnet_credit_factory(user=request.owner, percent='50', remain='50000')

    request.labsnet1 = credit
    discount = CreditService(request).apply_labsnet_credits()
    assert discount <= Decimal('50000')

@pytest.mark.django_db
def test_apply_grant_creates_transaction(grant_request_factory, request_factory):
    grant = grant_request_factory(remaining_amount=100000)
    request = request_factory(price=50000)
    request.grant_request1 = grant

    CreditService(request).apply_grant_requests()
    assert GrantRequestTransaction.objects.filter(request=request).count() == 1

@pytest.mark.django_db
def test_revoke_grant_usage_creates_revoke_transaction(grant_request_factory, request_factory):
    grant = grant_request_factory(remaining_amount=100000)
    request = request_factory(price=50000)
    request.grant_request1 = grant

    CreditService(request).apply_grant_requests()
    CreditService(request).revoke_grant_usage()

    txs = GrantRequestTransaction.objects.filter(request=request)
    assert txs.count() == 2  # One for use, one for revoke
    assert set(t.transaction_type for t in txs) == {'use', 'revoke'}
