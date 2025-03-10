from .base import *

DEBUG = True

# JWT 설정 (개발 환경에 맞게 변경)
SIMPLE_JWT.update(
    {
        "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    }
)
