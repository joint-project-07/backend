"""
Django settings for Dangnyang_Heroes project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from datetime import timedelta
from pathlib import Path

import environ

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# base.py 기준으로 루트 디렉토리의 위치를 지정
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# 사용할 환경 설정 파일 결정
ENV_MODE = os.getenv("DJANGO_ENV", "")
ENV_FILE = BASE_DIR / f".envs/{ENV_MODE}.env"

# 환경 변수 파일 로드
if os.path.exists(ENV_FILE):
    env.read_env(str(ENV_FILE))

SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise ValueError("SECRET_KEY environment variable is not set.")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS: list[str] = ["*"]


# Application definition

INSTALLED_APPS = [
    "storages",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "histories",
    "applications",
    "users",
    "shelters",
    "recruitments",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",  # 블랙리스트 기능 추가
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Dangnyang_Heroes.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Dangnyang_Heroes.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = []

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

# 이메일 설정
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")  # 예시로 Gmail을 사용
EMAIL_PORT = 587  # Gmail의 기본 SMTP 포트
EMAIL_USE_TLS = True  # TLS 사용
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")  # 이메일 발송자 (환경변수로 설정)
EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD"
)  # 이메일 비밀번호 (환경변수로 설정)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER  # 기본 발신자 이메일


AWS_ACCESS_KEY_ID = os.getenv("NCP_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("NCP_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("NCP_BUCKET_NAME")
AWS_S3_REGION_NAME = "kr-standard"
AWS_S3_ENDPOINT_URL = "https://kr.object.ncloudstorage.com"
AWS_S3_DEFAULT_ACL = "public-read"
MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.kr.object.ncloudstorage.com/"

# NCP Object Storage 설정

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://223.130.151.137",
    "https://back.dietstory.shop",
    "https://www.dietstory.shop",
]

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)


CORS_ALLOW_ALL_ORIGINS = False

# Social
KAKAO_CLIENT_ID = (os.getenv("KAKAO_CLIENT_ID"),)
KAKAO_SECRET = (os.getenv("KAKAO_SECRET"),)
KAKAO_REDIRECT_URI = (os.getenv("KAKAO_REDIRECT_URI"),)

CSRF_TRUSTED_ORIGINS = ["https://back.dietstory.shop/", "https://localhost:3000/"]
CSRF_COOKIE_DOMAIN = ".dietstory.shop"
SESSION_COOKIE_DOMAIN = ".dietstory.shop"
