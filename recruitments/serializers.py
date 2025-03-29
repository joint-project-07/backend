from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from users.models import User

from .models import Recruitment, RecruitmentImage


# 이미지 조회 serializer
class RecruitmentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentImage
        fields = ["id", "image_url"]


# ✅ 봉사활동 시리얼라이저
class RecruitmentSerializer(serializers.ModelSerializer):
    shelter_name = serializers.CharField(source="shelter.name", read_only=True)
    shelter_region = serializers.CharField(source="shelter.region", read_only=True)
    images = RecruitmentImageSerializer(read_only=True)

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "shelter",
            "shelter_name",
            "date",
            "start_time",
            "end_time",
            "type",
            "supplies",
            "shelter_region",
            "status",
            "images",
        ]


recruitment_types = ["cleaning", "walking", "feeding", "other"]


# ✅ 봉사활동 등록/수정 시리얼라이저
@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="봉사활동 등록",
            value={
                "date": "2025-04-01",
                "start_time": "10:00",
                "end_time": "13:00",
                "type": "cleaning",
                "supplies": "장갑, 마스크",
                "images": ["이미지1", "이미지2"],
            },
            request_only=True,
        )
    ]
)
class RecruitmentCreateUpdateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.ImageField(), required=False)

    class Meta:
        model = Recruitment
        fields = [
            "date",
            "start_time",
            "end_time",
            "type",  # ✅ 필수 값으로 설정
            "supplies",
            "images",
        ]
        extra_kwargs = {
            "type": {"required": True},  # ✅ 필수 값 설정
        }

    def validate(self, data):
        type_names = data["type"]

        invalid_types = [t for t in type_names if t not in recruitment_types]
        if invalid_types:
            raise serializers.ValidationError(f"Invalid type: {invalid_types}")

        return data

    def create(self, validated_data):
        # ✅ 보호소 연결 → 현재 로그인된 사용자 보호소와 연결
        images = validated_data.pop("images", [])
        user = self.context["request"].user

        if not hasattr(user, "shelter"):
            raise serializers.ValidationError("보호소 관리자만 등록할 수 있습니다.")

        recruitment = Recruitment.objects.create(shelter=user.shelter, **validated_data)

        for image in images:
            from common.utils import upload_file_to_s3, validate_file_extension

            validate_file_extension(image, "recruitments")
            image_url = upload_file_to_s3(image, "recruitments")
            RecruitmentImage.objects.create(
                recruitment=recruitment, image_url=image_url
            )

        return recruitment

    def update(self, instance, validated_data):
        # ✅ 수정 처리
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ✅ 봉사활동 상세 조회 시리얼라이저
class RecruitmentDetailSerializer(serializers.ModelSerializer):
    images = RecruitmentImageSerializer(read_only=True)
    shelter_name = serializers.CharField(source="shelter.name", read_only=True)
    shelter_region = serializers.CharField(source="shelter.region", read_only=True)

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "shelter",
            "shelter_name",
            "date",
            "start_time",
            "end_time",
            "type",
            "supplies",
            "shelter_region",
            "status",
            "images",
        ]


# 신청한 봉사자 조회 serializer
class RecruitmentApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "profile_image", "name", "contact_number"]
