import re
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.fundzi.models import (
    FinancingRequest,
    FormField,
    RequestAttachment,
    RequestFieldValue,
    RequestHistory,
    decimal_from_payload,
)


def normalize_option(value):
    if isinstance(value, dict):
        return value.get('value') or value.get('key') or value.get('label')
    return value


def field_value(payload, key):
    return payload.get(key)


def validate_required_fields(service, payload, files=None):
    files = files or {}
    missing = {}
    form = getattr(service, 'form', None)
    if not form:
        raise ValidationError({'form': 'برای این سرویس فرم فعال تعریف نشده است.'})

    for field in form.fields.filter(is_active=True, required=True):
        value = payload.get(field.key)
        has_file = field.key in files
        if field.field_type == 'file':
            if not has_file and value in (None, '', []):
                missing[field.key] = 'این فیلد الزامی است.'
        elif value in (None, '', []):
            missing[field.key] = 'این فیلد الزامی است.'
    if missing:
        raise ValidationError(missing)


def validate_select_fields(service, payload):
    errors = {}
    for field in service.form.fields.filter(is_active=True, field_type__in=['select', 'multi_select']):
        value = payload.get(field.key)
        if value in (None, ''):
            continue
        allowed = [normalize_option(option) for option in field.options]
        allowed_as_text = [str(option) for option in allowed]
        values = value if isinstance(value, list) else [value]
        invalid = [item for item in values if item not in allowed and str(item) not in allowed_as_text]
        if invalid:
            errors[field.key] = 'گزینه انتخاب‌شده معتبر نیست.'
    if errors:
        raise ValidationError(errors)


def validate_gold_request(service, payload):
    errors = {}
    weight = decimal_from_payload(field_value(payload, 'gold_weight_grams'))
    requested_amount = decimal_from_payload(field_value(payload, 'requested_amount'))
    duration = field_value(payload, 'desired_duration_months')
    allowed_durations = service.rules_config.get('accepted_durations_months') or service.rules_config.get('allowed_durations_months')

    if weight is not None and weight <= 0:
        errors['gold_weight_grams'] = 'وزن طلا باید بزرگ‌تر از صفر باشد.'
    if requested_amount is not None and requested_amount <= 0:
        errors['requested_amount'] = 'مبلغ درخواستی باید بزرگ‌تر از صفر باشد.'
    if allowed_durations and duration not in allowed_durations and str(duration) not in [str(item) for item in allowed_durations]:
        errors['desired_duration_months'] = 'مدت زمان انتخاب‌شده مجاز نیست.'
    if errors:
        raise ValidationError(errors)


def validate_property_request(service, payload):
    errors = {}
    rules = service.rules_config or {}
    city = field_value(payload, 'city')
    district = field_value(payload, 'district')
    requested_amount = decimal_from_payload(field_value(payload, 'requested_amount'))
    property_value = decimal_from_payload(field_value(payload, 'estimated_property_value'))

    accepted_city = rules.get('accepted_city')
    if accepted_city and city != accepted_city:
        errors['city'] = f'در حال حاضر فقط شهر {accepted_city} پذیرفته می‌شود.'

    accepted_districts = rules.get('accepted_districts') or []
    if accepted_districts and str(district) not in [str(item) for item in accepted_districts]:
        errors['district'] = 'منطقه انتخاب‌شده برای این سرویس پذیرفته نیست.'

    max_ltv = rules.get('max_ltv_percent')
    if property_value is not None and property_value <= 0:
        errors['estimated_property_value'] = 'ارزش ملک باید بزرگ‌تر از صفر باشد.'
    if requested_amount is not None and requested_amount <= 0:
        errors['requested_amount'] = 'مبلغ درخواستی باید بزرگ‌تر از صفر باشد.'
    if max_ltv is not None and requested_amount is not None and property_value is not None:
        max_amount = property_value * Decimal(str(max_ltv)) / Decimal('100')
        if requested_amount > max_amount:
            errors['requested_amount'] = f'مبلغ درخواستی نباید بیش از {max_ltv}٪ ارزش ملک باشد.'

    accepted_durations = rules.get('accepted_durations_months') or []
    duration = field_value(payload, 'repayment_duration_months')
    if accepted_durations and duration not in accepted_durations and str(duration) not in [str(item) for item in accepted_durations]:
        errors['repayment_duration_months'] = 'مدت بازپرداخت انتخاب‌شده مجاز نیست.'

    if errors:
        raise ValidationError(errors)


