import os  # Додано на початку для роботи зі шляхами
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv  # type: ignore

    # Repo root `.env`, потім `backend/.env` (останній перемагає для локальної конфігурації).
    load_dotenv(BASE_DIR.parent / ".env", override=False)
    load_dotenv(BASE_DIR / ".env", override=True)
except Exception:
    pass


def _env_csv(name: str):
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


# Stripe (НЕ зберігай ключі в коді; тільки через env vars)
# STRIPE_PUBLIC_KEY=pk_test_...
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-this-in-production-lingua-app-2024")

DEBUG = os.getenv("DJANGO_DEBUG", "1").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = _env_csv("DJANGO_ALLOWED_HOSTS") or ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'accounts',
    'learning',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOWED_ORIGINS = _env_csv("CORS_ALLOWED_ORIGINS")
if DEBUG and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = _env_csv("CSRF_TRUSTED_ORIGINS")
if DEBUG and not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
}

ROOT_URLCONF = 'lingua.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Додай цей процесор, якщо хочеш використовувати MEDIA_URL у шаблонах
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'lingua.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'lingua_db'),
        'USER': os.getenv('DB_USER', 'lingua_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'lingua123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]

LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

# --- СТАТИЧНІ ФАЙЛИ (CSS, JS, Images) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- МЕДІА ФАЙЛИ (Завантаження користувачів, аватари) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Email (OTP)
# In DEBUG we use console backend by default (prints emails in terminal)
# but only if SMTP is not configured.
if DEBUG and not os.getenv('EMAIL_BACKEND') and not os.getenv('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'no-reply@slovak.local')

# Gmail SMTP (set as env vars if you want real emails)
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587')) if os.getenv('EMAIL_PORT') else 587
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '1') == '1'

# TurboSMS (set as env vars if you want real SMS)
TURBOSMS_TOKEN = os.getenv('TURBOSMS_TOKEN', '')
TURBOSMS_SENDER = os.getenv('TURBOSMS_SENDER', 'TurboSMS')

# LiqPay
LIQPAY_PUBLIC_KEY = os.getenv('LIQPAY_PUBLIC_KEY', '')
LIQPAY_PRIVATE_KEY = os.getenv('LIQPAY_PRIVATE_KEY', '')
LIQPAY_SANDBOX = os.getenv('LIQPAY_SANDBOX', '1') == '1'

# Premium without API keys (payment by link)
# Example: Monobank "банка" / WayForPay hosted checkout / PayPal.me etc.
PREMIUM_PAYMENT_URL = os.getenv('PREMIUM_PAYMENT_URL', '')
PREMIUM_PAYMENT_INSTRUCTIONS = os.getenv(
    'PREMIUM_PAYMENT_INSTRUCTIONS',
    'Після оплати повернись сюди та введи ID/коментар платежу, щоб ми активували Premium.'
)