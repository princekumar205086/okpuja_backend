import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-for-dev')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,backend.okpuja.com,backend.okpuja.com,157.173.221.192').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'imagekit',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_filters',
    
    # Local apps
    'accounts',
    'core',
    'puja',
    'astrology',
    'promo',
    'cart',
    'booking',
    'payment',
    'blog',
    'cms',
    'gallery',
    'misc',
    'db_manager',  # Database backup/restore app
    'corsheaders',
    'rest_framework_simplejwt.token_blacklist'
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# The name of the root URLconf module.
ROOT_URLCONF = 'okpuja_backend.urls'

# configure CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://www.okpuja.com",
    "https://okpuja.com",
    "https://api.okpuja.com",
    "https://okpuja.in", 
    "https://www.okpuja.in"
]

# Additional CORS settings to fix frontend issues
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'X-CSRFToken']
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma'
]

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
            ],
        },
    },
]

WSGI_APPLICATION = 'okpuja_backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Email Configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'okpuja108@gmail.com')

# SMS Configuration
# Use Twilio backend if credentials are provided, otherwise default to console
if os.getenv('TWILIO_ACCOUNT_SID'):
    SMS_BACKEND = 'accounts.sms.backends.twilio.SMSBackend'
else:
    SMS_BACKEND = 'accounts.sms.backends.console.SMSBackend'

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

# ImageKit
IMAGEKIT_PUBLIC_KEY = os.getenv('IMAGEKIT_PUBLIC_KEY', '')
IMAGEKIT_PRIVATE_KEY = os.getenv('IMAGEKIT_PRIVATE_KEY', '')
IMAGEKIT_URL_ENDPOINT = os.getenv('IMAGEKIT_URL_ENDPOINT', '')

# OTP Configuration
OTP_EXPIRE_MINUTES = int(os.getenv('OTP_EXPIRE_MINUTES', 15))
OTP_LENGTH = int(os.getenv('OTP_LENGTH', 6))

# Production server flag
PRODUCTION_SERVER = os.getenv('PRODUCTION_SERVER', 'False') == 'True'

# PhonePe Payment Gateway Configuration (V2 API)
PHONEPE_ENV = os.getenv('PHONEPE_ENV', 'UAT')  # UAT for testing, PRODUCTION for live

# V2 API Credentials
PHONEPE_CLIENT_ID = os.getenv('PHONEPE_CLIENT_ID', '')
PHONEPE_CLIENT_SECRET = os.getenv('PHONEPE_CLIENT_SECRET', '')
PHONEPE_CLIENT_VERSION = os.getenv('PHONEPE_CLIENT_VERSION', '1')

# V1 Legacy Credentials (kept for backward compatibility)
PHONEPE_MERCHANT_ID = os.getenv('PHONEPE_MERCHANT_ID', '')
PHONEPE_MERCHANT_KEY = os.getenv('PHONEPE_MERCHANT_KEY', '')
PHONEPE_SALT_INDEX = int(os.getenv('PHONEPE_SALT_INDEX', 1))

# PhonePe API URLs (V2)
PHONEPE_AUTH_BASE_URL = os.getenv('PHONEPE_AUTH_BASE_URL', 'https://api-preprod.phonepe.com/apis/pg-sandbox')
PHONEPE_PAYMENT_BASE_URL = os.getenv('PHONEPE_PAYMENT_BASE_URL', 'https://api-preprod.phonepe.com/apis/pg-sandbox')

# Legacy V1 base URL
if PHONEPE_ENV == 'PRODUCTION':
    PHONEPE_BASE_URL = 'https://api.phonepe.com/apis/hermes'
else:
    PHONEPE_BASE_URL = 'https://api-preprod.phonepe.com/apis/hermes'

# PhonePe URLs
PHONEPE_REDIRECT_URL = os.getenv('PHONEPE_REDIRECT_URL', 'http://localhost:8000/api/payments/webhook/phonepe/')
PHONEPE_CALLBACK_URL = os.getenv('PHONEPE_CALLBACK_URL', 'http://localhost:8000/api/payments/webhook/phonepe/')
PHONEPE_FAILED_REDIRECT_URL = os.getenv('PHONEPE_FAILED_REDIRECT_URL', 'http://localhost:3000/failedbooking')
PHONEPE_SUCCESS_REDIRECT_URL = os.getenv('PHONEPE_SUCCESS_REDIRECT_URL', 'http://localhost:3000/confirmbooking/')

# Frontend Base URL
FRONTEND_BASE_URL = os.getenv('FRONTEND_BASE_URL', 'http://localhost:3000')


# Documentation
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
}

# Admin Seed Config
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@okpuja.com')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin@123')

# Employee Registration Code (set this in your .env for security)
EMPLOYEE_REGISTRATION_CODE = os.getenv('EMPLOYEE_REGISTRATION_CODE', 'EMP2025OK5')

# Database Backup Configuration
DB_BACKUP_STORAGE_TYPE = os.getenv('DB_BACKUP_STORAGE_TYPE', 'LOCAL')  # LOCAL, GDRIVE, SYSTEM
DB_BACKUP_PATH = os.getenv('DB_BACKUP_PATH', 'backups/')
DB_BACKUP_RETENTION_DAYS = int(os.getenv('DB_BACKUP_RETENTION_DAYS', 7))
DB_BACKUP_MAX_FILES = int(os.getenv('DB_BACKUP_MAX_FILES', 10))
DB_BACKUP_AUTO_ENABLED = os.getenv('DB_BACKUP_AUTO_ENABLED', 'True') == 'True'
