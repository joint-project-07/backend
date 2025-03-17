import re

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

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

    # 비밀번호 8자리 이상 검증
    def validate_password(self, value):

        if len(value) < 8:
            raise serializers.ValidationError(
                "비밀번호는 최소 8자리 이상이어야 합니다."
            )
        return value

    # 전화번호 형식 검증 (숫자만 허용, 10~11자리)
    def validate_contact_number(self, value):

        if not re.fullmatch(r"^01[0-9]\d{7,8}$", value):
            raise serializers.ValidationError(
                "전화번호는 01012345678 형식이어야 합니다."
            )
        return value

    def validate(self, data):
        errors = {}  # 여러 개의 에러를 모을 딕셔너리

        # 비밀번호 확인
        if data["password"] != data["password_confirm"]:
            errors["password_confirm"] = [
                "비밀번호와 비밀번호 확인이 일치하지 않습니다."
            ]

        # 이메일 중복 체크 (한 번더)
        if User.objects.filter(email=data["email"]).exists():
            errors["email"] = ["이미 사용 중인 이메일입니다."]

        # 전화번호 중복 확인
        if User.objects.filter(contact_number=data["contact_number"]).exists():
            errors["contact_number"] = ["이미 등록된 전화번호입니다."]

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

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value


# 🍒 이메일 인증 확인
class EmailConfirmationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # 이미 등록된 이메일은 다시 인증할 수 없음
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value

    def send_confirmation_email(self, email):
        # 이메일을 통해 User 객체를 조회하되, 사용자 없으면 새로 생성할 수 있도록 변경
        user = None
        try:
            user = User.objects.get(email=email)
            # 이미 존재하는 사용자라면, 인증 메일을 보내지 않음
            return  # 이미 가입된 사용자에게는 인증 메일을 보내지 않음
        except User.DoesNotExist:
            # 사용자가 없으면, 이메일 인증 메일을 보냄
            pass  # 아무것도 하지 않음 (예: 로깅하거나 다른 처리를 할 수 있음)

        # 인증을 위한 URL 생성
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode()).decode()

        # 이메일 내용
        subject = "이메일 인증을 완료해 주세요."
        message = render_to_string(
            "email/confirmation_email.html",
            {
                "user": user,
                "uid": uid,
                "token": token,
            },
        )
        # 이메일 발송
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,  # 발신자 이메일
            [user.email],  # 수신자 이메일
            fail_silently=False,
        )


# 🍒보호소 회원가입
class ShelterSignupSerializer(serializers.ModelSerializer):
    user = SignupSerializer()  # 중첩된 SignupSerializer (User 생성용)

    class Meta:
        model = Shelter
        fields = [
            "user",  # User 데이터를 포함
            "name",
            "shelter_type",
            "business_registration_number",
            "business_registration_email",
            "address",
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

    def validate(self, data):
        email = data.get("email")  # 로그인 요청시 입력한 email,password 가져옴므
        password = data.get("password")

        # 이메일로 사용자 조회
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"email": ["사용자를 찾을 수 없습니다."]})

        # 인증 (비밀번호 확인)
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError(
                {"password": ["비밀번호가 올바르지 않습니다."]}
            )

        # JWT Token 발급
        refresh = RefreshToken.for_user(user)  # Refresh & Access Token 생성

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "token_type": "Bearer",
        }


# 🍒카카오 로그인과 회원가입
class KakaoLoginSerializer(serializers.Serializer):
    access_token = (
        serializers.CharField()
    )  # 사용자가 카카오 로그인을 통해 받은 access_token

    def validate(self, data):
        access_token = data.get("access_token")

        # 카카오 사용자 정보 요청
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(user_info_url, headers=headers)

        if response.status_code != 200:
            raise serializers.ValidationError(
                {"message": "카카오 사용자 정보를 가져오는 데 실패했습니다."}
            )

        user_info = response.json()
        provider_id = str(user_info.get("id"))  # 카카오 고유 사용자 ID 추출

        # 카카오 로그인한 사용자가 이미 등록되었는지 확인
        user = User.objects.filter(provider_id=provider_id).first()

        if not user:  # 사용자 없으면 회원가입 처리
            nickname = user_info.get("properties", {}).get("nickname", "NoName")
            email = user_info.get("kakao_account", {}).get("email", None)
            if not email:
                raise serializers.ValidationError(
                    {"message": "이메일 정보가 필요합니다."}
                )

            # 새로운 사용자 생성
            user = User.objects.create(
                email=email,  # 카카오에서 받은 이메일
                name=nickname,  # 카카오에서 받은 닉네임
                provider_id=provider_id,  # 카카오 고유 사용자 ID
                is_shelter=False,  # 기본값
                kakao_login=True,  # 카카오 로그인으로 가입한 사용자임을 표시
            )

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "token_type": "Bearer",
        }


