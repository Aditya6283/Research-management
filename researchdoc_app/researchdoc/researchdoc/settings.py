"""
Django settings.

This is one file but it does a lot — it's where Django learns about
our database, our apps, our middleware, our auth backends, our static
files, our LLM keys, and roughly a dozen other things. Sections below
are split with comment headers so you can jump around.

Anything that varies between dev and prod (DEBUG, secret key, API
keys, DB password, etc.) is read from environment variables — the
.env file in the project root is what python-dotenv picks up locally.
See .env.example for the full list of variables.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from a .env file (Applied Class 7 pattern)
load_dotenv()


# Security

# Never commit a real secret key. Locally this falls back to an obviously
# insecure development key; in production DJANGO_SECRET_KEY is set in the
# systemd unit / environment so the real value never touches git.
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-only-key-set-DJANGO_SECRET_KEY-in-env',
)
# Nginx mounts the app at /researchdoc/ and strips that prefix before
# forwarding to gunicorn. FORCE_SCRIPT_NAME tells Django to add it back
# when generating URLs so links stay correct. Set to empty in .env for
# local runserver development (where there is no Nginx to strip the prefix).
FORCE_SCRIPT_NAME = os.getenv('FORCE_SCRIPT_NAME') or None

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

# Hosts allowed to serve the app (Applied Class 2)
ALLOWED_HOSTS = [
    h.strip() for h in os.getenv(
        'DJANGO_ALLOWED_HOSTS',
        'infs3202-3dfe6012.uqcloud.net,localhost,127.0.0.1',
    ).split(',') if h.strip()
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Django sites framework — required by allauth
    'django.contrib.sites',

    # django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # HTMX
    'django_htmx',

    # RESTful API
    'rest_framework',

    # Local apps
    'researchapp',
]

SITE_ID = 1

MIDDLEWARE = [
    'researchapp.middleware.ForceHTTPSScheme',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # HTMX middleware adds request.htmx attribute (Applied Class 7)
    'django_htmx.middleware.HtmxMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Allauth middleware — Applied Class 8
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'researchdoc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'researchdoc.wsgi.application'

# Database
# SQLite by default so the project runs locally with zero setup. Set
# MYSQL_PASSWORD (and optionally the other DB_* vars) in the environment
# to switch to MySQL, which is what the UQCloud deployment uses.
if os.getenv('MYSQL_PASSWORD'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'researchdoc_db'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('MYSQL_PASSWORD'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '3306'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Where Django redirects after login/logout
_prefix = FORCE_SCRIPT_NAME or ''  # e.g. '/researchdoc' on UQCloud, '' locally
LOGIN_URL = f'{_prefix}/accounts/login/'
LOGIN_REDIRECT_URL = f'{_prefix}/dashboard/'
LOGOUT_REDIRECT_URL = f'{_prefix}/' if _prefix else '/'
ACCOUNT_LOGOUT_REDIRECT_URL = f'{_prefix}/' if _prefix else '/'

# Allauth settings
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = [
    'username*', 'email*', 'password1*', 'password2*',
]
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True

# Wire the custom signup form (captures first/last name in addition to the
# default email/password/username fields).
ACCOUNT_FORMS = {
    'signup': 'researchapp.forms.CustomSignupForm',
}

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
}
# Google client_id and secret are stored in the database via the admin panel
# at /researchdoc/admin/socialaccount/socialapp/

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (Applied Class 6)
STATIC_URL = '/researchdoc_static/'
STATIC_ROOT = os.getenv('DJANGO_STATIC_ROOT', str(BASE_DIR / 'staticfiles'))

# Media files (user uploads)
MEDIA_URL = '/researchdoc_media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF — required for HTTPS on UQCloud
CSRF_TRUSTED_ORIGINS = [
    'https://*.uqcloud.net',
    'https://*.eait.uq.edu.au',
]


# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# Email backend
# In development we print emails to the console (no real SMTP needed).
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL', 'ResearchDoc <noreply@researchdoc.test>',
)

# File upload limits (25 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400

# LLM configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
