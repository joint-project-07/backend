from rest_framework import serializers

from applications.models import Application
from recruitments.models import Recruitment
from shelters.models import Shelter
from users.serializers import UserSerializer


class ApplicationRecruitmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = ["id", "date", "start_time", "end_time", "status", "type", "supplies"]


class ApplicationShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ["id", "name", "region", "address"]


class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    recruitment = ApplicationRecruitmentSerializer(read_only=True)
    shelter = ApplicationShelterSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ["id", "user", "recruitment", "shelter", "status", "rejected_reason"]


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["recruitment", "shelter"]

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        application = Application.objects.create(user=user, **validated_data)
        return application


class ApplicationRejectSerializer(serializers.Serializer):
    rejected_reason = serializers.CharField(max_length=255, required=True)
