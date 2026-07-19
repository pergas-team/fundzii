"""
Seed 20 realistic P2P requests in 'matching' status
(10 for private-investment, 10 for private-financing).
'matching' means admin has verified identity + collateral and the request
is publicly visible for pairing.

Usage:
    python manage.py seed_p2p_requests
    python manage.py seed_p2p_requests --clear   # delete existing matching requests first
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.fundzi.models import (
    FinancialService,
    FinancingRequest,
    FormField,
    RequestFieldValue,
    WorkflowStep,
)

User = get_user_model()

# ── Sample data pools ─────────────────────────────────────────────────────────

INVESTMENT_SAMPLES = [
    {
        'investment_amount': 2_000_000_000,
        'payment_schedule': 'یکجا',
        'duration_months': '12',
        'min_return_rate': 30,
        'max_return_rate': 38,
        'return_payment_type': 'ماهانه',
        'investment_sector': ['صنعت و تولید', 'فناوری'],
        'required_collateral_types': ['سند ملکی', 'سهام بورسی'],
        'min_collateral_ratio': 120,
        'risk_tolerance': 'ریسک متوسط',
        'contract_type': 'مشارکت',
        'geographic_preference': 'تهران',
    },
    {
        'investment_amount': 500_000_000,
        'payment_schedule': 'اقساط ماهانه',
        'duration_months': '6',
        'min_return_rate': 28,
        'max_return_rate': 35,
        'return_payment_type': 'ماهانه',
        'investment_sector': ['تجارت و بازرگانی'],
        'required_collateral_types': ['طلا و جواهر', 'سفته'],
        'min_collateral_ratio': 100,
        'risk_tolerance': 'ریسک پایین',
        'contract_type': 'قرض‌الحسنه',
        'geographic_preference': 'بدون محدودیت',
    },
    {
        'investment_amount': 1_500_000_000,
        'payment_schedule': 'اقساط فصلی',
        'duration_months': '18',
        'min_return_rate': 25,
        'max_return_rate': 32,
        'return_payment_type': 'فصلی',
        'investment_sector': ['مسکن و ساختمان'],
        'required_collateral_types': ['سند ملکی'],
        'min_collateral_ratio': 150,
        'risk_tolerance': 'ریسک پایین',
        'contract_type': 'فروش اقساطی',
        'geographic_preference': 'کلانشهرها',
    },
    {
        'investment_amount': 3_000_000_000,
        'payment_schedule': 'یکجا',
        'duration_months': '24',
        'min_return_rate': 32,
        'max_return_rate': 42,
        'return_payment_type': 'یکجا در پایان دوره',
        'investment_sector': ['فناوری', 'خدمات'],
        'required_collateral_types': ['سهام بورسی', 'چک'],
        'min_collateral_ratio': 110,
        'risk_tolerance': 'ریسک بالا',
        'contract_type': 'مضاربه',
        'geographic_preference': 'بدون محدودیت',
    },
    {
        'investment_amount': 800_000_000,
        'payment_schedule': 'اقساط ماهانه',
        'duration_months': '10',
        'min_return_rate': 27,
        'max_return_rate': 33,
        'return_payment_type': 'ماهانه',
        'investment_sector': ['کشاورزی'],
        'required_collateral_types': ['سند ملکی', 'ضامن معتبر'],
        'min_collateral_ratio': 130,
        'risk_tolerance': 'ریسک متوسط',
        'contract_type': 'مشارکت',
        'geographic_preference': 'سراسر کشور',
    },
    {
        'investment_amount': 5_000_000_000,
        'payment_schedule': 'اقساط فصلی',
        'duration_months': '36',
        'min_return_rate': 28,
        'max_return_rate': 36,
        'return_payment_type': 'نیمسالانه',
        'investment_sector': ['صنعت و تولید', 'مسکن و ساختمان'],
        'required_collateral_types': ['سند ملکی', 'سهام بورسی', 'ضامن معتبر'],
        'min_collateral_ratio': 140,
        'risk_tolerance': 'ریسک پایین',
        'contract_type': 'فروش اقساطی',
        'geographic_preference': 'تهران',
    },
    {
        'investment_amount': 1_200_000_000,
        'payment_schedule': 'یکجا',
        'duration_months': '12',
        'min_return_rate': 33,
        'max_return_rate': 40,
        'return_payment_type': 'یکجا در پایان دوره',
        'investment_sector': ['تجارت و بازرگانی', 'خدمات'],
        'required_collateral_types': ['طلا و جواهر', 'چک'],
        'min_collateral_ratio': 100,
        'risk_tolerance': 'ریسک بالا',
        'contract_type': 'مضاربه',
        'geographic_preference': 'کلانشهرها',
    },
    {
        'investment_amount': 700_000_000,
        'payment_schedule': 'اقساط ماهانه',
        'duration_months': '6',
        'min_return_rate': 26,
        'max_return_rate': 30,
        'return_payment_type': 'ماهانه',
        'investment_sector': ['سایر'],
        'required_collateral_types': ['سفته', 'ضامن معتبر'],
        'min_collateral_ratio': 100,
        'risk_tolerance': 'ریسک متوسط',
        'contract_type': 'قرض‌الحسنه',
        'geographic_preference': 'بدون محدودیت',
    },
    {
        'investment_amount': 2_500_000_000,
        'payment_schedule': 'اقساط فصلی',
        'duration_months': '24',
        'min_return_rate': 29,
        'max_return_rate': 37,
        'return_payment_type': 'فصلی',
        'investment_sector': ['مسکن و ساختمان', 'تجارت و بازرگانی'],
        'required_collateral_types': ['سند ملکی', 'سهام بورسی'],
        'min_collateral_ratio': 120,
        'risk_tolerance': 'ریسک متوسط',
        'contract_type': 'مشارکت',
        'geographic_preference': 'تهران',
    },
    {
        'investment_amount': 4_000_000_000,
        'payment_schedule': 'یکجا',
        'duration_months': '18',
        'min_return_rate': 31,
        'max_return_rate': 39,
        'return_payment_type': 'نیمسالانه',
        'investment_sector': ['صنعت و تولید'],
        'required_collateral_types': ['سند ملکی', 'طلا و جواهر', 'سهام بورسی'],
        'min_collateral_ratio': 160,
        'risk_tolerance': 'ریسک پایین',
        'contract_type': 'فروش اقساطی',
        'geographic_preference': 'سراسر کشور',
    },
]

FINANCING_SAMPLES = [
    {
        'requested_amount': 800_000_000,
        'duration_months': '12',
        'repayment_schedule': 'ماهانه',
        'max_acceptable_rate': 35,
        'financing_purpose': 'توسعه کسب‌وکار',
        'financing_purpose_description': 'خرید تجهیزات تولیدی و توسعه خط تولید',
        'offered_collateral_types': ['سند ملکی'],
        'collateral_description': 'یک واحد آپارتمان مسکونی در تهران',
        'collateral_estimated_value': 2_500_000_000,
        'employment_status': 'کارآفرین / صاحب کسب‌وکار',
        'has_active_loans': False,
        'credit_history': 'عالی — بدون چک برگشتی',
        'preferred_contract_type': 'مشارکت',
        'guarantor_available': True,
    },
    {
        'requested_amount': 300_000_000,
        'duration_months': '6',
        'repayment_schedule': 'ماهانه',
        'max_acceptable_rate': 32,
        'financing_purpose': 'تامین سرمایه در گردش',
        'financing_purpose_description': 'تامین موجودی کالا برای فصل پیک فروش',
        'offered_collateral_types': ['طلا و جواهر', 'سفته'],
        'collateral_description': '۵۰۰ گرم طلای آب‌شده و ۳ فقره سفته',
        'collateral_estimated_value': 700_000_000,
        'employment_status': 'کارآفرین / صاحب کسب‌وکار',
        'has_active_loans': False,
        'credit_history': 'خوب — یک مورد تسویه‌شده',
        'preferred_contract_type': 'قرض',
        'guarantor_available': False,
    },
    {
        'requested_amount': 1_500_000_000,
        'duration_months': '24',
        'repayment_schedule': 'فصلی',
        'max_acceptable_rate': 30,
        'financing_purpose': 'خرید تجهیزات',
        'financing_purpose_description': 'خرید ماشین‌آلات صنعتی برای واحد تولیدی',
        'offered_collateral_types': ['سند ملکی', 'سهام بورسی'],
        'collateral_description': 'ملک تجاری ۲۵۰ متری + پرتفوی سهامی',
        'collateral_estimated_value': 4_500_000_000,
        'employment_status': 'کارآفرین / صاحب کسب‌وکار',
        'has_active_loans': False,
        'credit_history': 'عالی — بدون چک برگشتی',
        'preferred_contract_type': 'فروش اقساطی',
        'guarantor_available': True,
    },
    {
        'requested_amount': 500_000_000,
        'duration_months': '10',
        'repayment_schedule': 'ماهانه',
        'max_acceptable_rate': 38,
        'financing_purpose': 'هزینه‌های شخصی',
        'financing_purpose_description': 'خرید واحد مسکونی در شهرستان',
        'offered_collateral_types': ['ضامن معتبر', 'چک'],
        'collateral_description': 'دو ضامن کارمند دولت و ۵ فقره چک',
        'collateral_estimated_value': 800_000_000,
        'employment_status': 'کارمند دولت',
        'has_active_loans': False,
        'credit_history': 'عالی — بدون چک برگشتی',
        'preferred_contract_type': 'قرض',
        'guarantor_available': True,
    },
    {
        'requested_amount': 2_000_000_000,
        'duration_months': '18',
        'repayment_schedule': 'نیمسالانه',
        'max_acceptable_rate': 33,
        'financing_purpose': 'خرید ملک یا زمین',
        'financing_purpose_description': 'خرید زمین کشاورزی جهت احداث گلخانه',
        'offered_collateral_types': ['سند ملکی', 'ضامن معتبر'],
        'collateral_description': 'زمین مزروعی ۵ هکتاری با سند رسمی',
        'collateral_estimated_value': 5_000_000_000,
        'employment_status': 'آزادکار',
        'has_active_loans': False,
        'credit_history': 'عالی — بدون چک برگشتی',
        'preferred_contract_type': 'مشارکت',
        'guarantor_available': True,
    },
    {
        'requested_amount': 600_000_000,
        'duration_months': '12',
        'repayment_schedule': 'ماهانه',
        'max_acceptable_rate': 36,
        'financing_purpose': 'توسعه کسب‌وکار',
        'financing_purpose_description': 'راه‌اندازی شعبه جدید فروشگاه زنجیره‌ای',
        'offered_collateral_types': ['سهام بورسی', 'سفته'],
        'collateral_description': 'سبد سهامی ارزش‌گذاری‌شده + ۴ فقره سفته',
        'collateral_estimated_value': 1_200_000_000,
        'employment_status': 'کارآفرین / صاحب کسب‌وکار',
        'has_active_loans': True,
        'credit_history': 'خوب — یک مورد تسویه‌شده',
        'preferred_contract_type': 'مضاربه',
        'guarantor_available': False,
    },
    {
        'requested_amount': 400_000_000,
        'duration_months': '6',
        'repayment_schedule': 'یکجا در سررسید',
        'max_acceptable_rate': 34,
        'financing_purpose': 'سایر',
        'financing_purpose_description': 'تامین هزینه درمان و پزشکی خانواده',
        'offered_collateral_types': ['طلا و جواهر', 'ضامن معتبر'],
        'collateral_description': 'طلاجات به وزن ۳۵۰ گرم و یک ضامن معتبر',
        'collateral_estimated_value': 600_000_000,
        'employment_status': 'کارمند بخش خصوصی',
        'has_active_loans': False,
        'credit_history': 'خوب — یک مورد تسویه‌شده',
        'preferred_contract_type': 'قرض',
        'guarantor_available': True,
    },
    {
        'requested_amount': 1_000_000_000,
        'duration_months': '18',
        'repayment_schedule': 'فصلی',
        'max_acceptable_rate': 31,
        'financing_purpose': 'خرید تجهیزات',
        'financing_purpose_description': 'خرید تجهیزات آزمایشگاهی جهت دندانپزشکی',
        'offered_collateral_types': ['سند ملکی'],
        'collateral_description': 'یک واحد تجاری ۸۰ متری',
        'collateral_estimated_value': 3_000_000_000,
        'employment_status': 'آزادکار',
        'has_active_loans': False,
        'credit_history': 'عالی — بدون چک برگشتی',
        'preferred_contract_type': 'فروش اقساطی',
        'guarantor_available': False,
    },
    {
        'requested_amount': 250_000_000,
        'duration_months': '6',
        'repayment_schedule': 'ماهانه',
        'max_acceptable_rate': 40,
        'financing_purpose': 'تامین سرمایه در گردش',
        'financing_purpose_description': 'خرید مواد اولیه برای تکمیل سفارشات صادراتی',
        'offered_collateral_types': ['چک', 'سفته'],
        'collateral_description': '۶ فقره چک و ۲ فقره سفته امضاشده',
        'collateral_estimated_value': 400_000_000,
        'employment_status': 'کارآفرین / صاحب کسب‌وکار',
        'has_active_loans': False,
        'credit_history': 'متوسط',
        'preferred_contract_type': 'قرض',
        'guarantor_available': True,
    },
    {
        'requested_amount': 3_000_000_000,
        'duration_months': '36',
        'repayment_schedule': 'نیمسالانه',
        'max_acceptable_rate': 29,
        'financing_purpose': 'توسعه کسب‌وکار',
        'financing_purpose_description': 'احداث سالن تولید و خرید زمین صنعتی',
        'offered_collateral_types': ['سند ملکی', 'سهام بورسی', 'ضامن معتبر'],
        'collateral_description': 'زمین صنعتی ۱۵۰۰ متری + پرتفوی بورسی + ضامن شرکتی',
        'collateral_estimated_value': 9_000_000_000,
        'employment_status': 'کارآفرین / صاحب کسب‌وکار',
        'has_active_loans': False,
        'credit_history': 'عالی — بدون چک برگشتی',
        'preferred_contract_type': 'مشارکت',
        'guarantor_available': True,
    },
]


def _serialize_value(field, value):
    """Mirror the logic in apps/fundzi/services.py::serialize_value (no file support)."""
    if field.field_type in ('number', 'money', 'percentage'):
        from apps.fundzi.models import decimal_from_payload
        return {'value_number': decimal_from_payload(value), 'value_text': '', 'value_json': None}
    if field.field_type in ('multi_select', 'boolean'):
        return {'value_json': value, 'value_text': '', 'value_number': None}
    return {'value_text': '' if value is None else str(value), 'value_number': None, 'value_json': None}


class Command(BaseCommand):
    help = 'Seed 20 P2P requests (matching status) for private-investment and private-financing.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing matching P2P requests before seeding.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # ── Seed user ──────────────────────────────────────────────────────────
        seed_user, created = User.objects.get_or_create(
            username='p2p_seed_user',
            defaults={'first_name': 'کاربر', 'last_name': 'نمونه', 'is_active': True},
        )
        if created:
            seed_user.set_unusable_password()
            seed_user.save()
            self.stdout.write(self.style.SUCCESS('  ✓ کاربر نمونه ایجاد شد.'))

        for slug, samples, label in [
            ('private-investment', INVESTMENT_SAMPLES, 'سرمایه‌گذاری خصوصی'),
            ('private-financing', FINANCING_SAMPLES, 'تامین مالی خصوصی'),
        ]:
            try:
                service = FinancialService.objects.get(slug=slug, is_active=True)
            except FinancialService.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'  ✗ سرویس {slug} یافت نشد. ابتدا seed_fundzi را اجرا کنید.'))
                continue

            matching_step = WorkflowStep.objects.filter(
                workflow=service.workflow, key='matching'
            ).first()
            if not matching_step:
                self.stdout.write(self.style.ERROR(f'  ✗ مرحله matching برای {slug} تعریف نشده.'))
                continue

            if options['clear']:
                deleted, _ = FinancingRequest.objects.filter(
                    service=service, current_status='matching', user=seed_user
                ).delete()
                self.stdout.write(f'  ✗ {deleted} درخواست قبلی حذف شد.')

            fields_qs = FormField.objects.filter(form=service.form, is_active=True)

            created_count = 0
            for sample in samples:
                req = FinancingRequest.objects.create(
                    user=seed_user,
                    service=service,
                    current_workflow_step=matching_step,
                    current_status=matching_step.key,
                    metadata={'source': 'seed', 'p2p': True},
                )
                for field in fields_qs:
                    raw = sample.get(field.key)
                    if raw is None:
                        continue
                    vals = _serialize_value(field, raw)
                    RequestFieldValue.objects.create(request=req, field=field, file=None, **vals)
                created_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'  ✓ {created_count} درخواست نمونه برای «{label}» ثبت شد.')
            )

        self.stdout.write(self.style.SUCCESS('\nعملیات seed با موفقیت انجام شد.'))
