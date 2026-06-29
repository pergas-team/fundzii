# Fundzi / فاندزی Implementation Review

This file summarizes all work done on the Fundzi MVP so another AI or engineer can review the implementation quickly and systematically.

## Project Context

Fundzi / فاندزی is a phase-1 financial services platform.

The MVP supports:

- Financial service catalog
- Service detail/content pages
- Dynamic forms per service
- File uploads
- Financing request submission
- Workflow-based request status tracking
- Request history
- Admin/operator review
- Internal notes
- RTL/Persian-ready user experience

Out of scope for phase 1:

- Wallet
- Payment
- Escrow/trust
- Contract automation
- Digital signature
- Full investor marketplace
- Full vendor portal
- Advanced matching engine
- Ticketing
- Push notifications

## High-Level Result

Two main layers were implemented/adapted:

1. Django backend Fundzi app:
   - Location: `apps/fundzi/`
   - API prefix: `/api/fundzi/`
   - User-facing Django fallback pages: `/fundzi/`

2. Next.js frontend:
   - Location: `interface/`
   - Uses Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui-style local components
   - API proxy path: `/backend/*`

## Backend Work

### New Django App

Created:

```text
apps/fundzi/
```

Key files:

```text
apps/fundzi/models.py
apps/fundzi/services.py
apps/fundzi/admin.py
apps/fundzi/api/views.py
apps/fundzi/api/urls.py
apps/fundzi/management/commands/seed_fundzi.py
apps/fundzi/migrations/0001_initial.py
apps/fundzi/tests.py
apps/fundzi/views.py
apps/fundzi/urls.py
```

### Backend Models

Implemented in `apps/fundzi/models.py`:

- `FinancialService`
- `ServiceContent`
- `DynamicForm`
- `FormField`
- `Workflow`
- `WorkflowStep`
- `FinancingRequest`
- `RequestFieldValue`
- `RequestAttachment`
- `RequestHistory`
- `InternalNote`
- `FinancialPartner`

### Service Model

`FinancialService` supports:

- `title`
- `slug`
- `short_description`
- `full_description`
- `service_type`
- `is_active`
- `order`
- `rules_config`
- `metadata`

`rules_config` stores configurable service rules, such as property LTV limits and allowed districts.

### Dynamic Form Model

`DynamicForm` and `FormField` support dynamic service-specific forms.

Supported field types:

- `text`
- `textarea`
- `number`
- `select`
- `multi_select`
- `boolean`
- `date`
- `file`
- `money`
- `percentage`

### Workflow Model

Each service can have its own:

- `Workflow`
- ordered `WorkflowStep` records
- one initial step
- terminal steps such as `approved` / `rejected`

Requests automatically start at the service workflow’s initial step.

### Request Model

`FinancingRequest` stores:

- user
- selected service
- current status
- current workflow step
- tracking code
- submitted date
- updated date
- admin assignee
- metadata
- archive flag

Tracking code format:

```text
FNDZ-YYYYMMDD-XXXX
```

### Request Values and Files

Submitted form values are stored in `RequestFieldValue`.

Uploaded files are stored in:

- `RequestFieldValue.file`
- `RequestAttachment`

This allows both field-level file display and admin attachment review.

### Business Validation

Implemented in:

```text
apps/fundzi/services.py
```

Validation is centralized and service-aware.

Gold-backed financing validation:

- `gold_weight_grams > 0`
- `requested_amount > 0`
- `desired_duration_months` must be allowed by config
- required fields must be present
- select options must be valid

Property-backed financing validation:

- `estimated_property_value > 0`
- `requested_amount > 0`
- city must match `accepted_city`
- district must be in `accepted_districts`
- requested amount must not exceed `max_ltv_percent`
- duration must be in `accepted_durations_months`
- required fields must be present

### Seed Data

Seed command:

```bash
./venv/bin/python manage.py seed_fundzi
```

Creates two services:

1. Gold-backed financing
   - Slug: `gold-backed-financing`
   - Persian title: `تأمین مالی با پشتوانه طلا`

2. Property-backed financing
   - Slug: `property-backed-financing`
   - Persian title: `تأمین مالی با وثیقه ملکی`

Seed includes:

- service descriptions
- content blocks
- dynamic form fields
- workflow steps
- rules config

### Backend API Endpoints

Implemented under:

```text
/api/fundzi/
```

