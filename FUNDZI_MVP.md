# Fundzi MVP

Fundzi / فاندزی is the phase-1 operational core for service-based financing requests.

It supports:

- Financial service catalog
- Persian service content
- Dynamic forms per service
- Uploaded request documents
- Workflow status per service
- User request tracking
- Custom Next.js admin review panel
- Internal notes and request history
- Service/form/workflow management
- User management
- Financial partner management

Phase 1 intentionally does not include wallet, payment, escrow, contract automation, digital signature, investor marketplace, matching engine, full vendor portal, or push notifications.

## Run

```bash
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_fundzi
./venv/bin/python manage.py runserver
```

Open:

- User pages: `http://127.0.0.1:8000/fundzi/`
- Login: `http://127.0.0.1:8000/accounts/login/`
- Admin: `http://127.0.0.1:8000/admin/`
- API: `http://127.0.0.1:8000/api/fundzi/services/`

Create a demo user/admin with Django management commands if needed:

```bash
./venv/bin/python manage.py createsuperuser
```

## Seed Data

The seed command creates two active services:

- `gold-backed-financing`: تأمین مالی با پشتوانه طلا
- `property-backed-financing`: تأمین مالی با وثیقه ملکی

It also creates:

- Service descriptions and content blocks
- Dynamic form fields
- Service workflows
- Configurable validation rules

The command is idempotent:

```bash
./venv/bin/python manage.py seed_fundzi
```

## User Flow

1. Go to `/fundzi/`.
2. Open a service.
3. Read the service content.
4. Click `شروع درخواست`.
5. Log in if required.
6. Fill the dynamic form.
7. Upload documents in file fields.
8. Submit the request.
9. Open `/fundzi/requests/` to track status.
10. Open request detail to see submitted values and history.

Each request receives a tracking code like:

```text
FNDZ-YYYYMMDD-XXXX
```

## Admin Flow

Use the custom Next.js admin panel at:

```text
http://127.0.0.1:3000/admin
```

Admin can manage:

- Financial services
- Service content
- Dynamic forms and fields
- Workflows and workflow steps
- Financing requests
- Submitted field values
- Uploaded documents
- Internal notes
- Request history
- Financial partners
- Users and roles

Django Admin at `/admin/` is still available as a lower-level fallback, but daily Fundzi admin operations are now covered in the Next.js panel.

To change a request status in the custom admin panel:

1. Open `/admin/requests`.
2. Open a request detail page.
3. Choose a workflow step.
4. Add an optional note.
5. Save.
6. A `RequestHistory` row is created.

Internal notes, assignee changes, archive/unarchive, and admin attachments are also available on the request detail page.

## API

Available endpoints:

```text
GET  /api/fundzi/services/
GET  /api/fundzi/services/<slug>/
GET  /api/fundzi/services/<slug>/form/
POST /api/fundzi/services/<slug>/requests/
GET  /api/fundzi/requests/
GET  /api/fundzi/requests/<id>/
GET  /api/fundzi/requests/<id>/history/
GET  /api/fundzi/admin/stats/
GET  /api/fundzi/admin/requests/
GET  /api/fundzi/admin/requests/<id>/
POST /api/fundzi/admin/requests/<id>/status/
POST /api/fundzi/admin/requests/<id>/notes/
POST /api/fundzi/admin/requests/<id>/assign/
POST /api/fundzi/admin/requests/<id>/archive/
POST /api/fundzi/admin/services/
GET  /api/fundzi/admin/services/
GET  /api/fundzi/admin/users/
GET  /api/fundzi/admin/partners/
```

Request submission requires login.

Admin status updates require a staff user.

## Adding A New Service

In the custom admin panel:

1. Open `/admin/services`.
2. Create a service.
3. Add `ServiceContent` blocks.
4. Configure the dynamic form and ordered fields.
5. Configure the workflow and ordered steps.
6. Mark exactly one initial step.
7. Put configurable rules in `rules_config` if the service has validations.

The user-facing pages render forms from `FormField`, so new services do not require new templates.

## Validation

Gold-backed financing validates:

- `gold_weight_grams > 0`
- `requested_amount > 0`
- `desired_duration_months` is allowed by config
- Required fields are present

Property-backed financing validates:

- `estimated_property_value > 0`
- `requested_amount > 0`
- City equals configured `accepted_city`
- District is in configured `accepted_districts`
- Requested amount does not exceed `max_ltv_percent`
- Duration is in `accepted_durations_months`
- Required fields are present

Rules are stored on `FinancialService.rules_config`.

## Tests

Run:

```bash
./venv/bin/python manage.py test apps.fundzi
```

The MVP tests cover:

- Active service list
- Service detail content
- Dynamic form schema
- Gold request submission
- Property request submission
- LTV validation
- District validation
- Tracking code generation
- Initial workflow status
- User request ownership
- File upload storage
- Admin status change
- Request history
- Internal notes
- User page rendering
