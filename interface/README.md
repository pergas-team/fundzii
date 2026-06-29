# Fundzi Interface

Next.js frontend MVP for Fundzi / فاندزی.

The app is intentionally scoped to phase 1:

- OTP-friendly login
- Role-based dashboard and navigation
- Financial service catalog
- Service detail pages
- Dynamic form rendering
- File upload
- Financing request submission
- Request tracking and timeline
- Admin/operator request review
- Status changes and internal notes

Out of scope:

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

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui-style local components
- React Hook Form
- Zod-ready structure
- Zustand auth state
- Lucide React icons

## Install

Node.js is required. From this folder:

```bash
npm install
```

## Environment

Create `.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The frontend calls `/backend/...` internally. `next.config.ts` rewrites that path to `NEXT_PUBLIC_API_BASE_URL`, which avoids browser CORS problems during local development.

## Run

Backend:

```bash
cd ..
./venv/bin/python manage.py migrate
./venv/bin/python manage.py seed_fundzi
./venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Frontend:

```bash
cd interface
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## Routes

Public:

- `/`
- `/services`
- `/services/[slug]`
- `/auth/login`
- `/auth/verify`

Applicant:

- `/dashboard`
- `/dashboard/requests`
- `/dashboard/requests/[id]`
- `/services/[slug]/apply`

Admin:

- `/admin`
- `/admin/requests`
- `/admin/requests/[id]`
- `/admin/services`
- `/admin/users`
- `/admin/vendors`

Operator:

- `/operator`
- `/operator/requests`
- `/operator/requests/[id]`

## Auth Flow

The UI is OTP-friendly:

1. `/auth/login` sends OTP.
2. `/auth/verify` verifies OTP.
3. The backend creates/loads a Django session user.
4. The frontend fetches current user and redirects by role.

For the current MVP backend, demo OTP is:

```text
123456
```

Admin/staff users should be created through Django:

```bash
./venv/bin/python manage.py createsuperuser
```

## Dynamic Forms

Dynamic forms are rendered from:

```text
GET /api/fundzi/services/{slug}/form/
```

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

The UI does not hardcode gold/property forms. It renders whatever schema the backend returns.

## API Layer

All API functions live in:

```text
lib/api/
```

Files:

- `client.ts`
- `auth.ts`
- `services.ts`
- `requests.ts`
- `admin.ts`
- `users.ts`
- `vendors.ts`

## Role Guards

Frontend access control is implemented with:

```text
components/layout/RoleGuard.tsx
```

Rules:

- Dashboard routes require an authenticated role.
- Admin routes require `admin`.
- Operator routes require `admin` or `operator`.
- Unauthorized users see a Persian access-denied message.

Backend authorization is still required and remains the source of truth.

## Adding A New Service

If a new service is added in backend/admin with:

- service content
- dynamic form fields
- workflow steps
- rules config

the frontend can display and submit it without new page code.

## Verification

Recommended commands:

```bash
npm run typecheck
npm run lint
npm run build
```

These commands require Node.js and installed dependencies.