def validate_field_constraints(service, payload):
    """Enforce each field's ``validation_config`` rules built in the admin
    form builder (numeric bounds, text length/pattern, selection counts)."""
    errors = {}
    form = getattr(service, 'form', None)
    if not form:
        return
    for field in form.fields.filter(is_active=True):
        rules = field.validation_config or {}
        if not rules:
            continue
        value = payload.get(field.key)
        if value in (None, '', []):
            continue  # presence is handled by validate_required_fields

        field_type = field.field_type
        if field_type in ('number', 'money', 'percentage'):
            number = decimal_from_payload(value)
            if number is None:
                continue
            if 'min' in rules and number < Decimal(str(rules['min'])):
                errors[field.key] = f"مقدار نباید کمتر از {rules['min']} باشد."
            elif 'max' in rules and number > Decimal(str(rules['max'])):
                errors[field.key] = f"مقدار نباید بیشتر از {rules['max']} باشد."
            elif rules.get('integer') and number != number.to_integral_value():
                errors[field.key] = 'مقدار باید عدد صحیح باشد.'
        elif field_type in ('text', 'textarea'):
            text = str(value)
            if 'min_length' in rules and len(text) < int(rules['min_length']):
                errors[field.key] = f"حداقل {rules['min_length']} نویسه لازم است."
            elif 'max_length' in rules and len(text) > int(rules['max_length']):
                errors[field.key] = f"حداکثر {rules['max_length']} نویسه مجاز است."
            elif rules.get('pattern'):
                try:
                    if not re.search(str(rules['pattern']), text):
                        errors[field.key] = rules.get('pattern_message') or 'قالب واردشده معتبر نیست.'
                except re.error:
                    pass
        elif field_type == 'multi_select':
            values = value if isinstance(value, list) else [value]
            if 'min_selections' in rules and len(values) < int(rules['min_selections']):
                errors[field.key] = f"حداقل {rules['min_selections']} گزینه را انتخاب کنید."
            elif 'max_selections' in rules and len(values) > int(rules['max_selections']):
                errors[field.key] = f"حداکثر {rules['max_selections']} گزینه مجاز است."
    if errors:
        raise ValidationError(errors)


def validate_request_payload(service, payload, files=None):
    validate_required_fields(service, payload, files)
    validate_select_fields(service, payload)
    validate_field_constraints(service, payload)
    if service.service_type == 'gold_backed':
        validate_gold_request(service, payload)
    elif service.service_type == 'property_backed':
        validate_property_request(service, payload)


def serialize_value(field, value, file_obj=None):
    data = {
        'field': field,
        'value_text': '',
        'value_number': None,
        'value_json': None,
        'file': file_obj,
    }
    if field.field_type in ['number', 'money', 'percentage']:
        data['value_number'] = decimal_from_payload(value)
    elif field.field_type in ['multi_select', 'boolean']:
        data['value_json'] = value
    elif field.field_type == 'file':
        data['value_text'] = value or ''
    else:
        data['value_text'] = '' if value is None else str(value)
    return data


@transaction.atomic
def create_financing_request(service, user, payload, files=None):
    files = files or {}
    validate_request_payload(service, payload, files)
    first_step = service.first_workflow_step()
    if not first_step:
        raise ValidationError({'workflow': 'برای این سرویس مرحله ابتدایی گردش کار تعریف نشده است.'})

    request = FinancingRequest.objects.create(
        user=user,
        service=service,
        current_workflow_step=first_step,
        current_status=first_step.key,
        metadata={'source': 'api'},
    )
    RequestHistory.objects.create(
        request=request,
        from_status=None,
        to_status=first_step.key,
        changed_by=user,
        note='ثبت درخواست',
    )

    fields = FormField.objects.filter(form=service.form, is_active=True)
    for field in fields:
        file_obj = files.get(field.key)
        raw_value = payload.get(field.key)
        value_data = serialize_value(field, raw_value, file_obj)
        RequestFieldValue.objects.create(request=request, **value_data)
        if file_obj:
            RequestAttachment.objects.create(
                request=request,
                file=file_obj,
                document_type=field.key,
                title=field.label,
                uploaded_by=user,
            )
    return request
