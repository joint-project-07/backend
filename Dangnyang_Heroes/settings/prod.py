from .base import *

DEBUG = False

# JWT 설정 (프로덕션 환경에 맞게 변경)
SIMPLE_JWT.update(
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    }
)

# 추가적인 보안 설정 (예: 쿠키 보안 설정)
REFRESH_TOKEN_COOKIE_SECURE = True
