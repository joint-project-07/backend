from rest_framework import serializers

from shelters.models import Shelter


class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"
        model = Shelter
