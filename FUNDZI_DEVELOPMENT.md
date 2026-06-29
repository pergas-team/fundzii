# سند توسعه‌ی فاندزی (Fundzi Development Roadmap)

این سند نقشه‌ی راه توسعه‌ی فاندزی پس از تکمیل MVP فاز ۱ است. وضعیت هر آیتم در حین کار به‌روزرسانی می‌شود.

## وضعیت پایه (نقطه‌ی شروع)

- ✅ هسته‌ی فاز ۱: کاتالوگ سرویس، فرم داینامیک، آپلود فایل، ثبت درخواست، workflow، tracking code، پنل ادمین، تاریخچه، یادداشت داخلی
- ✅ Backend: تست‌ها سبز، API هم‌تراز با فرانت، مرز امنیتی `401/403` اصلاح‌شده
- ✅ Frontend: ۱۹ صفحه، typecheck و build پاک
- ✅ عنوان workflowها فارسی (key انگلیسی)
- ✅ git راه‌اندازی شد

---

## فاز ۱ — آماده‌سازی برای عرضه

| آیتم | شرح | برآورد | وابستگی | وضعیت |
|---|---|---|---|---|
| ۱.۱ | OTP واقعی | ۱–۲ روز | ارائه‌دهنده‌ی SMS | ⬜ |
| ۱.۲ | سخت‌سازی امنیتی | ۱–۲ روز | — | ⬜ |
| ۱.۳ | مهاجرت به PostgreSQL | ۱ روز | سرور DB | ⬜ |
| ۱.۴ | ذخیره‌سازی فایل‌ها | ۱–۲ روز | ۱.۳ | ⬜ |
| ۱.۵ | استقرار سرور | ۲–۳ روز | ۱.۲، ۱.۳، ۱.۴ | ⬜ |
| ۱.۶ | لاگ‌گذاری و مانیتورینگ | ۱–۲ روز | ۱.۵ | ⬜ |

**ترتیب اجرا:** ۱.۱ → ۱.۲ → ۱.۳ → ۱.۴ → ۱.۵ → ۱.۶

---

### ۱.۱ — OTP واقعی

**هدف:** غیرفعال کردن `FUNDZI_OTP_ENABLED = False` و اتصال به ارائه‌دهنده‌ی واقعی.

**Backend**
- انتخاب ارائه‌دهنده: کاوه‌نگار (Kavenegar) یا ملی‌پیامک — هر دو REST API ساده دارند
- نوشتن آداپتور `apps/fundzi/otp_backend.py` با یک تابع `send_otp(phone, code) -> bool`
- جایگزینی `print(f"OTP: {otp_code}")` در `views.py` با فراخوانی آداپتور
- ذخیره‌ی `OTP_API_KEY` در environment variable (نه settings.py)
- تنظیم مدت انقضای OTP (پیش‌فرض: ۵ دقیقه)
- فعال‌سازی `FUNDZI_OTP_ENABLED = True` در production

**تست**
- `@override_settings(FUNDZI_OTP_ENABLED=True)` — تست‌های موجود کافی هستند
- تست integration با sandbox ارائه‌دهنده (محیط staging)

> **پرامپت اجرا:**
> آیتم ۱.۱ فاز اول (OTP واقعی) رو پیاده‌سازی کن. پروژه Django 5.2 داره با یک فلو OTP دومرحله‌ای — الان `FUNDZI_OTP_ENABLED = False` هست و کد OTP فقط با `print` نمایش داده می‌شه. کارها: یک آداپتور در `apps/fundzi/otp_backend.py` بنویس با تابع `send_otp(phone: str, code: str) -> bool` که از کاوه‌نگار استفاده کنه (API key از env `KAVENEGAR_API_KEY`)؛ `print` موجود در `apps/fundzi/api/views.py` رو با این آداپتور جایگزین کن؛ مدت انقضای OTP رو ۵ دقیقه تنظیم کن؛ فایل `.env.example` رو آپدیت کن. تست‌های موجود باید همچنان سبز بمونن.

---

### ۱.۲ — سخت‌سازی امنیتی

**هدف:** پیکربندی Django برای production؛ جلوگیری از آسیب‌پذیری‌های رایج.

