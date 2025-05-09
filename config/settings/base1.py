import os
from pathlib import Path
import environ
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
# 1. Creamos el lector de .env
env = environ.Env()

# 2. Detectamos el entorno (por defecto 'local') y cargamos el .env correspondiente
DJANGO_ENV = os.getenv('DJANGO_ENV', 'production')
env_file = BASE_DIR / ('.env.production' if DJANGO_ENV == 'production' else '.env.development')
if not env_file.exists():
    raise ImproperlyConfigured(f'No se encuentra el archivo de entorno: {env_file}')
env.read_env(env_file)

# 3. Variables críticas
SECRET_KEY = env('SECRET_KEY')
DEBUG      = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

CLIENT_ID = env('CLIENT_ID')
SECRET_CLIENT = env('SECRET_CLIENT')
ACCESS_TOKEN = env('ACCESS_TOKEN')
ORIGIN = env('ORIGIN')
TOKEN_URL = env('TOKEN_URL')
OTP_URL = env('OTP_URL')
AUTH_URL = env('AUTH_URL')
API_URL = env('API_URL')
AUTHORIZE_URL = env('AUTHORIZE_URL')
REDIRECT_URI = env('REDIRECT_URI')
SCOPE = env('SCOPE')

# 4. Apps y middleware (sin cambios)
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

    'api.transfers',
    'api.core',
    'api.authentication',
    
    # 'api.transactions',

    # 'api.accounts',
    # 'api.collection',
    # 'api.sandbox',
    # 'api.sct',
    # 'api.sepa_payment',
    # 'api.gpt',

    'api.gpt3',
    'api.gpt4',
]

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


ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

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

# 4. DEBUG_TOOLBAR_SETTINGS (opcional, pero recomendado)
INTERNAL_IPS = [
    '127.0.0.1',
    '192.168.0.143'
    # añade aquí la IP de tu máquina si usas Docker o VM
]

# 5. Plantillas de base de datos
DATABASES = {
    'default': dj_database_url.config(default=env('DATABASE_URL'))
}
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# 6. Resto de configuración (sin cambios)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_TMP =os.path.join(BASE_DIR, 'static')
os.makedirs(STATIC_TMP, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

STATICFILES_DIRS = [STATIC_TMP]
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://api.db.com",
    "https://simulator-api.db.com",
    "https://api-bank-heroku-72c443ab11d3.herokuapp.com",
]

# REST Framework y OAuth/JWT (sin cambios)
from datetime import timedelta
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.AllowAny',),
}

OAUTH2_PROVIDER = {'ACCESS_TOKEN_EXPIRE_SECONDS': 3600, 'OIDC_ENABLED': True}

OAUTH2 = {
    'CLIENT_ID': CLIENT_ID,
    'CLIENT_SECRET': SECRET_CLIENT,
    'TOKEN_URL': TOKEN_URL,
    'AUTHORIZE_URL': AUTHORIZE_URL,
    'REDIRECT_URI': REDIRECT_URI,
    'SCOPE': 'openid sepa_credit_transfers',
    'TIMEOUT': 10,
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env('JWT_SIGNING_KEY', default=''),
    "VERIFYING_KEY": env('JWT_VERIFYING_KEY', default=''),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# Logging (sin cambios)
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
            "filename": BASE_DIR / "logs" / "errors.log",
            "formatter": "verbose",
        },
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "django": {"handlers": ["file", "console"], "level": "WARNING", "propagate": True},
        "bank_services": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
    },
}

LOGIN_URL = '/login/'
SESSION_COOKIE_AGE = 300
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

# Configure Django App for Heroku.
import django_heroku
django_heroku.settings(locals())