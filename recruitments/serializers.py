from rest_framework import serializers

from .models import Recruitment


class RecruitmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = [
            "id",
            "shelter",
            "date",
            "start_time",
            "end_time",
            "type",
            "description",  # ✅ 선택형 필드 적용됨
            "supplies",
            "status",
        ]


class RecruitmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = [
            "date",
            "start_time",
            "end_time",
            "type",
            "description",
            "supplies",
            "status",
        ]
