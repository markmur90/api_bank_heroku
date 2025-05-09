import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Configuración de seguridad
SECRET_KEY = 'django-insecure-z*_hrh0ssiq1s5t=dqe5_c6@qfb(fhb!+ruqnvu$mxi4$*m0s4'
DEBUG = False
ALLOWED_HOSTS = ['localhost', '0.0.0.0', '127.0.0.1']
ORIGIN = 'api-bank-heroku-72c443ab11d3.herokuapp.com'

# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_yasg',
    'rest_framework',
    'oauth2_provider',
    'rest_framework_simplejwt',
    'corsheaders',
    'debug_toolbar',
    'rest_framework.authtoken',
    'markdownify',
    # 'api.accounts',
    # 'api.collection',
    # 'api.transactions',
    'api.transfers',
    'api.core',
    'api.authentication',
    # 'api.sandbox',
    # 'api.sct',
    # 'api.sepa_payment',
    # 'api.gpt',
    'api.gpt3',
    'api.gpt4',
]

# Middleware
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    "api.middleware.ExceptionLoggingMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.core.middleware.CurrentUserMiddleware',
]

# URL and WSGI configuration
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Templates
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



import dj_database_url

DATABASE_HEROKU = {
	'default': dj_database_url.config()
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Databases
DATABASE_SQLITE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

DATABASE_PSQL = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydatabase',
        'USER': 'markmur88',
        'PASSWORD': 'Ptf8454Jd55',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
DATABASES = DATABASE_PSQL


# Authentication
AUTH_USER_MODEL = 'authentication.CustomUser'
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

# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_TMP = os.path.join(BASE_DIR, 'static')

os.makedirs(STATIC_TMP, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://api.db.com",
    "https://api-bank-heroku-72c443ab11d3.herokuapp.com",
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
        #'rest_framework.permissions.AllowAny',
        
    ),
}

# OAuth2 and JWT
OAUTH2_PROVIDER = {
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    'OIDC_ENABLED': True,
}


OAUTH2 = {
    'CLIENT_ID': 'ynCsnS3WA2dQtvlDBttYpv51goAzlSMUxSLGxHEO',
    'CLIENT_SECRET': 'pbkdf2_sha256$870000$KBmduLQnMQdWI9gAjKMBMs$Ih40gPHNYMupc6H5N+k+JsDT2erKQdvpXz9RmDC20KA=',
    'TOKEN_URL': 'https://api.db.com:443/gw/oidc/token',
    'AUTHORIZE_URL': 'https://api.db.com:443/gw/oidc/authorize',
    'REDIRECT_URI': 'https://api-bank-heroku-72c443ab11d3.herokuapp.com/oauth2/callback',
    'SCOPE': 'sepa_credit_transfers',
    'TIMEOUT': 10,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": 'Ptf8454Jd55',
    "VERIFYING_KEY": 'Ptf8454Jd55',
    "AUTH_HEADER_TYPES": ("Bearer",),
}


# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "errors.log"),
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {"handlers": ["file", "console"], "level": "WARNING", "propagate": True},
        "bank_services": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
    },
}

SANDBOX_API_URL = os.getenv("SANDBOX_API_URL")
API_KEY = os.getenv("API_KEY")

LOGIN_URL = '/login/'

import os

ACCESS_TOKEN = {
    "refresh": os.getenv("REFRESH_TOKEN"),
    "access": os.getenv("ACCESS_TOKEN"),
}

# Session expiration settings
#SESSION_COOKIE_AGE = 1800  # 30 minutes in seconds
SESSION_COOKIE_AGE = 1800  # 30 minutes in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Configure Django App for Heroku.
import django_heroku
django_heroku.settings(locals())




# settings.py
COD_01 = '27CDBFRDE17BEH'
COD_02 = 'DEUT27CDBFRDE17BEH'
COD_03 = 'IMAD-20250427-001'
COD_04 = 'JEtg1v94VWNbpGoFwqiWxRR92QFESFHGHdwFiHvc'
COD_05 = 'SE0IWHFHJFHB848R9E0R9FRUFBCJHW0W9FHF008E88W0457338ASKH64880'
COD_06 = 'H858hfhg0ht40588hhfjpfhhd9944940jf'
COD_07 = '090512DEUTDEFFXXX886479'
COD_08 = 'DE0005140008'
COD_09 = 'DE86500700100925993805'
COD_10 = '25993805'
COD_11 = '0925993805'
COD_12 = '0105528001187'

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
TOKEN_URL = 'https://api.db.com:443/gw/oidc/token'
SCOPE = 'sepa_credit_transfers'
CLIENT_ID = COD_02
PRIVATE_KEY_PATH = BASE_DIR / 'certs' / 'client_key.pem'
KID = COD_03
TIMEOUT_REQUEST = 30