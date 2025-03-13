from rest_framework import serializers

from histories.models import History
from recruitments.serializers import RecruitmentSerializer
from shelters.models import Shelter


class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ["name", "region", "address"]


class HistorySerializer(serializers.ModelSerializer):
    shelter = ShelterSerializer()
    recruitment = RecruitmentSerializer()

    class Meta:
        model = History
        fields = ["id", "recruitment", "shelter", "rating"]


class HistoryRatingSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = History
        fields = "__all__"
