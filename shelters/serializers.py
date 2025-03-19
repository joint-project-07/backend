from django.core.exceptions import ValidationError
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
    owner_name = serializers.SerializerMethodField()
    contact_number = serializers.SerializerMethodField()

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

    # ✅ 사용자 이름이 없을 경우 처리
    def get_owner_name(self, obj):
        return obj.user.name if obj.user else None

    # ✅ 연락처가 없을 경우 처리
    def get_contact_number(self, obj):
        return obj.user.contact_number if obj.user else None


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

    # ✅ 필수 값이 누락될 경우 에러 반환
    def validate(self, data):
        required_fields = [
            "name",
            "region",
            "address",
            "shelter_type",
            "business_registration_number",
            "business_registration_email",
        ]
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f"{field} 값은 필수입니다.")
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        if not user:
            raise ValidationError("사용자 정보가 필요합니다.")
        return Shelter.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if not instance:
            raise ValidationError("수정할 보호소가 존재하지 않습니다.")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
