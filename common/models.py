from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 업데이트 시간

    class Meta:
        abstract = True  # 이 모델은 테이블이 생성되지 않음 (공통 상속용)
