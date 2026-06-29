from django.core.management.base import BaseCommand
from django.db import transaction

from apps.fundzi.models import DynamicForm, FinancialService, FormField, ServiceContent, Workflow, WorkflowStep


# Persian titles for workflow steps. Keys stay English; only the display title is localized.
# Kept in sync with interface/lib/utils/statusLabels.ts
WORKFLOW_STEP_LABELS = {
    'submitted': 'ثبت شده',
    'initial_review': 'در حال بررسی اولیه',
    'information_review': 'بررسی اطلاعات',
    'property_document_review': 'بررسی مدارک ملک',
    'property_location_check': 'بررسی موقعیت ملک',
    'property_valuation': 'ارزیابی ملک',
    'legal_review': 'بررسی حقوقی',
    'valuation_required': 'نیازمند ارزیابی',
    'offer_preparation': 'آماده‌سازی پیشنهاد',
    'offer_sent': 'پیشنهاد ارسال شده',
    'approved': 'تأیید شده',
    'rejected': 'رد شده',
    'needs_more_information': 'نیاز به تکمیل اطلاعات',
    # P2P steps
    'identity_verification': 'احراز هویت',
    'collateral_review': 'بررسی تضامین',
    'matching': 'در حال تطبیق',
    'matched': 'تطبیق یافته',
    'contract_signing': 'در انتظار امضای قرارداد',
    'active': 'فعال',
    'completed': 'تکمیل شده',
    'cancelled': 'لغو شده',
}


PRIVATE_INVESTMENT_FIELDS = [
    # ── اطلاعات شخصی ──────────────────────────────────────────────────────────
    ('full_name',               'نام و نام خانوادگی',                          'text',         True,  []),
    ('national_id',             'کد ملی',                                       'text',         True,  []),
    ('phone',                   'شماره تماس',                                   'text',         True,  []),
    # ── جزئیات سرمایه‌گذاری ───────────────────────────────────────────────────
    ('investment_amount',       'مبلغ سرمایه‌گذاری (تومان)',                   'money',        True,  []),
    ('payment_schedule',        'نحوه پرداخت مبلغ به گیرنده',                 'select',       True,  ['یکجا', 'اقساط ماهانه', 'اقساط فصلی']),
    ('duration_months',         'مدت زمان سرمایه‌گذاری (ماه)',                 'select',       True,  [6, 10, 12, 18, 24, 36]),
    ('min_return_rate',         'حداقل نرخ سود مورد انتظار (درصد سالانه)',     'percentage',   True,  []),
    ('max_return_rate',         'حداکثر نرخ سود قابل پذیرش (درصد سالانه)',     'percentage',   True,  []),
    ('return_payment_type',     'نحوه دریافت سود',                             'select',       True,  ['ماهانه', 'فصلی', 'نیمسالانه', 'یکجا در پایان دوره']),
    ('investment_sector',       'حوزه مورد علاقه برای سرمایه‌گذاری',          'multi_select', False, ['صنعت و تولید', 'مسکن و ساختمان', 'تجارت و بازرگانی', 'فناوری', 'خدمات', 'کشاورزی', 'سایر']),
    # ── تضامین مورد نیاز ──────────────────────────────────────────────────────
    ('required_collateral_types', 'نوع تضامین مورد نیاز',                     'multi_select', True,  ['سند ملکی', 'طلا و جواهر', 'سهام بورسی', 'ضامن معتبر', 'سفته', 'چک', 'سایر']),
    ('min_collateral_ratio',    'حداقل نسبت پوشش تضمین به سرمایه (درصد)',     'percentage',   True,  []),
    ('collateral_notes',        'توضیحات تضامین',                              'textarea',     False, []),
    # ── ریسک و شرایط قرارداد ──────────────────────────────────────────────────
    ('risk_tolerance',          'سطح پذیرش ریسک',                             'select',       True,  ['ریسک پایین', 'ریسک متوسط', 'ریسک بالا']),
    ('contract_type',           'نوع قرارداد مورد نظر',                        'select',       True,  ['مشارکت', 'قرض‌الحسنه', 'مضاربه', 'فروش اقساطی']),
    ('geographic_preference',   'محدوده جغرافیایی گیرنده',                    'select',       False, ['تهران', 'کلانشهرها', 'سراسر کشور', 'بدون محدودیت']),
    ('additional_conditions',   'شرایط و توضیحات تکمیلی',                     'textarea',     False, []),
]

