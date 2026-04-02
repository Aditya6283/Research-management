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

