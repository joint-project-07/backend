from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True
    )  # 응답에서 숨김(비밀번호는 요청에서만 사용)

    class Meta:
        pass