PRIVATE_FINANCING_FIELDS = [
    # ── اطلاعات شخصی ──────────────────────────────────────────────────────────
    ('full_name',               'نام و نام خانوادگی',                          'text',         True,  []),
    ('national_id',             'کد ملی',                                       'text',         True,  []),
    ('phone',                   'شماره تماس',                                   'text',         True,  []),
    # ── درخواست تامین مالی ────────────────────────────────────────────────────
    ('requested_amount',        'مبلغ مورد نیاز (تومان)',                      'money',        True,  []),
    ('duration_months',         'مدت بازپرداخت (ماه)',                          'select',       True,  [6, 10, 12, 18, 24, 36]),
    ('repayment_schedule',      'برنامه بازپرداخت',                            'select',       True,  ['ماهانه', 'فصلی', 'نیمسالانه', 'یکجا در سررسید']),
    ('max_acceptable_rate',     'حداکثر نرخ سود قابل قبول (درصد سالانه)',      'percentage',   True,  []),
    # ── هدف از تامین مالی ─────────────────────────────────────────────────────
    ('financing_purpose',       'هدف از تامین مالی',                           'select',       True,  ['توسعه کسب‌وکار', 'خرید تجهیزات', 'تامین سرمایه در گردش', 'خرید ملک یا زمین', 'هزینه‌های شخصی', 'سایر']),
    ('financing_purpose_description', 'شرح کامل هدف',                         'textarea',     True,  []),
    # ── تضامین قابل ارائه ─────────────────────────────────────────────────────
    ('offered_collateral_types', 'نوع تضامین قابل ارائه',                     'multi_select', True,  ['سند ملکی', 'طلا و جواهر', 'سهام بورسی', 'ضامن معتبر', 'سفته', 'چک', 'سایر']),
    ('collateral_description',  'شرح تضامین',                                  'textarea',     True,  []),
    ('collateral_estimated_value', 'ارزش تخمینی تضامین (تومان)',               'money',        True,  []),
    ('collateral_documents',    'مدارک تضامین (عکس / اسکن)',                   'file',         False, []),
    # ── وضعیت مالی متقاضی ─────────────────────────────────────────────────────
    ('monthly_income',          'درآمد ماهانه تقریبی (تومان)',                 'money',        True,  []),
    ('employment_status',       'وضعیت شغلی',                                  'select',       True,  ['کارمند دولت', 'کارمند بخش خصوصی', 'کارآفرین / صاحب کسب‌وکار', 'آزادکار', 'سایر']),
    ('has_active_loans',        'آیا وام یا تسهیلات فعال دارید؟',              'boolean',      True,  []),
    ('credit_history',          'سابقه اعتباری',                               'select',       True,  ['عالی — بدون چک برگشتی', 'خوب — یک مورد تسویه‌شده', 'متوسط', 'ضعیف']),
    # ── ترجیحات قرارداد ──────────────────────────────────────────────────────
    ('preferred_contract_type', 'نوع قرارداد مورد نظر',                        'select',       True,  ['مشارکت', 'قرض', 'مضاربه', 'فروش اقساطی']),
    ('guarantor_available',     'امکان معرفی ضامن وجود دارد؟',                 'boolean',      True,  []),
    ('additional_info',         'اطلاعات تکمیلی',                              'textarea',     False, []),
]

GOLD_FIELDS = [
    ('gold_type', 'نوع طلا', 'select', True, ['آب‌شده', 'سکه', 'شمش', 'مصنوعات']),
    ('gold_weight_grams', 'وزن طلا به گرم', 'number', True, []),
    ('estimated_gold_value', 'ارزش تقریبی طلا', 'money', False, []),
    ('requested_amount', 'مبلغ درخواستی', 'money', True, []),
    ('desired_duration_months', 'مدت زمان مدنظر', 'select', True, [3, 6, 12, 18, 24]),
    ('ownership_document', 'مدرک مالکیت', 'file', False, []),
    ('city', 'شهر', 'text', True, []),
    ('description', 'توضیحات', 'textarea', False, []),
]

