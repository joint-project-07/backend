from rest_framework import serializers

from histories.models import History
from recruitments.models import Recruitment
from shelters.models import Shelter


class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ["name", "region", "address"]


class RecruitmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = ["id", "date"]


class HistorySerializer(serializers.ModelSerializer):
    shelter = ShelterSerializer()
    recruitment = RecruitmentSerializer()

    class Meta:
        model = History

        fields = ["id", "shelter", "recruitment", "rating"]


class HistoryRatingSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = History

        fields = ["id", "rating"]