Auth:

```text
POST /api/fundzi/auth/send-otp/
POST /api/fundzi/auth/verify-otp/
POST /api/fundzi/auth/login/
GET  /api/fundzi/auth/me/
POST /api/fundzi/auth/logout/
```

Services:

```text
GET /api/fundzi/services/
GET /api/fundzi/services/<slug>/
GET /api/fundzi/services/<slug>/form/
```

User requests:

```text
POST /api/fundzi/services/<slug>/requests/
GET  /api/fundzi/requests/
GET  /api/fundzi/requests/<id>/
GET  /api/fundzi/requests/<id>/history/
```

Admin/operator:

```text
GET   /api/fundzi/admin/requests/
GET   /api/fundzi/admin/requests/<id>/
POST  /api/fundzi/admin/requests/<id>/status/
PATCH /api/fundzi/admin/requests/<id>/status/
POST  /api/fundzi/admin/requests/<id>/notes/
```

### Admin Panel Completion Update

The custom Next.js admin panel was completed beyond the original MVP scope. It no longer relies on placeholder pages that point admins to Django Admin for day-to-day Fundzi operations.

New/expanded admin backend endpoints:

```text
GET    /api/fundzi/admin/stats/

GET    /api/fundzi/admin/requests/
GET    /api/fundzi/admin/requests/<id>/
POST   /api/fundzi/admin/requests/<id>/status/
PATCH  /api/fundzi/admin/requests/<id>/status/
POST   /api/fundzi/admin/requests/<id>/notes/
POST   /api/fundzi/admin/requests/<id>/assign/
POST   /api/fundzi/admin/requests/<id>/archive/
POST   /api/fundzi/admin/requests/<id>/attachments/
DELETE /api/fundzi/admin/requests/<id>/attachments/<att_id>/

GET    /api/fundzi/admin/services/
POST   /api/fundzi/admin/services/
GET    /api/fundzi/admin/services/<id>/
PATCH  /api/fundzi/admin/services/<id>/
DELETE /api/fundzi/admin/services/<id>/

POST   /api/fundzi/admin/services/<service_id>/contents/
PATCH  /api/fundzi/admin/services/<service_id>/contents/<content_id>/
DELETE /api/fundzi/admin/services/<service_id>/contents/<content_id>/

PATCH  /api/fundzi/admin/services/<service_id>/form/
POST   /api/fundzi/admin/services/<service_id>/form/fields/
PATCH  /api/fundzi/admin/services/<service_id>/form/fields/<field_id>/
DELETE /api/fundzi/admin/services/<service_id>/form/fields/<field_id>/

PATCH  /api/fundzi/admin/services/<service_id>/workflow/
POST   /api/fundzi/admin/services/<service_id>/workflow/steps/
PATCH  /api/fundzi/admin/services/<service_id>/workflow/steps/<step_id>/
DELETE /api/fundzi/admin/services/<service_id>/workflow/steps/<step_id>/

GET    /api/fundzi/admin/users/
GET    /api/fundzi/admin/users/<id>/
PATCH  /api/fundzi/admin/users/<id>/
POST   /api/fundzi/admin/users/<id>/set-role/

GET    /api/fundzi/admin/partners/
POST   /api/fundzi/admin/partners/
GET    /api/fundzi/admin/partners/<id>/
PATCH  /api/fundzi/admin/partners/<id>/
DELETE /api/fundzi/admin/partners/<id>/
```

Admin request list now supports:

- server-side pagination with `page` / `page_size`
- search with `q` / `search`
- filters: `service`, `status`, `tracking_code`, `user_phone`
- ordering: `submitted_at`, `-submitted_at`, `current_status`, `-current_status`, `updated_at`, `-updated_at`
- backward-compatible `{ results, count, page, page_size }` response shape

Admin request detail now supports:

- full submitted form values
- attachments
- workflow steps
- status timeline/history
- internal notes
- status change with note
- assignee assignment/removal
- archive/unarchive
- admin upload/delete attachments

Admin dashboard now uses `GET /api/fundzi/admin/stats/` and shows:

- total request count
- status breakdown
- service breakdown
- today count
- last 7 days count
- archived count
- user count
- latest requests

Admin services page now supports in-panel management for:

- service base fields
- service JSON fields: `rules_config`, `metadata`
- service content blocks
- dynamic form metadata
- form fields, including `options` and `validation_config`
- workflow metadata
- workflow steps