**Backend**
- `SECRET_KEY` از env (`os.environ['DJANGO_SECRET_KEY']`)، نه hardcode
- `DEBUG = False` در production؛ `ALLOWED_HOSTS` دقیق
- `CSRF_COOKIE_SECURE = True`، `SESSION_COOKIE_SECURE = True`، `CSRF_TRUSTED_ORIGINS` برای دامنه‌ی فرانت
- `X_FRAME_OPTIONS = 'DENY'`، `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT` (بعد از HTTPS)
- فایل `.env.example` برای متغیرهای لازم
- جدا کردن `settings/base.py` / `settings/production.py` / `settings/local.py`

**Frontend (Next.js)**
- اضافه کردن `Content-Security-Policy` header در `next.config.ts`
- بررسی `CORS_ALLOWED_ORIGINS` از طرف Django برای `/api/*`
- Rate limiting روی login/OTP از طریق nginx یا middleware

> **پرامپت اجرا:**
> آیتم ۱.۲ فاز اول (سخت‌سازی امنیتی) رو پیاده‌سازی کن. پروژه Django 5.2 + Next.js 15 داره. الان `SECRET_KEY` hardcode توی `fundzii/settings.py` هست و `DEBUG = True`. کارها: فایل settings رو به سه فایل `fundzii/settings/base.py`، `local.py`، `production.py` تقسیم کن؛ همه‌ی متغیرهای حساس رو از env بخون با `os.environ.get`؛ تنظیمات امنیتی production رو اضافه کن (CSRF_COOKIE_SECURE، SESSION_COOKIE_SECURE، ALLOWED_HOSTS، X_FRAME_OPTIONS، SECURE_CONTENT_TYPE_NOSNIFF)؛ فایل `.env.example` بساز؛ در Next.js توی `next.config.ts` هدر CSP اضافه کن. تست‌های ۲۶ تایی باید همچنان سبز بمونن.

---

### ۱.۳ — مهاجرت به PostgreSQL

**هدف:** جایگزینی SQLite با PostgreSQL برای قابلیت اطمینان و concurrency.

**Backend**
- نصب `psycopg2-binary` (یا `psycopg[binary]`)، افزودن به `requirements.txt`
- تنظیم `DATABASES` از env: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `python manage.py migrate` روی PostgreSQL جدید
- اجرای `seed_fundzi` برای داده‌های اولیه
- بررسی indexes (مدل `Notification` index `(user, is_read)` — با SQLite بی‌اثر، با Postgres فعال)

**داده‌های موجود**
- صادر کردن داده‌ی SQLite با `dumpdata` قبل از مهاجرت
- وارد کردن با `loaddata` روی Postgres پس از migrate

> **پرامپت اجرا:**
> آیتم ۱.۳ فاز اول (مهاجرت به PostgreSQL) رو پیاده‌سازی کن. پروژه از SQLite استفاده می‌کنه (`db.sqlite3`). کارها: `psycopg2-binary` رو به `requirements.txt` اضافه کن؛ تنظیم `DATABASES` در settings رو طوری تغییر بده که اگر env variable `DATABASE_URL` تعریف شده باشه از Postgres استفاده کنه و وگرنه به SQLite fallback کنه؛ متغیرهای `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` رو به `.env.example` اضافه کن. مطمئن شو `python manage.py check` و تمام ۲۶ تست همچنان سبز می‌مونن.

---

### ۱.۴ — ذخیره‌سازی فایل‌ها

**هدف:** انتقال media از `MEDIA_ROOT` محلی به ذخیره‌سازی persistent (S3 یا MinIO).

**Backend**
- نصب `django-storages[s3]` یا `boto3`
- پیکربندی `DEFAULT_FILE_STORAGE` برای S3/MinIO
- متغیرهای env: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`
- migration داده‌های media موجود با `aws s3 sync`
- بررسی `FileUpload` model — `document` field باید بدون تغییر کار کند

**Frontend**
- اطمینان از اینکه URL های فایل از `/media/...` به `https://cdn.../...` تغییر می‌کنند
- پیاده‌سازی presigned URL برای دانلود امن مدارک (optional در فاز اول)

