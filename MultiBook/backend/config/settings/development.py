"""
Django development settings for MultiBook booking system.
Uses PostgreSQL database if DATABASE_URL is set, otherwise SQLite.
"""

from .base import *

# Debug mode enabled in development
DEBUG = True

# Allow all hosts in development (include EC2 test server so we can test at 13.135.109.229)
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '13.135.109.229',
    'ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
]

# Database - PostgreSQL if DATABASE_URL is set (e.g. Supabase), otherwise SQLite
database_url = env('DATABASE_URL', default=None)
if database_url and database_url.startswith('postgresql://'):
    import re
    from urllib.parse import unquote
    # Parse postgresql://user:password@host:port/dbname (password may be URL-encoded, e.g. %40 for @)
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/([^?\s]*)', database_url)
    if match:
        db_name = match.group(5).split('?')[0]  # strip query params if present
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': match.group(1),
                'PASSWORD': unquote(match.group(2)),  # URL-decode for Supabase/special chars
                'HOST': match.group(3),
                'PORT': match.group(4),
                'OPTIONS': {'connect_timeout': 10},
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': env('DB_NAME', default='postgres'),
                'USER': env('DB_USER', default='postgres'),
                'PASSWORD': env('DB_PASSWORD', default=''),
                'HOST': env('DB_HOST', default='localhost'),
                'PORT': env('DB_PORT', default='5432'),
            }
        }
else:
    # Use SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# CORS - Allow all origins in development (for local testing)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://13.135.109.229',
    'https://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
    'http://13.135.109.229',
    'http://ec2-13-135-109-229.eu-west-2.compute.amazonaws.com',
]
CORS_ALLOW_CREDENTIALS = True
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
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Email backend - Use SMTP if configured in .env, otherwise console for development
# If EMAIL_HOST is set in .env, use SMTP; otherwise use console backend
if env('EMAIL_HOST', default=''):
    # SMTP configured in .env - use it
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    # No email config in .env - use console backend for development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files served by Django in development
# In production, these should be served by a web server
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files served by Django in development
# In production, these should be served by a web server or S3

# Logging - More verbose in development
LOGGING['loggers']['apps']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'

# Django Debug Toolbar (optional, install if needed)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Disable security settings for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
