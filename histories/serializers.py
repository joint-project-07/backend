from rest_framework import serializers

from histories.models import History
from recruitments.models import Recruitment
from shelters.models import Shelter


class HistoryShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ["name", "region", "address"]


class HistoryRecruitmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = ["id", "date"]


class HistorySerializer(serializers.ModelSerializer):
    shelter = HistoryShelterSerializer()
    recruitment = HistoryRecruitmentSerializer()

    class Meta:
        model = History

        fields = ["id", "shelter", "recruitment", "rating"]


class HistoryRatingSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = History

        fields = ["id", "rating"]
