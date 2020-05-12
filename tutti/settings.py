import json
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', False)

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.').split(',')

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'members.apps.MembersConfig',  # members should be above contrib.admin so that it can override admin templates
    'ldapsync.apps.LdapSyncConfig',
    'oidc.apps.OIDCConfig',
    'pages.apps.PagesConfig',
    'aadsync.apps.AADSyncConfig',

    'django.contrib.admin',

    'phonenumber_field',
    'localflavor',
    'django_countries',
    'health_check',  # django-health-check
    'health_check.db',
    'health_check.storage',
    'import_export',  # django-import-export
    'pennotools.apps.PennotoolsConfig',
    'duqduqgo.apps.DuqduqgoConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tutti.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'tutti.context_processors.version_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'tutti.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.{}'.format(os.getenv('DATABASE_ENGINE', 'sqlite3')),
        'NAME': os.getenv('DATABASE_NAME', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.getenv('DATABASE_USERNAME', ''),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', '127.0.0.1'),
        'PORT': os.getenv('DATABASE_PORT', 5432),
        'OPTIONS': json.loads(os.getenv('DATABASE_OPTIONS', '{}')),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Amsterdam'
USE_I18N = False
USE_L10N = False
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend/dist'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = 'media'

AUTH_USER_MODEL = 'members.User'

LDAP = {
    'HOST': 'ldap://ds.esmgquadrivium.nl',  # Can be in URI form
    'USER': '',
    'PASSWORD': '',
    'START_TLS': True,
}

PHONENUMBER_DEFAULT_REGION = 'NL'

# OpenID Connect configuration

AUTHLIB_OAUTH_CLIENTS = {
    'keycloak': {
        'client_id': 'tutti',
        'client_secret': '',  # Needs to be set in deployment
    }
}

# When users need to be logged in, the OpenID Connect flow will be started by
# the login view.
LOGIN_URL = 'oidc:login'

# Poor man's version display.
#
# When set, will display in the footer something like: Last updated: today
VERSION_DATE = None  # Set to date value
VERSION_URL = ""  # Link to e.g. GitHub master branch


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('DJANGO_LOGLEVEL', 'info').upper(),
    },
}