import random

from django.conf import settings
from django.contrib.sites import requests
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (  # UserUpdateSerializer,
    ChangePasswordSerializer,
    EmailCheckSerializer,
    EmailConfirmationSerializer,
    EmailLoginSerializer,
    FindEmailSerializer,
    KakaoLoginSerializer,
    LogoutSerializer,
    ResetPasswordSerializer,
    ShelterSignupSerializer,
    SignupSerializer,
    UserDeleteSerializer,
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
                    "password": ["비밀번호는 최소 8자리 이상이어야 합니다."],
                    "contact_number": ["이미 등록된 전화번호입니다."],
                    "email": ["이미 사용 중인 이메일입니다."],
                    "password_confirm": [
                        "비밀번호와 비밀번호 확인이 일치하지 않습니다."
                    ],
                }
            },
        },
    )
    def post(self, request):

        # 이메일과 전화번호 중복 체크
        email = request.data.get("email")
        contact_number = request.data.get("contact_number")

        if User.objects.filter(email=email).exists():
            return Response(
                {"email": "이미 사용 중인 이메일입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(contact_number=contact_number).exists():
            return Response(
                {"contact_number": "이미 등록된 전화번호입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SignupSerializer(data=request.data)
        # 유효성 검사 및 데이터 저장
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "회원가입이 완료되었습니다."},
                status=status.HTTP_201_CREATED,
            )
        # 유효성 검사 실패 시, 오류 반환
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
    serializer_class = ShelterSignupSerializer
    """
    🍒보호소 회원가입 API
    """

    @extend_schema(
        request=ShelterSignupSerializer,
        responses={
            201: {"example": {"message": "회원가입이 완료되었습니다."}},
            400: {
                "example": {
                    "password": ["비밀번호는 최소 8자리 이상이어야 합니다."],
                    "contact_number": ["이미 등록된 전화번호입니다."],
                    "email": ["이미 사용 중인 이메일입니다."],
                    "password_confirm": [
                        "비밀번호와 비밀번호 확인이 일치하지 않습니다."
                    ],
                }
            },
        },
    )
    def post(self, request):
        # 이메일과 전화번호 중복 체크
        email = request.data.get("email")
        contact_number = request.data.get("contact_number")

        if User.objects.filter(email=email).exists():
            return Response(
                {"email": "이미 사용 중인 이메일입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(contact_number=contact_number).exists():
            return Response(
                {"contact_number": "이미 등록된 전화번호입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SignupSerializer(data=request.data)
        # 유효성 검사 및 데이터 저장
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "회원가입이 완료되었습니다."},
                status=status.HTTP_201_CREATED,
            )
        # 유효성 검사 실패 시, 오류 반환
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
                    "token_type": "Bearer",
                }
            },
            400: {
                "example": {"message": ["카카오 계정이 등록되지 않은 사용자입니다."]},
                500: {"example": {"Error": "Internal Server Error"}},
            },
        },
    )
    def post(self, request):
        serializer = KakaoLoginSerializer(data=request.data)

        # 시리얼라이저 검증
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 카카오 API 호출 (비즈니스 로직은 뷰에서 처리)
        access_token = serializer.validated_data["access_token"]
        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(user_info_url, headers=headers)

        if response.status_code != 200:
            return Response(
                {"Error": "Internal Server Error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        user_info = response.json()
        provider_id = str(user_info.get("id"))

        # 카카오 로그인한 사용자가 이미 등록되었는지 확인
        user = User.objects.filter(provider_id=provider_id).first()
        if not user:
            return Response(
                {"message": "카카오 계정이 등록되지 않은 사용자입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # JWT 토큰 발급
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "token_type": "Bearer",
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

        # 회원 탈퇴 처리 (뷰에서 수행)
        request.user.delete()

        return Response(
            {"message": "회원 탈퇴가 완료되었습니다."}, status=status.HTTP_200_OK
        )
