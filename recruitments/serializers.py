from rest_framework import serializers

from recruitments.models import Recruitment


class RecruitmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = "__all__"
