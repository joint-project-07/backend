from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.sites import requests
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError
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

    def validate(self, data):
        # 비밀번호와 비밀번호 확인 일치하는지 검증
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError(
                {"message": "비밀번호와 비밀번호 확인이 일치하지 않습니다."}
            )

        # 이메일 중복 검사
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"message": "이미 사용 중인 이메일입니다."}
            )

        # 전화번호 중복 검사
        if User.objects.filter(contact_number=data["contact_number"]).exists():
            raise serializers.ValidationError(
                {"message": "이미 등록된 전화번호 입니다."}
            )

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")  # DB에 저장안함
        validated_data["password"] = make_password(
            validated_data["password"]
        )  # 비밀번호 해싱
        return super().create(validated_data)


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
        user = User.objects.create(**user_data)  # User 객체 생성

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

        # 이메일로 사용자 조회함
        user = User.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError({"message": "사용자를 찾을 수 없습니다."})

        # 인증 (비밀번호 확인)
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError(
                {"message": "비밀번호가 올바르지 않습니다."}
            )

        # JWT Token 발급
        refresh = RefreshToken.for_user(user)  # Refresh & Access Token 생성

        return {
            "code": 200,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "token_type": "Bearer",
        }


# 🍒카카오 로그인(봉사자)
class KakaoLoginSerializer(serializers.Serializer):
    access_token = (
        serializers.CharField()
    )  # 사용자가 카카오 로그인을 통해 받은 -> 사용자의 카카오 정보를 요청 가능

    def validate(self, data):
        access_token = data.get("access_token")  # 카카오 서버에서 사용자 정보 가져옴

        # 카카오 사용자 정보 요청
        user_info_url = "https://kapi.kakao.com/v2/user/me"  # GET 요청
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(user_info_url, headers=headers)

        if response.status_code != 200:  # 200 OK가 아니면
            raise ValidationError(
                {"message": "카카오 사용자 정보를 가져오는 데 실패했습니다."}
            )

        user_info = response.json()  # 카카오에서 받은 응답 JSON 형태로
        provider_id = str(user_info.get("id"))  # 카카오 고유 사용자 ID 추출함

        # 카카오 로그인한 사용자가 이미 등록되었는지 확인함
        user = User.objects.filter(
            provider_id=provider_id
        ).first()  # 받은 provider_id가 기존에 등록된 provider_id랑 일치하는지
        if not user:
            raise ValidationError(
                {"message": "소셜 계정이 등록되지 않았습니다."}
            )  # 일치하지 않으면

        # JWT 토큰 발급 (로그인 후 사용자가 인증된 상태로 이용가능하게)
        refresh = RefreshToken.for_user(user)
        return {
            "code": 200,
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
            # 사용자 정보가 일치하지 않으면 404 에러 반환
            raise ValidationError(
                {"code": 404, "message": "사용자를 찾을 수 없습니다."}
            )

            # 일치하는 사용자가 있지만 이메일 정보가 없는 경우
        if not user.email:
            raise ValidationError(
                {"code": 400, "message": "사용자 정보가 일치하지 않습니다."}
            )

        return {"code": 200, "email": user.email}


# 🍒 비밀번호 재설정
class ResetPasswordSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()

    def validate(self, data):
        name = data.get("name")
        email = data.get("email")
        # 사용자 조회
        user = User.objects.filter(name=name, email=email).first()

        if not user:
            # 사용자 존재하지 않으면 404 에러 반환
            raise ValidationError(
                {"code": 404, "message": "사용자를 찾을 수 없습니다."}
            )

        if user.email != email:
            # 이메일이 일치하지 않으면 400 에러 반환
            raise ValidationError(
                {"code": 400, "message": "이메일이 일치하지 않습니다."}
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
                "no-reply@example.com",  # 발신자 이메일 ( 실제 존재해야함..)
                [user.email],  # 수신자 이메일
                fail_silently=False,  # 이메일 전송 실패 시 except으로
            )
        except Exception:
            # 이메일 전송 실패 시 500 에러 반환
            raise ValidationError(
                {
                    "code": 500,
                    "message": "전송에 실패했습니다. 잠시 후 다시 시도해주세요.",
                }
            )

        return {"code": 200, "message": "임시 비밀번호가 이메일로 전송되었습니다."}


# 🍒사용자 정보 조회
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "contact_number", "profile_image"]


# 🍒사용자 정보 수정
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["name", "birth_date", "contact_number", "profile_image"]
        read_only_fields = ["email", "contact_number"]  # 이메일과 전화번호는 수정 불가

    def update(self, instance, validated_data):
        # 이메일과 연락처는 이미 read_only=True로 설정되어있어서 수정하려고 하면 오류 발생시켜버리기
        if "email" in validated_data:
            raise serializers.ValidationError(
                {"message": "이메일은 수정할 수 없습니다."}
            )
        if "contact_number" in validated_data:
            raise serializers.ValidationError(
                {"message": "전화번호는 수정할 수 없습니다."}
            )

        # 나머지 데이터만(이메일,전번 제외 나머지) 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        # 성공 응답 반환
        return {"code": 200, "message": "사용자 정보가 성공적으로 수정되었습니다."}

        # 미인증 사용자일때 에러

    def validate(self, attrs):
        if not self.context.get("request").user.is_authenticated:
            raise AuthenticationFailed({"code": 401, "message": "인증이 필요합니다."})
        return attrs
