"""
Django base settings for MultiBook booking system.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import os
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Relax oauthlib scope check for Google OAuth (avoids "Scope has changed" when Google
# returns scopes in different order or with include_granted_scopes)
os.environ.setdefault('OAUTHLIB_RELAX_TOKEN_SCOPE', '1')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost', '127.0.0.1',
    '13.135.109.229', 'ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
])

# Application definition
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    
    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.services',
    'apps.staff',
    'apps.customers',
    'apps.appointments',
    'apps.payments',
    'apps.subscriptions',
    'apps.orders',
    'apps.notifications',
    'apps.calendar_sync',
    'apps.coupons',
    'apps.reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.AuthenticationMiddleware',  # Custom authentication middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Note: RoleBasedAccessMiddleware is optional and can be enabled if needed
    # 'apps.core.middleware.RoleBasedAccessMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/London'  # UK timezone
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'
# For now, using Django's default User model

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(env('JWT_ACCESS_TOKEN_LIFETIME', default=15))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(env('JWT_REFRESH_TOKEN_LIFETIME', default=7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Cache: default LocMem; production overrides with Redis when REDIS_URL is set
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'OPTIONS': {'MAX_ENTRIES': 2000},
    }
}

# CORS Settings (for Next.js frontend on localhost:3000 and EC2 test server)
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://13.135.109.229',
    'https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
    'http://13.135.109.229',
    'http://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
])
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False  # Set to True only in development

# API Documentation (Swagger/OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'MultiBook Booking System API',
    'DESCRIPTION': '''
    MultiBook Booking System REST API
    
    This API provides endpoints for:
    - Service and staff management
    - Appointment booking (with guest checkout support)
    - Customer management
    - Authentication and authorization
    - Subscriptions and orders
    
    **API Version:** 1.0.0
    
    **Security:**
    - Public endpoints: /api/svc/, /api/stf/, /api/bkg/, /api/aut/, /api/slots/
    - Protected endpoints: /api/cus/, /api/st/, /api/man/, /api/ad/
    - Authentication: JWT Bearer tokens
    
    **Documentation:**
    - Swagger UI: /api/docs/
    - ReDoc: /api/redoc/
    - OpenAPI Schema: /api/schema/
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and authorization'},
        {'name': 'Services', 'description': 'Service and category management'},
        {'name': 'Staff', 'description': 'Staff member management'},
        {'name': 'Customers', 'description': 'Customer management'},
        {'name': 'Appointments', 'description': 'Appointment booking and management'},
        {'name': 'Bookings', 'description': 'Public booking endpoints (guest checkout supported)'},
        {'name': 'Subscriptions', 'description': 'Subscription management'},
        {'name': 'Orders', 'description': 'Order management'},
    ],
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Development server'},
    ],
}

# Frontend URL (for email links)
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')

# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')

# Payment Gateways
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')

PAYPAL_CLIENT_ID = env('PAYPAL_CLIENT_ID', default='')
PAYPAL_CLIENT_SECRET = env('PAYPAL_CLIENT_SECRET', default='')
PAYPAL_MODE = env('PAYPAL_MODE', default='sandbox')  # or 'live'

# Google Services
# Note: GOOGLE_MAPS_API_KEY and GOOGLE_PLACES_API_KEY can use the same API key
# The same API key works for both Geocoding API and Places API
GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY', default='')
GOOGLE_PLACES_API_KEY = env('GOOGLE_PLACES_API_KEY', default='')
# If GOOGLE_MAPS_API_KEY is set but GOOGLE_PLACES_API_KEY is not, use GOOGLE_MAPS_API_KEY
if not GOOGLE_PLACES_API_KEY and GOOGLE_MAPS_API_KEY:
    GOOGLE_PLACES_API_KEY = GOOGLE_MAPS_API_KEY
# If GOOGLE_PLACES_API_KEY is set but GOOGLE_MAPS_API_KEY is not, use GOOGLE_PLACES_API_KEY
if not GOOGLE_MAPS_API_KEY and GOOGLE_PLACES_API_KEY:
    GOOGLE_MAPS_API_KEY = GOOGLE_PLACES_API_KEY

# Google OAuth (separate credentials for login and calendar)
# Login/Authentication credentials (from first OAuth client)
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET', default='')

# Google Calendar OAuth credentials (from Calendar API OAuth client - separate)
GOOGLE_CALENDAR_CLIENT_ID = env('GOOGLE_CALENDAR_CLIENT_ID', default=env('GOOGLE_CLIENT_ID', default=''))
GOOGLE_CALENDAR_CLIENT_SECRET = env('GOOGLE_CALENDAR_CLIENT_SECRET', default=env('GOOGLE_CLIENT_SECRET', default=''))

# Google OAuth Redirect URIs
# For login/authentication
GOOGLE_OAUTH_REDIRECT_URI = env('GOOGLE_OAUTH_REDIRECT_URI', default='http://localhost:8000/api/aut/google/callback/')
# For calendar sync
GOOGLE_REDIRECT_URI = env('GOOGLE_REDIRECT_URI', default='http://localhost:8000/api/calendar/google/callback/')

# Microsoft Services (Outlook Calendar)
MICROSOFT_CLIENT_ID = env('MICROSOFT_CLIENT_ID', default='')
MICROSOFT_CLIENT_SECRET = env('MICROSOFT_CLIENT_SECRET', default='')

# Supabase (DB via DATABASE_URL in dev/prod; API for auth/storage)
SUPABASE_URL = env('SUPABASE_URL', default='')
SUPABASE_ANON_KEY = env('SUPABASE_ANON_KEY', default='')
SUPABASE_SERVICE_ROLE_KEY = env('SUPABASE_SERVICE_ROLE_KEY', default='')
SUPABASE_JWT_SECRET = env('SUPABASE_JWT_SECRET', default='')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',  # Suppress template debug errors (404 page template issues)
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
# Ensure logs directory exists so file handler does not raise FileNotFoundError
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Security Settings (Production)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
