import random

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import (
    BlacklistedToken,
    OutstandingToken,
    RefreshToken,
)

from common.utils import delete_file_from_s3, upload_file_to_s3, validate_file_extension
from shelters.models import Shelter

from .models import User
from .serializers import (  # UserUpdateSerializer,
    ChangePasswordSerializer,
    EmailCheckSerializer,
    EmailConfirmationSerializer,
    EmailLoginSerializer,
    FindEmailSerializer,
    KakaoLoginSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    ResetPasswordSerializer,
    ShelterSignupSerializer,
    SignupSerializer,
    UserDeleteSerializer,
    UserProfileImageSerializer,
    UserProfileImageUploadSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)


class SignupView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SignupSerializer
    """
    🍒봉사자 회원가입 API
    """

    @extend_schema(
        request=SignupSerializer,
        responses={
            201: {"example": {"message": "회원가입이 완료되었습니다."}},
            400: {
                "example": {
                    "email": ["이미 사용 중인 이메일입니다."],
                    "contact_number_duplicate": ["이미 등록된 전화번호입니다."],
                    "password": ["비밀번호는 최소 8자리 이상이어야 합니다."],
                    "contact_number_format": [
                        "전화번호는 01012345678 형식이어야 합니다."
                    ],
                    "password_confirm": [
                        "비밀번호와 비밀번호 확인이 일치하지 않습니다."
                    ],
                }
            },
        },
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "회원가입이 완료되었습니다."},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailCheckView(APIView):
    permission_classes = [AllowAny]  # 로그인 여부 상관없이 누구나 접근 가능하도록 설정
    serializer_class = EmailCheckSerializer
    """
    🍒이메일 중복 확인 API
    """

    @extend_schema(
        request=EmailCheckSerializer,
        responses={
            200: {"example": {"message": "사용 가능한 이메일입니다."}},
            400: {"example": {"email": "이미 사용 중인 이메일입니다."}},
            403: {"example": {"message": "이미 로그인되어 있습니다."}},
        },
    )
    def post(self, request):
        # 로그인된 사용자는 이메일 중복 확인 API에 접근할 수 없도록 처리
        if request.user.is_authenticated:
            raise PermissionDenied({"message": "이미 로그인되어 있습니다."})

        # 이메일 중복 확인 시리얼라이저를 통해 요청 데이터 검증
        serializer = EmailCheckSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # 이메일 중복 확인 (뷰에서 처리)
            if User.objects.filter(email=email).exists():
                return Response(
                    {"email": "이미 사용 중인 이메일입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {"message": "사용 가능한 이메일입니다."},
                status=status.HTTP_200_OK,
            )

        # 이메일 중복 시 오류 반환
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class EmailConfirmationView(APIView):
    permission_classes = [AllowAny]  # 로그인 여부 상관없이 누구나 접근 가능하도록 설정
    serializer_class = EmailConfirmationSerializer
    """
    🍒이메일 인증 확인 API
    """

    @extend_schema(request=EmailConfirmationSerializer, responses={})
    def send_verification_email(self, email):

        verification_code = random.randint(100000, 999999)

        subject = "이메일 인증을 완료해주세요."
        message = f"""
        <html>
            <body>
                <h1>이메일 인증</h1>
                <p>아래 코드를 입력하여 이메일 인증을 완료해주세요.</p>
                <p><strong>{verification_code}</strong></p>
            </body>
        </html>
        """

        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
            html_message=message,
        )

        cache.set(f"email_verification_code_{verification_code}", email, timeout=300)

    @extend_schema(
        request=EmailConfirmationSerializer,
        responses={
            200: {"example": {"message": "이메일 인증을 위한 코드가 전송되었습니다."}},
            403: {"example": {"message": "이미 로그인되어 있습니다."}},
            400: {"example": {"email": "이미 사용 중인 이메일입니다."}},
        },
    )
    def post(self, request):
        if request.user.is_authenticated:
            raise PermissionDenied({"message": "이미 로그인되어 있습니다."})

        serializer = EmailConfirmationSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]

            # 이메일 중복 확인: 비즈니스 로직 (뷰에서 처리)
            if User.objects.filter(email=email).exists():
                return Response(
                    {"email": "이미 사용 중인 이메일입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 이메일 인증 코드 전송
            self.send_verification_email(email)
            return Response(
                {"message": "이메일 인증을 위한 코드가 전송되었습니다."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]  # 로그인 여부 상관없이 누구나 접근 가능하도록 설정

    """
    🍒이메일 인증 처리
    """

    @extend_schema(
        request=VerifyEmailSerializer,
        responses={
            200: {"example": {"message": "이메일 인증이 완료되었습니다!"}},
            400: {"example": {"message": "인증 코드를 입력하세요."}},
            404: {"example": {"message": "유효하지 않거나 만료된 인증 코드입니다."}},
        },
    )
    def post(self, request):
        # 인증 코드만 받음
        code = request.data.get("code")
        print(
            f"Received code: {code}", flush=True
        )  # 디버깅: 코드가 잘 전달되었는지 확인

        if not code:
            return Response(
                {"message": "인증 코드를 입력하세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 인증 코드가 캐시에서 유효한지 확인
        if not cache.get(f"email_verification_code_{code}"):
            return Response(
                {"message": "유효하지 않거나 만료된 인증 코드입니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 인증 코드가 유효하면 사용자 활성화
        # 여기서는 이미 코드가 유효한지 확인했으므로 이메일을 찾을 필요 없음
        return Response(
            {"message": "이메일 인증이 완료되었습니다!"}, status=status.HTTP_200_OK
        )


class ShelterSignupView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    """
    🍒보호소 회원가입
    """

    @extend_schema(
        request=ShelterSignupSerializer,
        responses={
            201: {"example": {"message": "회원가입이 완료되었습니다."}},
            400: {
                "example": {
                    "user": {
                        "email": ["이미 사용 중인 이메일입니다."],
                        "contact_number_duplicate": ["이미 등록된 전화번호입니다."],
                        "password": ["비밀번호는 최소 8자리 이상이어야 합니다."],
                        "contact_number_format": [
                            "전화번호는 01012345678 형식이어야 합니다."
                        ],
                        "password_confirm": [
                            "비밀번호와 비밀번호 확인이 일치하지 않습니다."
                        ],
                    }
                }
            },
        },
    )
    def post(self, request):
        # ShelterSignupSerializer에 요청 데이터 넘기기
        serializer = ShelterSignupSerializer(data=request.data)

        if serializer.is_valid():
            # 비밀번호 해싱과 검증이 완료된 validated_data로 User와 Shelter 인스턴스를 생성
            validated_data = serializer.validated_data

            # User 객체 생성
            user = User.objects.create_user(
                email=validated_data["email"],
                password=validated_data["password"],
                name=validated_data["user_name"],
                contact_number=validated_data["contact_number"],
            )

            # 사업자등록증 파일 처리
            business_license_file = request.FILES.get("business_license_file", None)
            if business_license_file:
                # 파일을 S3에 업로드하고 URL 반환
                file_url = upload_file_to_s3(business_license_file, "shelters")
            else:
                file_url = None

            # Shelter 객체 생성
            Shelter.objects.create(
                user=user,
                name=validated_data["shelter_name"],
                shelter_type=validated_data["shelter_type"],
                business_registration_number=validated_data[
                    "business_registration_number"
                ],
                business_registration_email=validated_data[
                    "business_registration_email"
                ],
                address=validated_data["address"],
                region=validated_data["region"],
                business_license_file=file_url,  # 사업자등록증 파일 URL 저장
            )

            return Response(
                {"message": "회원가입이 완료되었습니다."},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = EmailLoginSerializer
    """
    🍒이메일 로그인 API
    """

    @extend_schema(
        request=EmailLoginSerializer,
        responses={
            200: {
                "example": {
                    "message": "로그인 성공",
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                }
            },
            400: {
                "example": {
                    "email": "사용자를 찾을 수 없습니다.",
                    "password": "비밀번호가 올바르지 않습니다.",
                }
            },
        },
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = request.data.get("password")  # 비밀번호는 따로 가져옴

            # 사용자 조회 (뷰에서 처리)
            user = User.objects.filter(email=email).first()
            if not user:
                return Response(
                    {"email": "사용자를 찾을 수 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 인증 (비밀번호 확인)
            if not user.check_password(password):
                # 로그인 성공 시, 시리얼라이저에 작성된 validated_data 반환
                return Response(
                    {"password": "비밀번호가 올바르지 않습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # JWT 토큰 발급
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "message": "로그인 성공",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "token_type": "Bearer",
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RefreshTokenSerializer
    """
    🍒액세스 토큰 갱신 API
    """

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={
            200: {
                "example": {
                    "message": "액세스 토큰 갱신 성공",
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                }
            },
            400: {"example": {"error": "리프레시 토큰을 제공해야 합니다."}},
            401: {
                "example": {"error": "리프레시 토큰이 유효하지 않거나 만료되었습니다."}
            },
        },
    )
    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "리프레시 토큰을 제공해야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 리프레시 토큰 검증
            refresh = RefreshToken(refresh_token)

            # 새로운 액세스 토큰 발급
            new_access_token = str(refresh.access_token)

            return Response(
                {
                    "message": "액세스 토큰 갱신 성공",
                    "access_token": new_access_token,
                    "token_type": "Bearer",
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {"error": "리프레시 토큰이 유효하지 않거나 만료되었습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class KakaoLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = KakaoLoginSerializer
    """
    🍒 카카오 로그인API
    """

    @extend_schema(
        request=KakaoLoginSerializer,
        responses={
            200: {
                "example": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                }
            },
            400: {
                "example": {"message": "인가 코드가 필요합니다."},
                401: {
                    "example": {"message": "카카오 액세스 토큰 발급 실패"},
                    500: {"example": {"Error": "Internal Server Error"}},
                },
            },
        },
    )
    def post(self, request, *args, **kwargs):
        # 1. 프론트에서 받은 인가코드
        authorization_code = request.data.get("authorization_code")

        if not authorization_code:
            return Response(
                {"message": "인가 코드가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. 카카오 토큰 발급 요청
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "client_secret": settings.KAKAO_SECRET,
            "code": authorization_code,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(token_url, data=data, headers=headers)
        token_info = response.json()

        # 3. 카카오 액세스 토큰
        access_token = token_info.get("access_token")

        if not access_token:
            return Response(
                {"message": "카카오 액세스 토큰 발급 실패"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 4. 카카오 유저 정보 조회
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        user_info_headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=user_info_headers)
        user_info = user_info_response.json()

        # 5. 카카오 유저 정보로 유저 찾기 또는 생성
        provider_id = str(user_info.get("id"))
        email = user_info.get("kakao_account", {}).get("email", None)
        name = user_info.get("properties", {}).get("nickname", None)
        profile_image = user_info.get("properties", {}).get("profile_image", None)

        user = User.objects.filter(provider_id=provider_id).first()

        if not user:
            user = User.objects.create(
                email=email,
                name=name,
                provider_id=provider_id,
                kakao_login=True,
                profile_image=profile_image,
            )

        # 6. JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # 7. JWT 반환
        return Response(
            {
                "access_token": access_token,
                "refresh_token": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class FindEmailView(APIView):
    permission_classes = [AllowAny]  # 로그인 여부 상관없이 누구나 접근 가능하도록 설정
    serializer_class = FindEmailSerializer
    """
    🍒 아이디 찾기 API
    """

    @extend_schema(
        request=FindEmailSerializer,
        responses={
            200: {"example": {"email": "user@email.com"}},
            400: {"example": {"message": "이미 로그인되어 있습니다."}},
            404: {"example": {"message": "사용자를 찾을 수 없습니다."}},
        },
    )
    def post(self, request):
        # 아이디 찾기 시리얼라이저를 통해 요청 데이터 검증
        serializer = FindEmailSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            # 로그인된 사용자인지 체크 (뷰에서 처리)
            if request.user.is_authenticated:
                return Response(
                    {"message": "이미 로그인되어 있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            name = serializer.validated_data.get("name")
            contact_number = serializer.validated_data.get("contact_number")

            # 사용자 조회는 뷰에서 처리
            user = User.objects.filter(name=name, contact_number=contact_number).first()

            if not user:
                return Response(
                    {"message": "사용자를 찾을 수 없습니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 이메일 반환
            return Response({"email": user.email}, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시, 오류 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    """
    🍒 임시비밀번호 API
    """

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: {"example": {"message": "임시 비밀번호가 이메일로 전송되었습니다."}},
            400: {"example": {"message": "이미 로그인된 사용자입니다."}},
            404: {"example": {"message": "사용자를 찾을 수 없습니다."}},
            500: {"example": {"Error": "Internal Server Error"}},
        },
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            return Response(
                {"message": "이미 로그인된 사용자입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contact_number = serializer.validated_data["contact_number"]
        email = serializer.validated_data["email"]

        # 사용자 조회
        user = User.objects.filter(contact_number=contact_number, email=email).first()
        if not user:
            return Response(
                {"message": "사용자를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 임시 비밀번호 생성
        temp_password = get_random_string(length=8)
        user.set_password(temp_password)  # 해싱하여 저장
        user.save()

        # 이메일 전송
        try:
            send_mail(
                "펫모어헨즈에서 임시 비밀번호 알려드립니다.",  # 제목
                f"임시 비밀번호는 {temp_password}입니다.",  # 내용
                settings.EMAIL_HOST_USER,  # 발신자 이메일 (실제로 존재해야함)
                [user.email],  # 수신자 이메일
                fail_silently=False,
            )
        except Exception:
            return Response(
                {"Error": "Internal Server Error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "임시 비밀번호가 이메일로 전송되었습니다."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    """
    🍒 비밀번호 변경 API
    """

    @extend_schema(
        request=ChangePasswordSerializer,
        responses={
            200: {"example": {"message": "비밀번호가 성공적으로 변경되었습니다."}},
            400: {
                "example": {"current_password": ["현재 비밀번호가 올바르지 않습니다."]}
            },
        },
    )
    def put(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호 변경 처리 (뷰에서 수행)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"message": "비밀번호가 성공적으로 변경되었습니다."},
            status=status.HTTP_200_OK,
        )


class UserView(APIView):
    permission_classes = [IsAuthenticated]
    """
    🍒 사용자 정보 조회/수정 API
    """

    # 인증된 사용자만 접근 가능
    @extend_schema(request=UserSerializer, responses=UserSerializer)
    def get(self, request):
        # 인증된 사용자 정보 가져오기
        user = request.user

        # 사용자의 정보를 반환
        serializer = UserSerializer(user)

        # 원하는 형식으로 응답 데이터
        response_data = {
            "user": serializer.data,  # user 정보는 시리얼라이저에서 반환된 데이터
        }
        return Response(response_data, status=status.HTTP_200_OK)


# 현재 사용 x
# @extend_schema(
#     request=UserUpdateSerializer,
#     responses={
#         200: {
#             "example": {
#                 "message": "사용자 정보가 성공적으로 수정되었습니다.",
#                 "user": {
#                     "id": 29,
#                     "email": "user@gmail.com",
#                     "name": "string33",
#                     "contact_number": "01044444444",
#                     "profile_image": "string",
#                 },
#             }
#         }
#     },
# )
# def put(self, request):
#     # 인증된 사용자 정보 가져오기
#     user = request.user
#
#     # name 필드 포함해야함
#     serializer = UserUpdateSerializer(
#         user, data=request.data
#     )
#
#     # 시리얼라이저 유효성 검사
#     if serializer.is_valid():
#         # 정보가 유효하면, 업데이트 작업 후 결과 반환
#         updated_user = serializer.save()
#
#         # 수정된 사용자 객체를 시리얼라이즈 후 응답
#         updated_data = UserSerializer(updated_user).data
#         return Response(
#             {
#                 "message": "사용자 정보가 성공적으로 수정되었습니다.",
#                 "user": updated_data,
#             },
#             status=status.HTTP_200_OK,
#         )
#
#     # 유효성 검사 실패 시, 오류 반환
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    serializer_class = LogoutSerializer
    """
    🍒 로그아웃 API
    """

    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: {"example": {"message": "성공적으로 로그아웃 되었습니다."}},
            400: {"example": {"message": "Token is invalid"}},
        },
    )
    def post(self, request):
        try:
            serializer = LogoutSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            refresh_token = serializer.validated_data["refresh_token"]

            # Refresh Token 블랙리스트 처리
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "성공적으로 로그아웃 되었습니다."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]  # 로그인한 사용자만 접근 가능
    """
    🍒 회원탈퇴 API
    """

    @extend_schema(
        request=UserDeleteSerializer,
        responses={
            200: {"example": {"message": "회원 탈퇴가 완료되었습니다."}},
            400: {"example": {"password": ["비밀번호가 올바르지 않습니다."]}},
        },
    )
    def post(self, request):
        serializer = UserDeleteSerializer(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # 사용자 탈퇴 후, 해당 사용자의 JWT 토큰을 블랙리스트에 추가
        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)

        # 회원 탈퇴 처리 (뷰에서 수행)
        request.user.delete()

        return Response(
            {"message": "회원 탈퇴가 완료되었습니다."}, status=status.HTTP_200_OK
        )


class ProfileImageUploadDeleteView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    """
    🍒 이미지 API
    """

    # 유저 프로필 이미지 업로드
    @extend_schema(
        summary="유저 프로필 이미지 업로드",
        request=UserProfileImageUploadSerializer,
        responses={201: UserProfileImageSerializer},
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = UserProfileImageUploadSerializer(data=request.FILES)
        if serializer.is_valid(raise_exception=True):

            file = serializer.validated_data["image"]

            if not file:
                return Response(
                    {"error": "이미지를 업로드해야 합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 기존 이미지 삭제
            if user.profile_image:
                delete_file_from_s3(user.profile_image)
                user.profile_image = None
                user.save()

            # 파일 검증 및 업로드
            try:
                validate_file_extension(file, "users")
                s3_url = upload_file_to_s3(file, "users")
            except ValueError as e:
                return Response(
                    {"error": "업로드에 실패하였습니다.", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 새 이미지 저장
            user.profile_image = s3_url
            user.save()

            return Response(
                UserProfileImageSerializer(user).data, status=status.HTTP_201_CREATED
            )

        return Response(
            {"error": "업로드에 실패하였습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 유저 프로필 이미지 삭제
    @extend_schema(
        summary="유저 프로필 이미지 삭제",
        description="유저가 자신의 프로필 이미지를 삭제합니다.",
        responses={
            204: None,
            400: {"example": {"error": "삭제 실패"}},
            403: {"example": {"error": "권한 없음"}},
            404: {"example": {"error": "이미지 없음"}},
        },
    )
    def delete(self, request, *args, **kwargs):
        user = request.user

        if not user.profile_image:
            return Response(
                {"error": "삭제할 프로필 이미지가 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            delete_file_from_s3(user.profile_image)
            user.profile_image = None
            user.save()
            return Response(
                {"message": "이미지 삭제가 완료되었습니다."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "이미지 삭제에 실패하였습니다.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserProfileImageView(APIView):
    permission_classes = [AllowAny]

    # 유저 프로필 이미지 조회
    @extend_schema(
        summary="유저 프로필 이미지 조회",
        responses={200: UserProfileImageSerializer},
    )
    def get(self, request):
        user = request.user

        if not user.profile_image:
            return Response(
                {"error": "프로필 이미지가 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            UserProfileImageSerializer(user).data,
            status=status.HTTP_200_OK,
        )
