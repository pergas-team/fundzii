import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-r^i+desnozk^iq@7ynzf)ekd7o&tdi7ntz1%b2rl^!r7qj^i-5',
)

_env = os.environ.get('DJANGO_ENV', 'local')
DEBUG = _env != 'production'

_allowed = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()] or (['localhost', '127.0.0.1'] if DEBUG else [])

# ── Application definition ────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.fundzi',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.fundzi.api.authentication.CsrfExemptSessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'EXCEPTION_HANDLER': 'apps.fundzi.api.exceptions.exception_handler',
    'NON_FIELD_ERRORS_KEY': 'detail',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fundzii.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'fundzii.wsgi.application'

# Nginx terminates TLS and forwards the original request scheme.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Auth ──────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'fundzi-home'
LOGOUT_REDIRECT_URL = 'fundzi-home'

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static / media ───────────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Fundzi feature flags ──────────────────────────────────────────────────────
# Set FUNDZI_OTP_ENABLED=True in production after wiring KAVENEGAR_API_KEY.
FUNDZI_OTP_ENABLED = os.environ.get('FUNDZI_OTP_ENABLED', 'False').lower() == 'true'

FUNDZI_SMS_NOTIFICATIONS_ENABLED = os.environ.get('FUNDZI_SMS_NOTIFICATIONS_ENABLED', 'False').lower() == 'true'
FUNDZI_EMAIL_NOTIFICATIONS_ENABLED = os.environ.get('FUNDZI_EMAIL_NOTIFICATIONS_ENABLED', 'False').lower() == 'true'

# ── Production security ───────────────────────────────────────────────────────
if not DEBUG:
    _https_enabled = os.environ.get('DJANGO_HTTPS_ENABLED', 'False').lower() == 'true'
    CSRF_COOKIE_SECURE = _https_enabled
    SESSION_COOKIE_SECURE = _https_enabled
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000 if _https_enabled else 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _https_enabled
    SECURE_HSTS_PRELOAD = _https_enabled
    SECURE_SSL_REDIRECT = _https_enabled

    _trusted = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
    if _trusted:
        CSRF_TRUSTED_ORIGINS = [o.strip() for o in _trusted.split(',') if o.strip()]

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.fundzi': {
            'handlers': ['console'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}

# ── Sentry ────────────────────────────────────────────────────────────────────
_sentry_dsn = os.environ.get('SENTRY_DSN', '')
if _sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
    except ImportError:
        pass
