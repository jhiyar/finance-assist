"""
Django settings for finance_assist project.
"""

from pathlib import Path
import os
from decouple import config

# Using default MySQL client (mysqlclient)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'chat',
    'document_processing',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'finance_assist.urls'

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

WSGI_APPLICATION = 'finance_assist.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# Database configuration - use different databases for local vs production
import os

if os.getenv('DB_HOST'):
    # Check if PostgreSQL is configured (production)
    if os.getenv('DB_ENGINE') == 'postgresql':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DB_NAME', 'finance_assist'),
                'USER': os.getenv('DB_USER', 'postgres'),
                'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
                'HOST': os.getenv('DB_HOST', 'localhost'),
                'PORT': os.getenv('DB_PORT', '5432'),
            }
        }
    else:
        # Use MySQL for local development
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': os.getenv('DB_NAME', 'finance_assist'),
                'USER': os.getenv('DB_USER', 'finance_user'),
                'PASSWORD': os.getenv('DB_PASSWORD', 'finance_password'),
                'HOST': os.getenv('DB_HOST', 'db'),
                'PORT': os.getenv('DB_PORT', '3306'),
                'OPTIONS': {
                    'charset': 'utf8mb4',
                },
            }
        }
else:
    # Use SQLite for AWS App Runner deployment if no database is configured
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# URL settings
APPEND_SLASH = False

# Watson AI configuration removed - using OpenAI only

# OpenAI API Configuration
# Read from environment variable first, then fall back to config/decouple
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or config('OPENAI_API_KEY', default='')
OPENAI_MODEL_NAME = os.getenv('OPENAI_MODEL_NAME') or config('OPENAI_MODEL_NAME', default='gpt-3.5-turbo')
OPENAI_EMBEDDING_MODEL = os.getenv('OPENAI_EMBEDDING_MODEL') or config('OPENAI_EMBEDDING_MODEL', default='text-embedding-3-small')
OPENAI_TEMPERATURE = os.getenv('OPENAI_TEMPERATURE') or config('OPENAI_TEMPERATURE', default='0.1')
OPENAI_MAX_TOKENS = os.getenv('OPENAI_MAX_TOKENS') or config('OPENAI_MAX_TOKENS', default='4096')

# AI Service Configuration
AI_SERVICE_PROVIDER = 'openai'  # Using OpenAI only

# Document Processing Configuration
UNSTRUCTURED_API_KEY = config('UNSTRUCTURED_API_KEY', default='')
LLAMAPARSE_API_KEY = config('LLAMAPARSE_API_KEY', default='')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
