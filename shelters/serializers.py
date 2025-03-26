from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from shelters.models import Shelter


# ✅ 보호소 시리얼라이저 (기본 정보)
class ShelterSerializer(serializers.ModelSerializer):
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

    # ✅ Shelter 생성 → user 연결해서 생성
    def create(self, validated_data):
        user = self.context["request"].user
        return Shelter.objects.create(user=user, **validated_data)

    # ✅ Shelter 수정 → 부분 수정 가능
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ShelterBusinessLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shelter
        fields = ["id", "business_license_file"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="이미지 업로드",
            value={"business_license": "사업자등록증 파일"},
            request_only=True,
        )
    ]
)
class ShelterBusinessLicenseUploadSerializer(serializers.Serializer):
    business_license = serializers.FileField()