Admin users page now supports:

- search by phone/name
- role filtering
- paginated admin user list
- first/last name editing
- `is_active` editing
- `is_staff` editing
- role changes through groups/staff flags

Admin vendors/partners page now supports `FinancialPartner` CRUD:

- `name`
- `type`
- `service_categories`
- `min_amount`
- `max_amount`
- `accepted_collateral_types`
- `is_active`
- `description`

No new database migration was needed for this update. Existing Fundzi models already contained the required fields.

### Auth Notes

The MVP has an OTP-friendly flow.

For demo purposes:

```text
OTP code = 123456
```

`verify-otp` creates/loads a Django user by phone number and logs them in using Django session auth.

Admin users should be created with:

```bash
./venv/bin/python manage.py createsuperuser
```

Role detection:

- staff/superuser -> `admin`
- group `operator` -> `operator`
- group `investor` -> `investor`
- group `vendor` -> `vendor`
- otherwise -> `applicant`

### Django Admin

Admin registration exists for:

- services
- service content
- dynamic forms
- form fields
- workflows
- workflow steps
- financing requests
- field values
- attachments
- history
- internal notes
- financial partners

Admin can:

- inspect submitted values
- inspect files
- change status
- add notes
- view history

### Django User-Facing Fallback Pages

Basic server-rendered pages exist under:

```text
/fundzi/
```

These were built before the Next.js interface and remain useful as fallback/demo pages.

### Media Handling

`fundzii/urls.py` serves media in `DEBUG` mode:

```python
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

This is important because uploaded documents are returned as `/media/...`.

## Frontend Work

### Frontend Location

Created dedicated frontend app:

```text
interface/
```

No frontend code was placed randomly in backend folders.

### Frontend Stack

Implemented:

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui-style local components
- React Hook Form
- Zustand auth/session state
- Lucide React icons
- typed Fetch API client

### Important Config Files

```text
interface/package.json
interface/next.config.ts
interface/tsconfig.json
interface/tailwind.config.ts
interface/postcss.config.js
interface/components.json
interface/.env.example
interface/README.md
```

### Environment Variable

```text
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### API Proxy

The frontend calls:

```text
/backend/...
```

`next.config.ts` rewrites this to:

```text
NEXT_PUBLIC_API_BASE_URL
```

This avoids local CORS issues.

Example:

```text
/backend/api/fundzi/services/
```

rewrites to:

```text
http://127.0.0.1:8000/api/fundzi/services/
```

### Frontend Pages

Public:

```text
/
/services
/services/[slug]
/auth/login
/auth/verify
```

Applicant/user:

```text
/dashboard
/dashboard/requests
/dashboard/requests/[id]
/services/[slug]/apply
```

Admin:

```text
/admin
/admin/requests
/admin/requests/[id]
/admin/services
/admin/users
/admin/vendors
```

Operator:

```text
/operator
/operator/requests
/operator/requests/[id]
```

### Frontend Components

Layout:

```text
components/layout/AppHeader.tsx
components/layout/AppSidebar.tsx
components/layout/MobileNav.tsx
components/layout/DashboardShell.tsx
components/layout/RoleGuard.tsx
```

Auth:

```text
components/auth/LoginForm.tsx
components/auth/OtpVerifyForm.tsx
```

Services:

```text
components/services/ServiceCard.tsx
components/services/ServiceList.tsx
components/services/ServiceDetail.tsx
components/services/ServiceConditions.tsx
components/services/RequiredDocuments.tsx
```

Dynamic forms:

```text
components/forms/DynamicFormRenderer.tsx
components/forms/DynamicField.tsx
components/forms/FileUploadField.tsx
components/forms/MoneyInput.tsx
components/forms/SelectField.tsx
```

Requests:

```text
components/requests/RequestCard.tsx
components/requests/RequestList.tsx
components/requests/RequestStatusBadge.tsx
components/requests/RequestTimeline.tsx
components/requests/RequestDetail.tsx
components/requests/RequestSubmittedValues.tsx
components/requests/RequestAttachments.tsx
```

Admin:

```text
components/admin/AdminRequestTable.tsx
components/admin/AdminStatusChanger.tsx
components/admin/AdminInternalNotes.tsx
components/admin/AdminServiceManager.tsx
components/admin/AdminFilters.tsx
components/admin/AdminRequestActions.tsx
```

