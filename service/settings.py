"""
Django settings for service project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'b_31oxxpj%x00znw!msfnzt=r$ra9$a+6nl6$fdwm2+evcimtl'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '*'
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'service.api',
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

ROOT_URLCONF = 'service.urls'

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

WSGI_APPLICATION = 'service.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'gnosis',
        'USER': 'gnosis',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

FUNDING_ACCOUNT_PHRASE = os.environ.get('FUNDING_ACCOUNT_PHRASE')

# Google settings

ANDROID_SUBSCRIPTION_ID = os.environ.get('ANDROID_SUBSCRIPTION_ID', 'pm.gnosis.heimdall.dev.transaction_execution_rinkeby_1')
ANDROID_PRODUCT_ID = os.environ.get('ANDROID_PRODUCT_ID', 'pm.gnosis.heimdall.dev.100_transaction_executions_rinkeby_1')
PRODUCT_CREDITS = int(os.environ.get('PRODUCT_CREDITS', '50'))
MAX_CREDITS = int(os.environ.get('MAX_CREDITS', '100'))
GOOGLE_ANDROID_PACKAGE = 'pm.gnosis.heimdall.dev'
GOOGLE_SUBSCRIPTIONS_ENDPOINT = 'https://www.googleapis.com/androidpublisher/v2/applications/%s/purchases/subscriptions/%s/tokens/%s'
GOOGLE_PRODUCTS_ENDPOINT = 'https://www.googleapis.com/androidpublisher/v2/applications/%s/purchases/products/%s/tokens/%s'
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')
DEFAULT_GAS_PRICE = int(os.environ.get('DEFAULT_GAS_PRICE', '100000000'))
GAS_PER_CREDIT = int(os.environ.get('GAS_PER_CREDIT', '60000'))
GOOGLE_SCOPE = 'https://www.googleapis.com/auth/androidpublisher'