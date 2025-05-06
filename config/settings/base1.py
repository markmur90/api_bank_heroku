import os
from pathlib import Path
import environ
from django.core.exceptions import ImproperlyConfigured
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 1. Creamos el lector de .env
env = environ.Env()

# 2. Detectamos el entorno (por defecto 'local') y cargamos el .env correspondiente
DJANGO_ENV = os.getenv('DJANGO_ENV', 'local')
env_file = BASE_DIR / ('.env.production' if DJANGO_ENV == 'production' else '.env')
if not env_file.exists():
    raise ImproperlyConfigured(f'No se encuentra el archivo de entorno: {env_file}')
env.read_env(env_file)

# 3. Variables críticas
SECRET_KEY = env('SECRET_KEY')
DEBUG      = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# 4. Apps y middleware (sin cambios)
INSTALLED_APPS_FIJO = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
INSTALLED_APPS_ADS = [
    'drf_yasg',
    'rest_framework',
    'oauth2_provider',
    'rest_framework_simplejwt',
    'corsheaders',
    'debug_toolbar',
    'rest_framework.authtoken',
    'markdownify',
]
INSTALLED_APPS_API = [
    'api.accounts',
    'api.collection',
    'api.transfers',
    'api.core',
    'api.authentication',
    'api.sandbox',
    'api.sct',
    'api.sepa_payment',
    'api.gpt',
    'api.gpt3',
    'api.gpt4',
]
INSTALLED_APPS = INSTALLED_APPS_FIJO + INSTALLED_APPS_ADS + INSTALLED_APPS_API

MIDDLEWARE_FIJO = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
MIDDLEWARE_API = [
    "api.middleware.ExceptionLoggingMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    'api.core.middleware.CurrentUserMiddleware',
]
MIDDLEWARE = MIDDLEWARE_FIJO + MIDDLEWARE_API

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# 5. Plantillas de base de datos
DATABASES_PG = {
    'default': dj_database_url.config(default=env('DATABASE_URL'))
}
DATABASES_LOCAL = {
    'default': {
        'ENGINE':   env('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME':     env('DB_NAME', default=''),
        'USER':     env('DB_USER', default=''),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST':     env('DB_HOST', default='localhost'),
        'PORT':     env('DB_PORT', default='5432'),
    }
}

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
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_TMP = BASE_DIR / 'static'
os.makedirs(STATIC_TMP, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)
STATICFILES_DIRS = [STATIC_TMP]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

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
SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
