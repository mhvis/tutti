import email.utils
import os

import environ

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
environ.Env.read_env(env_file=str(os.path.join(BASE_DIR, ".env")))

SECRET_KEY = env.str('DJANGO_SECRET_KEY')
if env.str("DJANGO_SECRET_KEY_FILE", None):
    with open(os.getenv("DJANGO_SECRET_KEY_FILE")) as f:
        SECRET_KEY = f.read()

DEBUG = env.bool('DJANGO_DEBUG', default=False)

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1').split(',')

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
    # We're using WhiteNoise for the static files
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'tutti.wsgi.application'

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}
DATABASES["default"]["CONN_MAX_AGE"] = 3600
if env.str("DATABASE_PASSWORD_FILE", None):
    with open(env.str("DATABASE_PASSWORD_FILE")) as f:
        DATABASES["default"]["PASSWORD"] = f.read()

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
# We're using WhiteNoise in production
STATIC_ROOT = os.getenv('DJANGO_STATIC_ROOT', None)
if os.getenv('DJANGO_WHITENOISE', None):
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('DJANGO_MEDIA_ROOT', None)

AUTH_USER_MODEL = 'members.User'

# LDAP settings
LDAP = {
    'HOST': os.getenv('DJANGO_LDAP_HOST', ''),  # Can be in URI form
    'USER': os.getenv('DJANGO_LDAP_USER', ''),
    'PASSWORD': os.getenv('DJANGO_LDAP_PASSWORD', ''),
    'START_TLS': True,
}
if os.getenv("DJANGO_LDAP_PASSWORD_FILE", None):
    with open(os.getenv("DJANGO_LDAP_PASSWORD_FILE")) as f:
        LDAP["PASSWORD"] = f.read()


PHONENUMBER_DEFAULT_REGION = 'NL'

# Keycloak OpenID Connect configuration
AUTHLIB_OAUTH_CLIENTS = {
    'keycloak': {
        'client_id': 'tutti',
        # If unset, OIDC will not be used
        'client_secret': os.getenv('DJANGO_KEYCLOAK_SECRET', ''),
    }
}
if os.getenv("DJANGO_KEYCLOAK_SECRET_FILE", None):
    with open(os.getenv("DJANGO_KEYCLOAK_SECRET_FILE")) as f:
        AUTHLIB_OAUTH_CLIENTS["keycloak"]["client_secret"] = f.read()

# When users need to be logged in, the OpenID Connect flow will be started by
# the login view.
LOGIN_URL = 'oidc:login'

# Logging to console as that's common for containers.
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

# E-mail settings
EMAIL_CONFIG = env.email_url("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)
SERVER_EMAIL = os.getenv('DJANGO_SERVER_EMAIL', 'root@localhost')
DEFAULT_FROM_EMAIL = os.getenv('DJANGO_DEFAULT_FROM_EMAIL', 'webmaster@localhost')
# E-mail address string where 5xx errors are sent, e.g. 'Me <my@address.net>, Someone Else <his@address.com>'
ADMINS = email.utils.getaddresses([env.str('DJANGO_ADMINS', default='')])

# Ensure cookies over HTTPS
if os.getenv('DJANGO_COOKIE_SECURE', False):
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# Nginx proxy settings (only effective in production environment)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