UI primitives:

```text
components/ui/button.tsx
components/ui/card.tsx
components/ui/input.tsx
components/ui/textarea.tsx
components/ui/label.tsx
components/ui/badge.tsx
components/ui/table.tsx
components/ui/alert.tsx
components/ui/separator.tsx
components/ui/skeleton.tsx
```

### Frontend API Layer

Implemented under:

```text
interface/lib/api/
```

Files:

```text
client.ts
auth.ts
services.ts
requests.ts
admin.ts
adminServices.ts
users.ts
vendors.ts
```

### Frontend Types

Implemented under:

```text
interface/types/
```

Files:

```text
auth.ts
user.ts
service.ts
form.ts
request.ts
workflow.ts
admin.ts
vendor.ts
```

### Frontend Hooks

Implemented:

```text
hooks/useAuth.ts
hooks/useCurrentUser.ts
hooks/useServices.ts
hooks/useRequests.ts
hooks/useDynamicForm.ts
```

### Dynamic Form Rendering

`DynamicFormRenderer` fetches backend form schema and renders fields dynamically.

It does not hardcode gold/property forms.

It supports:

- text
- textarea
- number
- select
- multi_select
- boolean
- date
- file
- money
- percentage

If a form has file fields, submission uses `multipart/form-data`.

### File URL Handling

Backend returns file paths like:

```text
/media/...
```

Frontend helper:

```text
interface/lib/utils/fileUrl.ts
```

converts these to:

```text
/backend/media/...
```

so Next.js proxy can serve them from Django.

### Status Labels

Centralized in:

```text
interface/lib/utils/statusLabels.ts
```

Examples:

- `submitted` -> `ثبت شده`
- `initial_review` -> `در حال بررسی اولیه`
- `approved` -> `تأیید شده`
- `rejected` -> `رد شده`
- `needs_more_information` -> `نیاز به تکمیل اطلاعات`

### Role Guards

Implemented in:

```text
interface/components/layout/RoleGuard.tsx
```

Rules:

- dashboard routes require authenticated roles
- admin routes require admin
- operator routes require admin/operator
- unauthorized users see Persian access-denied UI

Backend remains the source of truth for security.

## Tests

Backend tests are in:

```text
apps/fundzi/tests.py
```

Current test count:

```text
19 tests
```

Covered behavior:

- active services list
- service detail content
- dynamic form schema
- gold request submission
- property request submission
- LTV validation
- invalid district validation
- tracking code generation
- initial workflow status
- user can list own requests only
- user cannot view another user’s request
- file upload stored as value and attachment
- admin status change creates history
- internal note model
- user page rendering
- OTP send/verify/current user
- OTP code required
- admin request list/detail endpoints
- admin note endpoint

Commands run successfully:

```bash
./venv/bin/python manage.py check
./venv/bin/python manage.py makemigrations --check --dry-run
./venv/bin/python manage.py test apps.fundzi
```

Latest result:

```text
19 tests OK
No changes detected
System check identified no issues
```

## Latest Verification

The latest admin-completion pass was verified with both backend and frontend commands.

Backend:

```bash
venv/bin/python manage.py check
venv/bin/python manage.py makemigrations --check
```

Frontend:

```bash
cd interface
npm run lint
npm run typecheck
npm run build
```

Latest result:

```text
Django system check: OK
Django makemigrations --check: No changes detected
ESLint: OK
TypeScript typecheck: OK
Next.js production build: OK
```

Note: `interface/eslint.config.mjs` was added because this project uses ESLint 9, which requires flat config. The config extends `next/core-web-vitals` and `next/typescript`.

## How To Run Locally

Backend:

```bash
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_fundzi
./venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Frontend:

```bash
cd interface
npm install
cp .env.example .env.local
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Demo Scenarios

### Scenario 1: Gold-backed Financing

1. User opens `/auth/login`
2. User enters phone number
3. User verifies OTP using `123456`
4. User goes to `/services`
5. User opens `تأمین مالی با پشتوانه طلا`
6. User starts request
7. Dynamic gold form renders
8. User submits form
9. Backend creates tracking code
10. User opens request detail
11. User sees status and timeline
12. Admin opens request
13. Admin changes status
14. History updates

### Scenario 2: Property-backed Financing

