import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5_gj%^ok#l6#rw@03qondoll)9@zw6jocnvi&x9@ktsvie$=yo'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'mozilla_django_oidc',
    'phonenumber_field',
    'localflavor',
    'django_countries',

    'members.apps.MembersConfig',
    # 'ldapproxy.apps.LdapProxyConfig'
    # 'ldapserver.apps.LdapServerConfig'
    'ldapsync.apps.LdapSyncConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Checks for OpenID Connect token expiry (e.g. when account is removed)
    'mozilla_django_oidc.middleware.SessionRefresh',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tutti.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'

AUTH_USER_MODEL = 'members.User'

LDAP = {
    'HOST': 'ldap://ds.esmgquadrivium.nl',  # Can be in URI form
    'USER': '',
    'PASSWORD': '',
    'START_TLS': True,
}

PHONENUMBER_DEFAULT_REGION = 'NL'

# OpenID Connect settings, see https://mozilla-django-oidc.readthedocs.io
# These are currently configured for Keycloak
OIDC_RP_CLIENT_ID = 'tutti'
OIDC_RP_CLIENT_SECRET = 'd3083693-9f01-480e-941b-e0d2be32651e'  # SET IN DEPLOYMENT
OIDC_OP_AUTHORIZATION_ENDPOINT = "https://keycloak.esmgquadrivium.nl/auth/realms/esmgquadrivium/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = "https://keycloak.esmgquadrivium.nl/auth/realms/esmgquadrivium/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = "https://keycloak.esmgquadrivium.nl/auth/realms/esmgquadrivium/protocol/openid-connect/userinfo"
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_OP_JWKS_ENDPOINT = 'https://keycloak.esmgquadrivium.nl/auth/realms/esmgquadrivium/protocol/openid-connect/certs'
OIDC_CREATE_USER = False  # Do not create non-existing users

AUTHENTICATION_BACKENDS = [
    'members.oidc.MyOIDCAB',
    'django.contrib.auth.backends.ModelBackend',
]

# When users need to be logged in, they'll get send to OIDC
LOGIN_URL = 'oidc_authentication_init'
# LOGIN_REDIRECT_URL = "/"
# LOGOUT_REDIRECT_URL = "/"
