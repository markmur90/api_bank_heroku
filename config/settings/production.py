from .base1 import *

from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

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






