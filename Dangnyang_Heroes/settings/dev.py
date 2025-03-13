from .base import *

DEBUG = True


# drf_spectacular 추가
INSTALLED_APPS += [
    "drf_spectacular",
]


# JWT 설정 (개발 환경에 맞게 변경)
SIMPLE_JWT.update(
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    }
)

REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"


SPECTACULAR_SETTINGS = {
    "TITLE": "Your Project API",
    "DESCRIPTION": "Your project description",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "http", "scheme": "bearer",'bearerFormat': "JWT"}
    },
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,  # 인증 정보 유지
    },
    'AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # OTHER SETTINGS
}
