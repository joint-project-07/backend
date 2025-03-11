from rest_framework import serializers

from applications.models import Application
from users.serializers import UserSerializer
from recruitments.serializers import RecruitmentSerializer
from shelters.serializers import ShelterSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    recruitment = RecruitmentSerializer(read_only=True)
    shelter = ShelterSerializer(read_only=True)

    class Meta:
        model = Application
        fields = "__all__"


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["recruitment", "shelter"]

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        application = Application.objects.create(user=user, **validated_data)
        return application