PROPERTY_FIELDS = [
    ('property_type', 'نوع ملک', 'select', True, ['مسکونی', 'اداری', 'تجاری']),
    ('city', 'شهر', 'text', True, []),
    ('district', 'منطقه', 'select', True, ['1', '2', '3']),
    ('approximate_address', 'آدرس تقریبی', 'textarea', False, []),
    ('property_area_sqm', 'متراژ ملک', 'number', True, []),
    ('estimated_property_value', 'ارزش تقریبی ملک', 'money', True, []),
    ('requested_amount', 'مبلغ درخواستی', 'money', True, []),
    ('repayment_duration_months', 'مدت بازپرداخت', 'select', True, [12, 24]),
    ('ownership_status', 'وضعیت مالکیت', 'select', True, ['مالک اصلی', 'وکالتی', 'شراکتی', 'سایر']),
    ('deed_status', 'وضعیت سند', 'select', True, ['سند تک‌برگ', 'سند دفترچه‌ای', 'قولنامه‌ای', 'سایر']),
    ('is_currently_mortgaged', 'در رهن است؟', 'boolean', True, []),
    ('deed_document', 'تصویر سند', 'file', False, []),
    ('description', 'توضیحات', 'textarea', False, []),
]


class Command(BaseCommand):
    help = 'Seed phase-1 Fundzi financial services, forms, rules, and workflows.'

    @transaction.atomic
    def handle(self, *args, **options):
        gold = self.seed_service(
            slug='gold-backed-financing',
            title='تأمین مالی با پشتوانه طلا',
            short_description='ثبت درخواست تأمین مالی بر اساس دارایی طلای کاربر.',
            full_description='کاربر نوع، وزن و ارزش تقریبی طلای خود را اعلام می‌کند و مبلغ تأمین مالی موردنیاز را ثبت می‌کند.',
            service_type='gold_backed',
            order=1,
            rules_config={'accepted_durations_months': [3, 6, 12, 18, 24]},
            fields=GOLD_FIELDS,
            workflow_steps=[
                'submitted',
                'initial_review',
                'information_review',
                'valuation_required',
                'offer_preparation',
                'offer_sent',
                'approved',
                'rejected',
                'needs_more_information',
            ],
        )
        self.seed_content(gold, [
            ('introduction', 'معرفی', 'در این سرویس، طلا به عنوان پشتوانه اولیه برای بررسی امکان تأمین مالی اعلام می‌شود.'),
            ('conditions', 'شرایط', 'وزن طلا و مبلغ درخواستی باید معتبر باشد و بررسی نهایی توسط کارشناس انجام می‌شود.'),
            ('required_documents', 'مدارک مورد نیاز', 'در صورت وجود، مدرک مالکیت یا تصویر دارایی طلا بارگذاری شود.'),
            ('process_steps', 'فرآیند', 'ثبت درخواست، بررسی اولیه، ارزیابی، آماده‌سازی پیشنهاد و اعلام نتیجه.'),
        ])

        property_service = self.seed_service(
            slug='property-backed-financing',
            title='تأمین مالی با وثیقه ملکی',
            short_description='ثبت درخواست تأمین مالی بر اساس اطلاعات و ارزش تقریبی ملک.',
            full_description='کاربر اطلاعات ملک، وضعیت سند، ارزش تقریبی و مبلغ درخواستی را ثبت می‌کند تا امکان تأمین مالی بررسی شود.',
            service_type='property_backed',
            order=2,
            rules_config={
                'accepted_city': 'تهران',
                'accepted_districts': [1, 2, 3],
                'max_ltv_percent': 70,
                'accepted_durations_months': [12, 24],
            },
            fields=PROPERTY_FIELDS,
            workflow_steps=[
                'submitted',
                'initial_review',
                'property_document_review',
                'property_location_check',
                'property_valuation',
                'legal_review',
                'offer_preparation',
                'offer_sent',
                'approved',
                'rejected',
                'needs_more_information',
            ],
        )
        self.seed_content(property_service, [
            ('introduction', 'معرفی', 'این سرویس برای بررسی تأمین مالی با پشتوانه ملک طراحی شده است.'),
            ('conditions', 'شرایط', 'در فاز اول فقط ملک‌های تهران در مناطق ۱ تا ۳ و تا سقف ۷۰٪ ارزش ملک بررسی می‌شوند.'),
            ('required_documents', 'مدارک مورد نیاز', 'در صورت امکان تصویر سند یا مدارک مالکیت بارگذاری شود.'),
            ('warning', 'هشدار', 'ثبت اطلاعات به معنی تأیید نهایی نیست و بررسی کارشناسی الزامی است.'),
        ])

        p2p_workflow = [
            'submitted',
            'initial_review',
            'identity_verification',
            'collateral_review',
            'matching',
            'matched',
            'contract_signing',
            'active',
            'completed',
            'cancelled',
            'rejected',
            'needs_more_information',
        ]

        private_investment = self.seed_service(
            slug='private-investment',
            title='سرمایه‌گذاری خصوصی',
            short_description='اعلام آمادگی برای سرمایه‌گذاری خصوصی با تضامین و شرایط مشخص.',
            full_description=(
                'سرمایه‌گذار مبلغ، مدت، نرخ سود مورد انتظار و نوع تضامین مورد نیاز را اعلام می‌کند. '
                'پلتفرم این درخواست را با متقاضیان تامین مالی خصوصی تطبیق می‌دهد. '
                'قرارداد نهایی بدون پشتوانه دولتی و به‌صورت خصوصی بین طرفین منعقد می‌شود.'
            ),
            service_type='other',
            order=3,
            rules_config={
                'min_investment_amount': 100_000_000,
                'accepted_durations_months': [6, 10, 12, 18, 24, 36],
                'p2p': True,
                'role': 'investor',
            },
            fields=PRIVATE_INVESTMENT_FIELDS,
            workflow_steps=p2p_workflow,
        )
        self.seed_content(private_investment, [
            ('introduction', 'معرفی', (
                'در این سرویس شما به عنوان سرمایه‌گذار، شرایط سرمایه‌گذاری خود را اعلام می‌کنید. '
                'پلتفرم درخواست شما را با متقاضیان مناسب تطبیق داده و پس از احراز هویت و تأیید تضامین، قرارداد تنظیم می‌شود.'
            )),
            ('conditions', 'شرایط', (
                '• سرمایه‌گذار باید احراز هویت شود.\n'
                '• تضامین معرفی‌شده توسط متقاضی باید به نسبت اعلام‌شده ارزش‌گذاری شود.\n'
                '• تمام قراردادها دو طرفه و لازم‌الاجراست.\n'
                '• پلتفرم فاندزی نقش واسطه و تسهیل‌کننده دارد و ضامن بازپرداخت نیست.'
            )),
            ('required_documents', 'مدارک لازم برای احراز هویت', (
                '• کارت ملی\n'
                '• شناسنامه\n'
                '• در صورت نیاز: گواهی سابقه مالی'
            )),
            ('process_steps', 'مراحل فرآیند', (
                '۱. ثبت درخواست و اعلام شرایط\n'
                '۲. بررسی اولیه توسط پلتفرم\n'
                '۳. احراز هویت سرمایه‌گذار\n'
                '۴. تطبیق با متقاضی مناسب\n'
                '۵. بررسی و تأیید تضامین\n'
                '۶. امضای قرارداد دو طرفه\n'
                '۷. فعال‌سازی سرمایه‌گذاری'
            )),
            ('warning', 'هشدار مهم', (
                'سرمایه‌گذاری خصوصی دارای ریسک است. '
                'پلتفرم فاندزی ضمانت بازپرداخت اصل یا سود سرمایه را نمی‌دهد. '
                'تصمیم نهایی و مسئولیت آن بر عهده طرفین قرارداد است.'
            )),
        ])

        private_financing = self.seed_service(
            slug='private-financing',
            title='تامین مالی خصوصی',
            short_description='درخواست تامین مالی از سرمایه‌گذاران خصوصی با ارائه تضامین.',
            full_description=(
                'متقاضی مبلغ مورد نیاز، مدت بازپرداخت، حداکثر نرخ سود قابل قبول و تضامین قابل ارائه را اعلام می‌کند. '
                'پلتفرم این درخواست را با سرمایه‌گذاران خصوصی تطبیق می‌دهد. '
                'قرارداد نهایی بدون پشتوانه دولتی و به‌صورت خصوصی بین طرفین منعقد می‌شود.'
            ),
            service_type='other',
            order=4,
            rules_config={
                'min_requested_amount': 100_000_000,
                'accepted_durations_months': [6, 10, 12, 18, 24, 36],
                'p2p': True,
                'role': 'borrower',
            },
            fields=PRIVATE_FINANCING_FIELDS,
            workflow_steps=p2p_workflow,
        )
        self.seed_content(private_financing, [
            ('introduction', 'معرفی', (
                'در این سرویس شما به عنوان متقاضی، نیاز مالی خود را اعلام می‌کنید. '
                'پلتفرم پس از بررسی تضامین، شما را با سرمایه‌گذار مناسب تطبیق داده و قرارداد تنظیم می‌شود.'
            )),
            ('conditions', 'شرایط', (
                '• متقاضی باید احراز هویت شود.\n'
                '• ارزش تضامین ارائه‌شده باید متناسب با مبلغ درخواستی باشد.\n'
                '• سابقه اعتباری متقاضی بررسی می‌شود.\n'
                '• تمام قراردادها دو طرفه و لازم‌الاجراست.\n'
                '• پلتفرم فاندزی نقش واسطه و تسهیل‌کننده دارد.'
            )),
            ('required_documents', 'مدارک لازم', (
                '• کارت ملی و شناسنامه\n'
                '• مدارک تضامین (سند ملک / فاکتور طلا / گواهی سهام و...)\n'
                '• گواهی درآمد یا وضعیت شغلی\n'
                '• در صورت داشتن ضامن: مدارک ضامن'
            )),
            ('process_steps', 'مراحل فرآیند', (
                '۱. ثبت درخواست و اعلام نیاز مالی\n'
                '۲. بررسی اولیه توسط پلتفرم\n'
                '۳. احراز هویت متقاضی\n'
                '۴. بررسی و ارزیابی تضامین\n'
                '۵. تطبیق با سرمایه‌گذار مناسب\n'
                '۶. امضای قرارداد دو طرفه\n'
                '۷. دریافت تامین مالی'
            )),
            ('warning', 'هشدار مهم', (
                'ارائه اطلاعات نادرست یا تضامین غیرمعتبر تبعات قانونی دارد. '
                'پس از امضای قرارداد، بازپرداخت در موعد مقرر الزامی است.'
            )),
            ('faq', 'سؤالات متداول', (
                'آیا می‌توانم چند درخواست همزمان ثبت کنم؟\n'
                'خیر، در حال حاضر هر کاربر یک درخواست فعال می‌تواند داشته باشد.\n\n'
                'آیا نرخ سود قابل مذاکره است؟\n'
                'بله، نرخ نهایی در توافق بین طرفین تعیین می‌شود.'
            )),
        ])

        self.stdout.write(self.style.SUCCESS('Fundzi seed data is ready.'))

    def seed_service(self, slug, title, short_description, full_description, service_type, order, rules_config, fields, workflow_steps):
        service, _ = FinancialService.objects.update_or_create(
            slug=slug,
            defaults={
                'title': title,
                'short_description': short_description,
                'full_description': full_description,
                'service_type': service_type,
                'order': order,
                'is_active': True,
                'rules_config': rules_config,
            },
        )
        form, _ = DynamicForm.objects.update_or_create(
            service=service,
            defaults={'title': f'فرم {title}', 'description': short_description, 'is_active': True},
        )
        for index, (key, label, field_type, required, options) in enumerate(fields, start=1):
            FormField.objects.update_or_create(
                form=form,
                key=key,
                defaults={
                    'label': label,
                    'field_type': field_type,
                    'required': required,
                    'options': options,
                    'order': index,
                    'is_active': True,
                },
            )
        workflow, _ = Workflow.objects.update_or_create(
            service=service,
            defaults={'name': f'گردش کار {title}', 'is_active': True},
        )
        for index, key in enumerate(workflow_steps, start=1):
            WorkflowStep.objects.update_or_create(
                workflow=workflow,
                key=key,
                defaults={
                    'title': WORKFLOW_STEP_LABELS.get(key, key.replace('_', ' ')),
                    'order': index,
                    'is_initial': index == 1,
                    'is_terminal': key in ['approved', 'rejected'],
                    'is_active': True,
                },
            )
        return service

    def seed_content(self, service, contents):
        for index, (content_type, title, body) in enumerate(contents, start=1):
            ServiceContent.objects.update_or_create(
                service=service,
                content_type=content_type,
                title=title,
                defaults={'body': body, 'order': index, 'is_active': True},
            )
