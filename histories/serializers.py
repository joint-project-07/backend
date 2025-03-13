from rest_framework import serializers

from histories.models import History
from shelters.models import Shelter


class ShelterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ["name", "region", "address"]


class HistorySerializer(serializers.ModelSerializer):
    shelter = ShelterSerializer()

    class Meta:
        model = History
        fields = ["id", "recruitment_id", "shelter", "date", "rating"]
        extra_kwargs = {"id": {"source": "history_id", "read_only": True}}


class HistoryRatingSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
