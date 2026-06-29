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
}


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
