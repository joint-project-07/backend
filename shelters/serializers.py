from rest_framework import serializers

from shelters.models import Shelter, ShelterImage


# ✅ 보호소 이미지 시리얼라이저
class ShelterImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShelterImage
        fields = ["id", "image_url", "image_type"]


# ✅ 보호소 시리얼라이저 (기본 정보)
class ShelterSerializer(serializers.ModelSerializer):
    images = ShelterImageSerializer(
        many=True, read_only=True
    )  # related_name="images" 사용
    owner_name = serializers.CharField(source="user.name", read_only=True)
    contact_number = serializers.CharField(source="user.contact_number", read_only=True)

    class Meta:
        model = Shelter
        fields = [
            "id",
            "name",
            "region",
            "address",
            "shelter_type",
            "business_registration_number",
            "business_registration_email",
            "contact_number",
            "business_license_file",
            "images",
            "owner_name",
        ]


# ✅ 보호소 생성 & 수정 시리얼라이저.
class ShelterCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = [
            "name",
            "region",
            "address",
            "shelter_type",
            "business_registration_number",
            "business_registration_email",
            "contact_number",
            "business_license_file",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        return Shelter.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
