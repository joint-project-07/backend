import re

from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from common.utils import upload_file_to_s3
from shelters.models import Shelter

from .models import User


# 🍒봉사자 회원가입
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True
    )  # 요청에서만 사용 응답에선 숨김(get요청(응답)에는 안보임)
    password_confirm = serializers.CharField(write_only=True)  # 같은 이유

    class Meta:
        model = User  # 어떤 모델쓸래
        fields = [
            "email",
            "password",
            "password_confirm",
            "name",
            "contact_number",
        ]  # 포함할 필드
        extra_kwargs = {
            "email": {
                "validators": []
            },  # 기본 유니크 검증 비활성화!(email 필드의 기본 유니크 검증을 끄고, 대신 우리가 직접 검증하겠다)
        }

    def validate(self, data):
        errors = {}  # 여러 개의 에러를 모을 딕셔너리

        # 🧀 이메일 중복 검사
        if User.objects.filter(email=data["email"]).exists():
            errors["email"] = ["이미 사용 중인 이메일입니다."]

        # 🧀 전화번호 중복 검사
        if User.objects.filter(contact_number=data["contact_number"]).exists():
            errors["contact_number_duplicate"] = ["이미 등록된 전화번호입니다."]

        # 🧀 비밀번호 길이 검증
        if len(data["password"]) < 8:
            errors["password"] = ["비밀번호는 최소 8자리 이상이어야 합니다."]

        # 🧀 전화번호 형식 검증
        if not re.fullmatch(r"^01[0-9]\d{7,8}$", data["contact_number"]):
            errors["contact_number_format"] = [
                "전화번호는 01012345678 형식이어야 합니다."
            ]

        # 🧀 비밀번호 확인
        if data["password"] != data["password_confirm"]:
            errors["password_confirm"] = [
                "비밀번호와 비밀번호 확인이 일치하지 않습니다."
            ]

        if errors:  # 하나라도 에러가 있으면 ValidationError 발생
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")  # DB에 저장안함
        validated_data["password"] = make_password(
            validated_data["password"]
        )  # 비밀번호 해싱
        return super().create(validated_data)


# 🍒이메일 중복
class EmailCheckSerializer(serializers.Serializer):
    email = serializers.EmailField()


# 🍒이메일 인증 확인
class EmailConfirmationSerializer(serializers.Serializer):
    email = serializers.EmailField()


# 🍒이메일 인증 처리
class VerifyEmailSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)


# 🍒보호소 회원가입
class ShelterSignupSerializer(serializers.ModelSerializer):
    user = SignupSerializer()  # 중첩된 SignupSerializer (User 생성용)
    business_license = serializers.FileField()  # 사업자등록증

    class Meta:
        model = Shelter
        fields = [
            "user",  # User 데이터를 포함
            "name",
            "shelter_type",
            "business_registration_number",
            "business_registration_email",
            "address",
            "region",
            "business_license",
        ]

    def validate(self, data):
        user_data = data.get("user")

        # SignupSerializer의 validate()를 직접 호출하여 검증 (중복 검사)
        user_serializer = SignupSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)

        return data  # 검증된 데이터 반환

    def create(self, validated_data):
        user_data = validated_data.pop("user")  # User 데이터만 분리해서
        user_data.pop("password_confirm", None)  # 'password_confirm'을 실제로 제거
        # 비밀번호를 해싱하여 저장
        if user_data.get("password"):
            user_data["password"] = make_password(user_data["password"])

        user = User.objects.create(
            **user_data, is_shelter=True
        )  # 보호소 관리자인 경우 is_shelter=True로 설정

        shelter_data = validated_data
        shelter = Shelter.objects.create(
            user_id=user.id, **shelter_data
        )  # 나머지 Shelter 객체 생성

        return shelter  # 생성된 Shelter 객체 반환


# 🍒이메일 로그인(봉사자/보호소)
class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()  # 필수값, 이메일 형식인지 검증
    password = serializers.CharField(write_only=True)


# 🍒 액세스 토큰 갱신
class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()  # 문자열 필드로 리프레시 토큰을 받음


# 🍒카카오 로그인
class KakaoLoginSerializer(serializers.Serializer):
    authorization_code = serializers.CharField()


# 🍒아이디 찾기
class FindEmailSerializer(serializers.Serializer):
    name = serializers.CharField()
    contact_number = serializers.CharField()


# 🍒 임시비밀번호
class ResetPasswordSerializer(serializers.Serializer):
    contact_number = serializers.CharField()
    email = serializers.EmailField()


# 🍒비밀번호 변경
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        """현재 비밀번호 확인"""
        user = self.context["request"].user
        if not check_password(value, user.password):
            raise serializers.ValidationError("현재 비밀번호가 올바르지 않습니다.")
        return value

    def validate_new_password(self, value):
        """비밀번호 정책 검증"""
        validate_password(value)  # Django 기본 비밀번호 검증 사용
        return value


# 🍒사용자 정보 조회
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "contact_number", "profile_image"]


# # 🍒사용자 정보 수정 (현재 사용x)
# class UserUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["name", "profile_image"]
#         read_only_fields = ["email", "contact_number"]  # 이메일과 전화번호는 수정 불가
#
#     def update(self, instance, validated_data):
#         # name만 업데이트 (profile_image 관련 코드 제거)
#         instance.name = validated_data.get("name", instance.name)
#         instance.save()
#         return instance


# 🍒 로그아웃
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


# 🍒회원 탈퇴
class UserDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("비밀번호가 올바르지 않습니다.")
        return value


class UserProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "profile_image"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            name="이미지 업로드",
            value={"image": "이미지 파일"},
            request_only=True,
        )
    ]
)
class UserProfileImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
