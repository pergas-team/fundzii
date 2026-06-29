import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.fundzi.models import FinancialService, FinancingRequest, InternalNote, Notification, WorkflowStep


class FundziAPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_fundzi')
        cls.user = User.objects.create_user(username='09120000000', password='pass')
        cls.other_user = User.objects.create_user(username='09121111111', password='pass')
        cls.admin = User.objects.create_user(username='admin', password='pass', is_staff=True)

    def test_service_list_loads_active_services(self):
        response = self.client.get(reverse('fundzi-service-list'))

        self.assertEqual(response.status_code, 200)
        slugs = [item['slug'] for item in response.json()['results']]
        self.assertIn('gold-backed-financing', slugs)
        self.assertIn('property-backed-financing', slugs)

    def test_service_detail_returns_content(self):
        response = self.client.get(reverse('fundzi-service-detail', args=['gold-backed-financing']))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['contents'])

    def test_dynamic_form_schema_returns_fields(self):
        response = self.client.get(reverse('fundzi-service-form', args=['property-backed-financing']))

        self.assertEqual(response.status_code, 200)
        keys = [field['key'] for field in response.json()['fields']]
        self.assertIn('estimated_property_value', keys)
        self.assertIn('requested_amount', keys)

    def test_user_can_submit_gold_request(self):
        self.client.login(username='09120000000', password='pass')
        response = self.client.post(
            reverse('fundzi-service-request-create', args=['gold-backed-financing']),
            data=json.dumps({
                'gold_type': 'سکه',
                'gold_weight_grams': '25',
                'requested_amount': '100000000',
                'desired_duration_months': 12,
                'city': 'تهران',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        request = FinancingRequest.objects.get(id=response.json()['id'])
        self.assertEqual(request.current_status, 'submitted')
        self.assertTrue(request.history.filter(to_status='submitted').exists())

    def test_user_can_submit_property_request(self):
        self.client.login(username='09120000000', password='pass')
        response = self.client.post(
            reverse('fundzi-service-request-create', args=['property-backed-financing']),
            data=json.dumps({
                'property_type': 'مسکونی',
                'city': 'تهران',
                'district': '2',
                'property_area_sqm': '120',
                'estimated_property_value': '10000000000',
                'requested_amount': '7000000000',
                'repayment_duration_months': 12,
                'ownership_status': 'مالک اصلی',
                'deed_status': 'سند تک‌برگ',
                'is_currently_mortgaged': False,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        values = FinancingRequest.objects.get(id=response.json()['id']).field_values
        self.assertEqual(values.get(field__key='requested_amount').value_number, Decimal('7000000000.00'))

    def test_property_ltv_validation_works(self):
        self.client.login(username='09120000000', password='pass')
        response = self.client.post(
            reverse('fundzi-service-request-create', args=['property-backed-financing']),
            data=json.dumps({
                'property_type': 'مسکونی',
                'city': 'تهران',
                'district': '1',
                'property_area_sqm': '80',
                'estimated_property_value': '1000000000',
                'requested_amount': '800000000',
                'repayment_duration_months': 12,
                'ownership_status': 'مالک اصلی',
                'deed_status': 'سند تک‌برگ',
                'is_currently_mortgaged': False,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('requested_amount', response.json()['errors'])

    def test_invalid_property_district_is_rejected(self):
        self.client.login(username='09120000000', password='pass')
        response = self.client.post(
            reverse('fundzi-service-request-create', args=['property-backed-financing']),
            data=json.dumps({
                'property_type': 'مسکونی',
                'city': 'تهران',
                'district': '5',
                'property_area_sqm': '80',
                'estimated_property_value': '1000000000',
                'requested_amount': '500000000',
                'repayment_duration_months': 12,
                'ownership_status': 'مالک اصلی',
                'deed_status': 'سند تک‌برگ',
                'is_currently_mortgaged': False,
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('district', response.json()['errors'])

    def test_request_receives_tracking_code(self):
        service = FinancialService.objects.get(slug='gold-backed-financing')
        request = FinancingRequest.objects.create(user=self.user, service=service)

        self.assertRegex(request.tracking_code, r'^FNDZ-\d{8}-[A-Z0-9]{4}$')

    def test_request_enters_initial_workflow_status(self):
        service = FinancialService.objects.get(slug='gold-backed-financing')
        request = FinancingRequest.objects.create(user=self.user, service=service)

        self.assertEqual(request.current_status, 'submitted')
        self.assertEqual(request.current_workflow_step.key, 'submitted')

    def test_user_can_list_only_own_requests(self):
        gold = FinancialService.objects.get(slug='gold-backed-financing')
        own_request = FinancingRequest.objects.create(user=self.user, service=gold)
        FinancingRequest.objects.create(user=self.other_user, service=gold)
        self.client.login(username='09120000000', password='pass')

        response = self.client.get(reverse('fundzi-request-list'))

        self.assertEqual(response.status_code, 200)
        ids = [item['id'] for item in response.json()['results']]
        self.assertEqual(ids, [own_request.id])

    def test_user_cannot_view_another_users_request(self):
        gold = FinancialService.objects.get(slug='gold-backed-financing')
        other_request = FinancingRequest.objects.create(user=self.other_user, service=gold)
        self.client.login(username='09120000000', password='pass')

        response = self.client.get(reverse('fundzi-request-detail', args=[other_request.id]))

        self.assertEqual(response.status_code, 404)

    def test_uploaded_file_is_stored_as_value_and_attachment(self):
        self.client.login(username='09120000000', password='pass')
        upload = SimpleUploadedFile('deed.txt', b'deed-content', content_type='text/plain')
        response = self.client.post(
            reverse('fundzi-service-request-create', args=['property-backed-financing']),
            data={
                'property_type': 'مسکونی',
                'city': 'تهران',
                'district': '2',
                'property_area_sqm': '120',
                'estimated_property_value': '10000000000',
                'requested_amount': '5000000000',
                'repayment_duration_months': 12,
                'ownership_status': 'مالک اصلی',
                'deed_status': 'سند تک‌برگ',
                'is_currently_mortgaged': 'false',
                'deed_document': upload,
            },
        )

        self.assertEqual(response.status_code, 201)
        request = FinancingRequest.objects.get(id=response.json()['id'])
        self.assertTrue(request.field_values.get(field__key='deed_document').file)
        self.assertTrue(request.attachments.filter(document_type='deed_document').exists())

    def test_admin_status_change_creates_history(self):
        service = FinancialService.objects.get(slug='gold-backed-financing')
        request = FinancingRequest.objects.create(user=self.user, service=service)
        next_step = WorkflowStep.objects.get(workflow=service.workflow, key='initial_review')
        self.client.login(username='admin', password='pass')

        response = self.client.post(
            reverse('fundzi-admin-request-status', args=[request.id]),
            data=json.dumps({'status': next_step.key, 'note': 'بررسی اولیه'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        request.refresh_from_db()
        self.assertEqual(request.current_status, 'initial_review')
        self.assertTrue(request.history.filter(from_status='submitted', to_status='initial_review').exists())

    def test_otp_auth_flow_returns_current_user(self):
        send_response = self.client.post(
            reverse('fundzi-auth-send-otp'),
            data=json.dumps({'phone_number': '09123334444'}),
            content_type='application/json',
        )
        verify_response = self.client.post(
            reverse('fundzi-auth-verify-otp'),
            data=json.dumps({'phone_number': '09123334444', 'otp_code': '123456'}),
            content_type='application/json',
        )
        me_response = self.client.get(reverse('fundzi-auth-me'))

        self.assertEqual(send_response.status_code, 200)
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()['user']['phone_number'], '09123334444')

    @override_settings(FUNDZI_OTP_ENABLED=True)
    def test_otp_verify_requires_code(self):
        response = self.client.post(
            reverse('fundzi-auth-verify-otp'),
            data=json.dumps({'phone_number': '09123334444'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('otp_code', response.json()['errors'])

    def test_admin_request_list_and_detail_are_connected(self):
        service = FinancialService.objects.get(slug='gold-backed-financing')
        request = FinancingRequest.objects.create(user=self.user, service=service)
        self.client.login(username='admin', password='pass')

        list_response = self.client.get(reverse('fundzi-admin-request-list'))
        detail_response = self.client.get(reverse('fundzi-admin-request-detail', args=[request.id]))

        self.assertEqual(list_response.status_code, 200)
        self.assertIn(request.id, [item['id'] for item in list_response.json()['results']])
        self.assertEqual(detail_response.status_code, 200)
        self.assertTrue(detail_response.json()['workflow_steps'])

    def test_admin_note_endpoint_creates_internal_note(self):
        service = FinancialService.objects.get(slug='gold-backed-financing')
        request = FinancingRequest.objects.create(user=self.user, service=service)
        self.client.login(username='admin', password='pass')

        response = self.client.post(
            reverse('fundzi-admin-request-note', args=[request.id]),
            data=json.dumps({'body': 'بررسی مدارک انجام شود'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(request.internal_notes.filter(body='بررسی مدارک انجام شود').exists())

    def test_admin_can_add_internal_note(self):
        service = FinancialService.objects.get(slug='gold-backed-financing')
        request = FinancingRequest.objects.create(user=self.user, service=service)

        note = InternalNote.objects.create(request=request, author=self.admin, body='نیاز به بررسی مالکیت')

        self.assertEqual(request.internal_notes.get(), note)

    def test_user_pages_render_demo_journey(self):
        self.client.login(username='09120000000', password='pass')

        list_response = self.client.get(reverse('fundzi-home'))
        detail_response = self.client.get(reverse('fundzi-service-page', args=['gold-backed-financing']))
        form_response = self.client.get(reverse('fundzi-request-create-page', args=['gold-backed-financing']))
        dashboard_response = self.client.get(reverse('fundzi-dashboard-page'))

        self.assertContains(list_response, 'تأمین مالی با پشتوانه طلا')
        self.assertContains(detail_response, 'شروع درخواست')
        self.assertContains(form_response, 'gold_weight_grams')
        self.assertEqual(dashboard_response.status_code, 200)


class FundziNotificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_fundzi')
        cls.user = User.objects.create_user(username='09120000000', password='pass')
        cls.admin = User.objects.create_user(username='admin', password='pass', is_staff=True)

    def _submit_request(self):
        self.client.login(username='09120000000', password='pass')
        response = self.client.post(
            reverse('fundzi-service-request-create', args=['gold-backed-financing']),
            data=json.dumps({
                'gold_type': 'سکه',
                'gold_weight_grams': '25',
                'requested_amount': '100000000',
                'desired_duration_months': 12,
                'city': 'تهران',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        return FinancingRequest.objects.get(id=response.json()['id'])

    def test_submission_creates_in_app_notification(self):
        request = self._submit_request()
        notifications = Notification.objects.filter(user=self.user, channel='in_app')
        self.assertEqual(notifications.count(), 1)
        notification = notifications.get()
        self.assertEqual(notification.kind, 'request_submitted')
        self.assertIn(request.tracking_code, notification.body)
        self.assertFalse(notification.is_read)

    def test_status_change_creates_localized_notification(self):
        request = self._submit_request()
        step = WorkflowStep.objects.get(workflow=request.service.workflow, key='approved')
        request.change_status(step, changed_by=self.admin)

        notification = Notification.objects.filter(
            user=self.user, channel='in_app', kind='status_changed'
        ).latest('created_at')
        self.assertIn('تأیید شده', notification.body)

    def test_notification_list_and_unread_count(self):
        self._submit_request()
        response = self.client.get(reverse('fundzi-notification-list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['unread_count'], 1)

    def test_mark_notification_read(self):
        self._submit_request()
        notification = Notification.objects.filter(user=self.user, channel='in_app').get()
        response = self.client.post(reverse('fundzi-notification-read', args=[notification.id]))
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_read(self):
        request = self._submit_request()
        step = WorkflowStep.objects.get(workflow=request.service.workflow, key='initial_review')
        request.change_status(step, changed_by=self.admin)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 2)

        response = self.client.post(reverse('fundzi-notification-read-all'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_user_cannot_read_other_users_notification(self):
        self._submit_request()
        notification = Notification.objects.filter(user=self.user, channel='in_app').get()
        self.client.logout()
        self.client.login(username='admin', password='pass')
        response = self.client.post(reverse('fundzi-notification-read', args=[notification.id]))
        self.assertEqual(response.status_code, 404)

    def test_notifications_require_login(self):
        response = self.client.get(reverse('fundzi-notification-list'))
        self.assertEqual(response.status_code, 401)


class HealthCheckTests(TestCase):
    def test_health_endpoint_returns_200_with_db_ok(self):
        response = self.client.get(reverse('fundzi-health'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(data['db'])
