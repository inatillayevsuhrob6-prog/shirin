from pathlib import Path
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / '.env')
SECRET_KEY = os.getenv('SECRET_KEY', 'development-only-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = [x.strip() for x in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')]
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','corsheaders','rest_framework','store']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware','django.middleware.security.SecurityMiddleware','whitenoise.middleware.WhiteNoiseMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
FORCE_SCRIPT_NAME = os.getenv('FORCE_SCRIPT_NAME') or None
DATABASE_URL = os.getenv('DATABASE_URL','')
if DATABASE_URL.startswith(('postgresql://','postgres://')):
    database_url = DATABASE_URL.replace('postgres://','postgresql://',1)
    parsed=urlparse(database_url)
    DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':parsed.path.lstrip('/'),'USER':parsed.username,'PASSWORD':parsed.password,'HOST':parsed.hostname,'PORT':parsed.port or 5432,'CONN_MAX_AGE':600}}
else:
    DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
STATIC_URL=f'{FORCE_SCRIPT_NAME}/static/' if FORCE_SCRIPT_NAME else '/static/'
STATIC_ROOT=BASE_DIR/'staticfiles'
STATICFILES_DIRS=[BASE_DIR/'static']
STORAGES={'staticfiles':{'BACKEND':'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
MEDIA_URL=f'{FORCE_SCRIPT_NAME}/media/' if FORCE_SCRIPT_NAME else '/media/'
MEDIA_ROOT=BASE_DIR/'media'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LANGUAGE_CODE='uz'
TIME_ZONE='Asia/Tashkent'
USE_I18N=True
USE_TZ=True
CORS_ALLOW_ALL_ORIGINS=DEBUG
REST_FRAMEWORK={'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.AllowAny'],'DEFAULT_THROTTLE_RATES':{'anon':'60/minute'}}
CELERY_BROKER_URL=os.getenv('REDIS_URL','redis://localhost:6379/0')
CELERY_RESULT_BACKEND=CELERY_BROKER_URL