# 🍒아이디 찾기
class FindEmailSerializer(serializers.Serializer):
    name = serializers.CharField()
    contact_number = serializers.CharField()

    def validate(self, data):
        name = data.get("name")
        contact_number = data.get("contact_number")
        # 사용자를 이름과 전번으로 조회
        user = User.objects.filter(name=name, contact_number=contact_number).first()

        if not user:
            # 사용자 정보가 일치하지 않으면 ValidationError 발생
            raise serializers.ValidationError({"message": "사용자를 찾을 수 없습니다."})

        # 이메일 정보가 없는 경우
        if not user.email:
            raise serializers.ValidationError({"message": "이메일 정보가 없습니다."})

        return {"email": user.email}


# 🍒 임시비밀번호
class ResetPasswordSerializer(serializers.Serializer):
    contact_number = serializers.CharField()
    email = serializers.EmailField()

    def validate(self, data):
        contact_number = data.get("contact_number")
        email = data.get("email")

        # 사용자 조회
        user = User.objects.filter(contact_number=contact_number, email=email).first()

        if not user:
            # 사용자 존재하지 않으면 ValidationError 발생
            raise serializers.ValidationError({"message": "사용자를 찾을 수 없습니다."})

        if user.email != email:
            # 이메일이 일치하지 않으면 ValidationError 발생
            raise serializers.ValidationError(
                {"message": "이메일이 일치하지 않습니다."}
            )

        # 임시 비밀번호 생성
        temp_password = get_random_string(length=8)  # 임시 비밀번호 (8자리)

        # 임시 비밀번호를 설정하고 저장
        user.set_password(temp_password)  # 해싱하여 저장
        user.save()

        # 이메일로 임시 비밀번호 전송
        try:
            send_mail(
                "펫모어헨즈에서 임시 비밀번호 알려드립니다.",  # 제목
                f"임시 비밀번호는 {temp_password}입니다.",  # 내용
                settings.EMAIL_HOST_USER,  # 발신자 이메일 (실제로 존재해야함)
                [user.email],  # 수신자 이메일
                fail_silently=False,  # 이메일 전송 실패 시 except으로
            )
        except Exception:
            # 이메일 전송 실패 시 500 에러 발생
            raise serializers.ValidationError(
                {"message": "전송에 실패했습니다. 잠시 후 다시 시도해주세요."}
            )

        return {"message": "임시 비밀번호가 이메일로 전송되었습니다."}


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

    def update(self, instance, validated_data):
        """비밀번호 변경 처리"""
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance


# 🍒사용자 정보 조회
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "contact_number", "profile_image"]


# 🍒사용자 정보 수정
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "contact_number", "profile_image"]
        read_only_fields = ["email", "contact_number"]  # 이메일과 전화번호는 수정 불가

    def update(self, instance, validated_data):
        # 이메일과 전화번호는 이미 read_only=True로 설정되어있어서 수정하려고 하면 오류 발생시켜버리기
        if "email" in validated_data:
            raise serializers.ValidationError(
                {
                    "message": "이메일은 수정할 수 없습니다."
                }  # `code`는 응답에서 뷰에서 설정
            )
        if "contact_number" in validated_data:
            raise serializers.ValidationError(
                {
                    "message": "전화번호는 수정할 수 없습니다."
                }  # `code`는 응답에서 뷰에서 설정
            )

        # 나머지 데이터만(이메일, 전번 제외 나머지) 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        # 데이터가 성공적으로 수정된 후, 수정된 인스턴스 반환
        return instance

    def validate(self, attrs):
        # 인증된 사용자만 접근할 수 있도록 처리
        request = self.context.get("request")  # context에서 request 객체를 가져옴
        if request and not request.user.is_authenticated:
            raise AuthenticationFailed({"message": "인증이 필요합니다."})
        return attrs


# 🍒 로그아웃
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
