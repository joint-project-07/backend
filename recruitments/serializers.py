from rest_framework import serializers

from .models import Recruitment, RecruitmentImage


# ✅ 봉사활동 시리얼라이저
class RecruitmentSerializer(serializers.ModelSerializer):
    shelter_name = serializers.CharField(source="shelter.name", read_only=True)

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
            "status",
        ]


# ✅ 봉사활동 등록/수정 시리얼라이저
class RecruitmentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruitment
        fields = [
            "date",
            "start_time",
            "end_time",
            "type",  # ✅ 필수 값으로 설정
            "supplies",
        ]
        extra_kwargs = {
            "type": {"required": True},  # ✅ 필수 값 설정
        }

    def create(self, validated_data):
        # ✅ 보호소 연결 → 현재 로그인된 사용자 보호소와 연결
        user = self.context["request"].user
        if not hasattr(user, "shelter"):
            raise serializers.ValidationError("보호소 관리자만 등록할 수 있습니다.")
        validated_data["shelter"] = user.shelter
        return Recruitment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # ✅ 수정 처리
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ✅ 봉사활동 상세 조회 시리얼라이저
class RecruitmentDetailSerializer(serializers.ModelSerializer):
    shelter_name = serializers.CharField(source="shelter.name", read_only=True)

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
            "status",
        ]


class RecruitmentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecruitmentImage
        fields = ["id", "recruitment", "image_url"]