> **پرامپت اجرا:**
> آیتم ۱.۴ فاز اول (ذخیره‌سازی فایل با S3/MinIO) رو پیاده‌سازی کن. پروژه Django 5.2 داره و مدل `FileUpload` با فیلد `document = FileField` فایل‌های کاربر رو ذخیره می‌کنه — الان روی دیسک محلی. کارها: `django-storages[s3]` رو به `requirements.txt` اضافه کن؛ در `fundzii/settings/production.py` پیکربندی `DEFAULT_FILE_STORAGE`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL` رو از env بخون؛ در محیط local همچنان از `FileSystemStorage` استفاده کن؛ `.env.example` رو آپدیت کن. مطمئن شو آپلود و دانلود فایل توی تست‌ها همچنان کار می‌کنن.

---

### ۱.۵ — استقرار سرور

**هدف:** اجرای پایدار در production با nginx + gunicorn.

**Backend**
- نصب `gunicorn`، افزودن به `requirements.txt`
- فایل `gunicorn.conf.py`: `workers = 2 * CPU + 1`، `bind = "127.0.0.1:8000"`، `timeout = 120`
- systemd service: `fundzi-backend.service` (restart on failure)
- `python manage.py collectstatic` → `STATIC_ROOT`

**Frontend**
- `npm run build` → `.next/` standalone
- PM2 یا systemd service برای `node server.js`
- (option ب) Deploy روی Vercel — ساده‌تر برای فاز اول

**nginx**
- reverse proxy برای Django (`/api/`, `/admin/`, `/static/`, `/media/`)
- reverse proxy برای Next.js (همه‌ی مسیرهای دیگر)
- SSL با Let's Encrypt (certbot)

> **پرامپت اجرا:**
> آیتم ۱.۵ فاز اول (استقرار) رو آماده‌سازی کن — فایل‌های پیکربندی لازم رو بساز. کارها: فایل `gunicorn.conf.py` در ریشه‌ی پروژه بساز (`workers = multiprocessing.cpu_count() * 2 + 1`، `bind = "127.0.0.1:8000"`، `timeout = 120`)؛ فایل `deploy/fundzi-backend.service` برای systemd بساز؛ فایل `deploy/nginx.conf` بساز که `/api/`, `/admin/`, `/static/`, `/media/` رو به gunicorn (پورت 8000) و بقیه رو به Next.js (پورت 3000) پروکسی کنه؛ فایل `deploy/README.md` با دستورات گام‌به‌گام استقرار روی Ubuntu 22.04 بساز. فاندزی یک Django 5.2 + Next.js 15 هست.

---

### ۱.۶ — لاگ‌گذاری و مانیتورینگ

**هدف:** دیدپذیری روی خطاها و رفتار سیستم در production.

**Backend**
- پیکربندی `LOGGING` در Django: `WARNING+` به stdout، `ERROR+` به Sentry
- نصب `sentry-sdk[django]`، `dsn` از env
- middleware برای لاگ زمان response (optional)
- health-check endpoint: `GET /api/fundzi/health/` → `{"status": "ok", "db": true}`

**Frontend**
- `@sentry/nextjs` برای error tracking در browser و SSR
- لاگ 4xx/5xx از `apiFetch` به console/Sentry

**زیرساخت**
- لاگ‌های nginx و gunicorn در `/var/log/fundzi/`
- rotation با `logrotate`
- هشدار uptime (UptimeRobot یا Betterstack — رایگان)

> **پرامپت اجرا:**
> آیتم ۱.۶ فاز اول (لاگ‌گذاری و مانیتورینگ) رو پیاده‌سازی کن. پروژه Django 5.2 + Next.js 15 داره. کارها: تنظیم `LOGGING` در `fundzii/settings/base.py` برای لاگ `WARNING+` به stdout؛ نصب `sentry-sdk[django]` و افزودن به `requirements.txt`؛ پیکربندی Sentry در production.py از env `SENTRY_DSN`؛ اضافه کردن health-check endpoint `GET /api/fundzi/health/` که اتصال به دیتابیس رو چک کنه و `{"status": "ok", "db": true}` برگردونه (یا `503` اگر DB در دسترس نباشه)؛ URL این endpoint رو به `apps/fundzi/api/urls.py` اضافه کن؛ یک تست ساده برای `/health/` بنویس. تست‌های موجود باید همچنان سبز بمونن.

---

## فاز ۲ — تجربه‌ی اپراتور و کاربر

| آیتم | شرح | برآورد | وابستگی | وضعیت |
|---|---|---|---|---|
| ۲.۵ | تست خودکار + CI | ۲–۳ روز | git init | ✅ انجام شد |
| ۲.۱ | داشبورد واقعی + pagination | ۴–۵ روز | — | ✅ انجام شد |
| ۲.۲ | مدیریت کاربران در فرانت | ۳–۴ روز | گارد admin inline | ✅ انجام شد |
| ۲.۳ | نوتیفیکیشن کاربر | ۲–۴ روز | hook روی RequestHistory | ✅ انجام شد |
| ۲.۴ | مدیریت سرویس/فرم/workflow از UI | ۵–۷ روز | — | ✅ انجام شد |

**ترتیب اجرا:** ۲.۵ → ۲.۱ → ۲.۲ → ۲.۳ → ۲.۴

> وضعیت: کل فاز ۲ پیاده‌سازی شد. تست‌های بک‌اند: **۲۶ سبز**. typecheck و build فرانت: پاک.
> نوتیفیکیشن فعلاً sync است (بدون Celery)؛ کانال‌های SMS/ایمیل pluggable و با
> `FUNDZI_SMS_NOTIFICATIONS_ENABLED` / `FUNDZI_EMAIL_NOTIFICATIONS_ENABLED` خاموش‌اند تا
> ارائه‌دهنده‌ی واقعی فاز ۱ وصل شود.

---

### ۲.۵ — تست خودکار + CI

**هدف:** هر تغییر به‌صورت خودکار اعتبارسنجی شود.

- GitHub Actions: backend tests (`manage.py test`) + frontend (`typecheck`, `build`)
- اجرای job روی هر push و pull request
- (آینده) Playwright e2e روی فلوهای اصلی: لاگین، ثبت درخواست با آپلود، رهگیری، تغییر وضعیت ادمین، گاردهای نقش

---

### ۲.۱ — داشبورد واقعی + pagination

**Backend**
- helper صفحه‌بندی مشترک (`limit`/`offset`) روی تمام لیست‌ها (`results`, `count`, `next`, `previous`)
- `GET /api/fundzi/admin/stats/` → شمارش به تفکیک وضعیت، درخواست‌های امروز، صف بدون متصدی
- فیلتر پیشرفته روی لیست ادمین: assignee، بازه‌ی تاریخ، مرتب‌سازی، آرشیو
- `POST /api/fundzi/admin/requests/<id>/assign/` (فیلد `admin_assignee` موجود است)

**Frontend**
- کارت‌های آماری بالای داشبورد ادمین/اپراتور
- صف کار با تب (ارجاع‌شده به من / بدون متصدی / همه)
- کنترل صفحه‌بندی روی جدول‌ها
- دکمه‌ی self-assign

---

### ۲.۲ — مدیریت کاربران در فرانت

**Backend**
- decorator `api_admin_required` (فقط staff/superuser، نه operator)
- `GET /api/fundzi/admin/users/` با صفحه‌بندی و جستجو
- `GET /api/fundzi/admin/users/<id>/` → پروفایل + درخواست‌های کاربر
- `POST /api/fundzi/admin/users/<id>/role/` → تغییر نقش از طریق Django groups
- فعال/غیرفعال‌سازی کاربر

**Frontend**
- جدول کاربران واقعی (جایگزین stub) + جستجو + صفحه‌بندی
- صفحه‌ی جزئیات کاربر
- تغییر نقش با گارد admin

---

### ۲.۳ — نوتیفیکیشن کاربر

**Backend**
- مدل `NotificationLog` (کاربر، نوع، کانال، وضعیت، payload) برای رهگیری و idempotency
- لایه‌ی سرویس نوتیفیکیشن با کانال‌های pluggable (SMS، ایمیل، درون‌اپ)
- قلاب در `FinancingRequest.change_status()` روی stepهای کلیدی
- متن پیام‌ها بر اساس `WORKFLOW_STEP_LABELS`
- (در صورت نیاز) اجرای async با Celery + Redis

**Frontend**
- نمایش نوتیفیکیشن‌های درون‌اپ + mark-as-read

---

### ۲.۴ — مدیریت سرویس/فرم/workflow از UI

**Backend**
- CRUD برای `FinancialService`، `ServiceContent`، `DynamicForm`، `FormField`، `Workflow`، `WorkflowStep`
- اعتبارسنجی ساختاری: دقیقاً یک `is_initial`، یکتایی `key`، جلوگیری از حذف step دارای درخواست فعال
- ویرایش `rules_config`

**Frontend**
- ویرایشگر فرم (افزودن/مرتب‌سازی فیلد)
- ویرایشگر workflow
- ویرایشگر محتوای سرویس
- پیش‌نمایش زنده‌ی فرم

**یادداشت:** پیچیده‌ترین آیتم UI؛ ابتدا محتوا و فیلد ساده، سپس ویرایشگر کامل workflow.

---

## فاز ۳ — گسترش دامنه‌ی کسب‌وکار

| آیتم | شرح | برآورد | وابستگی | وضعیت |
|---|---|---|---|---|
| ۳.۱ | پورتال همکار مالی | ۷–۱۰ روز | فاز ۱ | ⬜ |
| ۳.۲ | موتور تطبیق | ۵–۷ روز | ۳.۱ | ⬜ |
| ۳.۳ | قرارداد و امضای دیجیتال | ۵–۸ روز | ۳.۲ | ⬜ |
| ۳.۴ | کیف پول / پرداخت / اسکرو | ۱۰–۱۴ روز | ۳.۳ | ⬜ |
| ۳.۵ | گزارش‌گیری و تحلیل | ۳–۵ روز | ۳.۱ | ⬜ |

**ترتیب اجرا:** ۳.۱ → ۳.۲ → ۳.۵ (موازی) → ۳.۳ → ۳.۴

---

### ۳.۱ — پورتال همکار مالی (Vendor Portal)

**هدف:** ارائه‌ی دسترسی جداگانه به بانک‌ها، صندوق‌ها و شرکت‌های مالی برای مشاهده و پاسخ به درخواست‌های تطبیق‌یافته.

**مدل‌ها**
- `FinancialPartner`: نام، نوع (bank / fund / leasing)، `is_active`، اطلاعات تماس
- `PartnerUser`: رابط بین `User` و `FinancialPartner`، نقش درون سازمان (admin / analyst)
- `PartnerOffer`: پیشنهاد رسمی از شریک مالی به یک `FinancingRequest` (مبلغ، نرخ، شرایط، `expires_at`)

**Backend**
- decorator `api_partner_required`: کاربر باید عضو یک `FinancialPartner` فعال باشد
- `GET /api/fundzi/partner/requests/` — فقط درخواست‌های assign‌شده به این شریک
- `GET /api/fundzi/partner/requests/<id>/` — جزئیات (بدون اطلاعات شناسایی کاربر)
- `POST /api/fundzi/partner/requests/<id>/offer/` — ثبت پیشنهاد رسمی
- `GET /api/fundzi/partner/offers/` — لیست پیشنهادهای داده‌شده + وضعیت پذیرش

**Frontend**
- لاگین جداگانه یا تفکیک route زیر `/partner/`
- داشبورد شریک: درخواست‌های فعال، وضعیت پیشنهادها
- فرم ثبت پیشنهاد: مبلغ تسهیلات، نرخ سود/کارمزد، مدت، شرایط خاص، تاریخ انقضا
- نمایش مدارک (با presigned URL)

---

### ۳.۲ — موتور تطبیق (Matching Engine)

**هدف:** اتصال خودکار درخواست‌های کاربر به شرکای مالی مناسب بر اساس پارامترهای از پیش‌تعریف‌شده.

**مدل‌ها**
- `MatchingRule`: مجموعه‌ای از شرط‌ها (JSON) + `FinancialPartner` هدف + اولویت
  - شرط‌ها: `service_id`, `min_amount`, `max_amount`, `property_type`, `region`
- `MatchResult`: رابط `FinancingRequest` ↔ `FinancialPartner` با `score`, `matched_at`, `status`

**Backend**
- سرویس `matching.run(request)` — اجرا پس از رسیدن به step مشخص (مثلاً `property_valuation`)
- اجرا با signal یا manual trigger توسط اپراتور
- `GET /api/fundzi/admin/requests/<id>/matches/` — لیست تطبیق‌ها + امتیاز
- `POST /api/fundzi/admin/requests/<id>/matches/<partner_id>/assign/` — ارسال رسمی به شریک
- رابط ادمین برای مدیریت `MatchingRule` ها

**Frontend**
- در صفحه‌ی جزئیات درخواست ادمین: بخش "شرکای پیشنهادی" با امتیاز
- دکمه‌ی "ارسال به شریک" (با تأیید)
- ویرایشگر قوانین تطبیق در پنل ادمین

---

### ۳.۳ — قرارداد و امضای دیجیتال

**هدف:** تولید و امضای الکترونیک قرارداد پس از پذیرش پیشنهاد.

**مدل‌ها**
- `Contract`: رابط `PartnerOffer` ↔ `FinancingRequest`؛ فیلدها: `template`, `content` (JSON)، `status` (draft/sent/signed/rejected)، `signed_at`, `pdf_file`
- `ContractSignature`: امضای هر طرف (`user`, `partner_user`, `admin`)؛ `ip_address`, `signed_at`, `otp_verified`

**Backend**
- تولید PDF از template (کتابخانه: `WeasyPrint` یا `reportlab`)
- endpoint ثبت امضا با تأیید OTP: `POST /api/fundzi/contracts/<id>/sign/`
- ذخیره‌ی PDF نهایی در media/S3
- نوتیفیکیشن به کاربر و شریک هنگام آماده‌شدن قرارداد برای امضا
- (آینده) اتصال به سرویس امضای معتبر (جمع‌امضا، ایمضا)

**Frontend**
- صفحه‌ی مشاهده‌ی قرارداد (PDF در iframe یا HTML preview)
- دکمه‌ی "تأیید و امضا" + تأیید OTP
- وضعیت امضا هر طرف (pending / signed)
- دانلود PDF نهایی

---

### ۳.۴ — کیف پول / پرداخت / اسکرو

**هدف:** مدیریت مالی داخل پلتفرم — کارمزد سرویس، آزادسازی تسهیلات، اسکرو.

**مدل‌ها**
- `Wallet`: موجودی هر `User` و هر `FinancialPartner` در پلتفرم
- `Transaction`: ثبت هر تراکنش (نوع: deposit/withdraw/fee/escrow_lock/escrow_release)؛ `amount`, `currency`, `status`, `reference_id`
- `EscrowAccount`: قفل وجه برای یک `Contract` تا تکمیل شرایط

**Backend**
- اتصال به درگاه پرداخت ایرانی (زرین‌پال / ایران‌کیش / سداد)
- `POST /api/fundzi/wallet/deposit/` — شروع فرآیند پرداخت + redirect به درگاه
- `GET /api/fundzi/wallet/callback/` — تأیید پرداخت از درگاه، شارژ wallet
- `POST /api/fundzi/escrow/<contract_id>/lock/` — قفل مبلغ برای قرارداد
- `POST /api/fundzi/escrow/<contract_id>/release/` — آزادسازی پس از تأیید ادمین
- تمام تراکنش‌ها idempotent (reference_id یکتا)

**Frontend**
- صفحه‌ی کیف پول: موجودی، تاریخچه‌ی تراکنش‌ها
- فرم شارژ با redirect به درگاه
- وضعیت اسکرو در صفحه‌ی قرارداد
- دریافت رسید (PDF)

**نکته‌ی حیاتی:** این آیتم نیازمند مجوز PSP (Payment Service Provider) و اتصال به شاپرک است. باید به‌صورت موازی با ۳.۳ پیگیری شود.

---

### ۳.۵ — گزارش‌گیری و تحلیل

**هدف:** داده‌ی عملیاتی و کسب‌وکاری برای تصمیم‌گیری.

**Backend**
- `GET /api/fundzi/admin/reports/funnel/` — نرخ تبدیل هر step workflow
- `GET /api/fundzi/admin/reports/partner-performance/` — نرخ ارائه‌ی پیشنهاد، زمان پاسخ، نرخ پذیرش هر شریک
- `GET /api/fundzi/admin/reports/monthly/` — درخواست‌ها، تأیید‌ها، مبالغ به تفکیک ماه
- export CSV برای هر گزارش

**Frontend**
- صفحه‌ی `/admin/reports/` با chart های ساده (recharts یا chart.js)
- فیلتر بازه‌ی تاریخ
- دکمه‌ی دانلود CSV

---

## بدهی فنی / کیفیت

- تصمیم معماری: حفظ ویوهای ساده یا مهاجرت به DRF
- مدیریت متمرکز خطای `401` در فرانت (auto-redirect به لاگین)
- اشتراک type بین بک و فرانت (OpenAPI → تولید type)
