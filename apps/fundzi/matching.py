from decimal import Decimal, InvalidOperation


def run(financing_request):
    """Match a FinancingRequest against all active MatchingRules.

    Creates or updates MatchResult records and returns the list of matches.
    """
    from apps.fundzi.models import MatchingRule, MatchResult

    rules = MatchingRule.objects.filter(is_active=True).select_related('partner')
    amount = _get_request_amount(financing_request)
    results = []

    for rule in rules:
        if not rule.partner.is_active:
            continue
        score = _evaluate(rule, financing_request, amount)
        if score > 0:
            match, _ = MatchResult.objects.update_or_create(
                request=financing_request,
                partner=rule.partner,
                defaults={'score': score, 'status': 'matched'},
            )
            results.append(match)

    return results


def _get_request_amount(financing_request):
    fv = financing_request.field_values.filter(
        field__key__in=['amount', 'loan_amount', 'financing_amount', 'property_value']
    ).first()
    if fv and fv.value:
        try:
            return Decimal(str(fv.value))
        except (InvalidOperation, TypeError):
            pass
    return None


def _evaluate(rule, financing_request, amount):
    """Return a positive score when the rule matches, 0 when it does not."""
    cond = rule.conditions
    score = rule.priority

    if 'service_slug' in cond:
        if financing_request.service.slug != cond['service_slug']:
            return 0
        score += 10

    if amount is not None:
        min_a = cond.get('min_amount')
        max_a = cond.get('max_amount')
        try:
            if min_a is not None and amount < Decimal(str(min_a)):
                return 0
            if max_a is not None and amount > Decimal(str(max_a)):
                return 0
        except (InvalidOperation, TypeError):
            pass
        if min_a is not None or max_a is not None:
            score += 20

    # A rule with no conditions is a catch-all; give it a base score of 1.
    if score == 0:
        score = 1

    return score