1. User opens property-backed service
2. Dynamic property form renders
3. User fills property data
4. Backend validates Tehran/district/LTV/duration
5. User sees validation errors or success
6. Request enters property workflow
7. Admin/operator reviews and changes status

### Scenario 3: Admin Review

1. Admin logs in
2. Admin opens `/admin/requests`
3. Admin filters requests
4. Admin opens request detail
5. Admin sees values and attachments
6. Admin changes status
7. Admin adds internal note
8. Admin assigns/removes an assignee
9. Admin archives/unarchives the request
10. Admin uploads/deletes request attachments
11. Timeline/history updates

### Scenario 4: Admin Service Management

1. Admin opens `/admin/services`
2. Admin creates or selects a service
3. Admin edits base service fields
4. Admin edits JSON config fields
5. Admin adds/edits/deletes content blocks
6. Admin edits dynamic form title
7. Admin adds/edits/deletes form fields
8. Admin edits workflow name
9. Admin adds/edits/deletes workflow steps

### Scenario 5: Admin User Management

1. Admin opens `/admin/users`
2. Admin searches by phone/name
3. Admin filters by role
4. Admin selects a user
5. Admin edits first/last name
6. Admin toggles active/staff flags
7. Admin changes role through the role selector

### Scenario 6: Admin Partner/Vendor Management

1. Admin opens `/admin/vendors`
2. Admin creates a financial partner
3. Admin edits type, service categories, amount range, collateral types, active flag, and description
4. Admin deletes a partner if needed

## Important Files For Review

Backend:

```text
apps/fundzi/models.py
apps/fundzi/services.py
apps/fundzi/api/views.py
apps/fundzi/admin.py
apps/fundzi/tests.py
apps/fundzi/management/commands/seed_fundzi.py
fundzii/urls.py
fundzii/settings.py
```

Frontend:

```text
interface/app/
interface/components/
interface/lib/api/
interface/lib/utils/
interface/types/
interface/hooks/
interface/package.json
interface/next.config.ts
interface/README.md
```

## Files Changed In Admin Completion Pass

Backend:

```text
apps/fundzi/api/views.py
apps/fundzi/api/urls.py
```

Frontend pages:

```text
interface/app/admin/page.tsx
interface/app/admin/requests/page.tsx
interface/app/admin/requests/[id]/page.tsx
interface/app/admin/services/page.tsx
interface/app/admin/users/page.tsx
interface/app/admin/vendors/page.tsx
```

Frontend components:

```text
interface/components/admin/AdminFilters.tsx
interface/components/admin/AdminRequestActions.tsx
interface/components/admin/AdminRequestTable.tsx
interface/components/admin/AdminServiceManager.tsx
```

Frontend API clients and types:

```text
interface/lib/api/admin.ts
interface/lib/api/adminServices.ts
interface/lib/api/client.ts
interface/lib/api/users.ts
interface/lib/api/vendors.ts
interface/types/admin.ts
interface/types/request.ts
interface/types/service.ts
interface/types/user.ts
interface/types/vendor.ts
```

Frontend tooling:

```text
interface/eslint.config.mjs
interface/tailwind.config.ts
interface/middleware.ts
```

## Review Notes / Things Another AI Should Check

1. Re-run frontend verification if dependencies or UI code change:

```bash
cd interface
npm install
npm run lint
npm run typecheck
npm run build
```

2. Manually test browser flow:

- OTP login
- services list
- service detail
- dynamic request form
- file upload
- dashboard requests
- admin dashboard
- admin request filtering/pagination/detail
- status change
- internal note
- assignee/archive/attachment actions
- service CRUD/form/workflow management
- user role/status editing
- partner/vendor CRUD

3. Confirm Django session cookies work correctly through Next rewrite `/backend`.

4. Confirm uploaded file links open correctly through `/backend/media/...`.

5. Confirm production deployment plan:

- Django and Next on same domain or proper CORS/session cookie config
- media storage in production
- real OTP provider instead of demo `123456`

6. Consider replacing demo OTP with real existing account OTP service when productionizing.

7. Consider adding frontend automated tests for the completed admin workflows.

## Current Status

Backend:

```text
Ready and tested
```

Frontend:

```text
Implemented, typechecked, linted, and production-build verified
```

Overall MVP:

```text
Demo-ready with the custom admin panel completed and verified
```
