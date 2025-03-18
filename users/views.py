from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
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
    UserUpdateSerializer,
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
    )
    def post(self, request):
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

    @extend_schema(request=EmailCheckSerializer)
    def post(self, request):
        # 로그인된 사용자는 이메일 중복 확인 API에 접근할 수 없도록 처리
        if request.user.is_authenticated:
            raise PermissionDenied({"message": "이미 로그인되어 있습니다."})

        # 이메일 중복 확인 시리얼라이저를 통해 요청 데이터 검증
        serializer = EmailCheckSerializer(data=request.data)

        if serializer.is_valid():
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

    @extend_schema(request=EmailConfirmationSerializer)
    def post(self, request):
        # 로그인된 사용자는 이메일 인증 확인 API에 접근할 수 없도록 처리
        if request.user.is_authenticated:
            raise PermissionDenied({"message": "이미 로그인되어 있습니다."})

        # 시리얼라이저에 데이터 전달
        serializer = EmailConfirmationSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            serializer.send_verification_email(email)  # 이메일 인증 코드 발송
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

    @extend_schema(request=VerifyEmailSerializer)
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
                status=status.HTTP_400_BAD_REQUEST,
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

    @extend_schema(request=ShelterSignupSerializer)
    def post(self, request):
        # 시리얼라이저에 요청 데이터 전달
        serializer = ShelterSignupSerializer(data=request.data)

        # 유효성 검사 및 데이터 저장
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "보호소 회원가입이 완료되었습니다."},
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

    @extend_schema(request=EmailLoginSerializer)
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)

        if serializer.is_valid():
            # 로그인 성공 시, 시리얼라이저에 작성된 validated_data 반환
            return Response(
                {"message": "로그인 성공", **serializer.validated_data},
                status=status.HTTP_200_OK,
            )
        # 유효성 검사 실패 시, 오류 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class KakaoLoginView(APIView):
    permission_classes = [AllowAny]
    serializer_class = KakaoLoginSerializer
    """
    🍒 카카오 로그인과 회원가입API
    """

    @extend_schema(request=KakaoLoginSerializer)
    def post(self, request):
        # 카카오 로그인 시리얼라이저를 통해 요청 데이터 검증
        serializer = KakaoLoginSerializer(data=request.data)

        # 시리얼라이저 검증
        if serializer.is_valid():
            # 유효성 검사를 통과하면 validated_data에 접근하여 JWT 토큰 반환
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        # 유효성 검사 실패 시, 오류 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FindEmailView(APIView):
    permission_classes = [AllowAny]  # 로그인 여부 상관없이 누구나 접근 가능하도록 설정
    serializer_class = FindEmailSerializer
    """
    🍒 아이디 찾기 API
    """

    @extend_schema(request=FindEmailSerializer)
    def post(self, request):
        # 로그인된 사용자는 아이디 찾기 API에 접근할 수 없도록 처리
        if request.user.is_authenticated:
            raise PermissionDenied({"message": "이미 로그인되어 있습니다."})

        # 아이디 찾기 시리얼라이저를 통해 요청 데이터 검증
        serializer = FindEmailSerializer(data=request.data)

        # 시리얼라이저 검증
        if serializer.is_valid():
            # 유효성 검사를 통과하면 validated_data에 접근하여 이메일 반환
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시, 오류 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ResetPasswordSerializer
    """
    🍒 임시비밀번호  API
    """

    @extend_schema(request=ResetPasswordSerializer)
    def post(self, request):
        # 로그인된 사용자는 접근할 수 없도록 설정
        if request.user and request.user.is_authenticated:
            raise PermissionDenied({"message": "이미 로그인된 사용자입니다."})

        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            return Response(
                serializer.validated_data,
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    """
    🍒 비밀번호 변경 API
    """

    @extend_schema(request=ChangePasswordSerializer)
    def put(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(
            user, data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "비밀번호가 성공적으로 변경되었습니다."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    permission_classes = [IsAuthenticated]
    """
    🍒 사용자 정보 조회/수정 API
    """

    # 인증된 사용자만 접근 가능
    @extend_schema(request=UserSerializer)
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

    @extend_schema(request=UserUpdateSerializer)
    def put(self, request):
        # 인증된 사용자 정보 가져오기
        user = request.user

        # UserUpdateSerializer에 현재 사용자 정보와 업데이트할 데이터를 전달하여 시리얼라이징
        serializer = UserUpdateSerializer(
            user, data=request.data, context={"request": request}
        )

        # 시리얼라이저 유효성 검사
        if serializer.is_valid():
            # 정보가 유효하면, 업데이트 작업 후 결과 반환
            updated_user = serializer.save()

            # 수정된 사용자 객체를 시리얼라이즈 후 응답
            updated_data = UserSerializer(updated_user).data
            return Response(
                {
                    "message": "사용자 정보가 성공적으로 수정되었습니다.",
                    "user": updated_data,
                },
                status=status.HTTP_200_OK,
            )

        # 유효성 검사 실패 시, 오류 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    serializer_class = LogoutSerializer
    """
    🍒 로그아웃 API
    """

    @extend_schema(request=LogoutSerializer)
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

    @extend_schema(request=UserDeleteSerializer)
    def post(self, request):
        serializer = UserDeleteSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            request.user.delete()  # 현재 로그인한 유저 삭제
            return Response(
                {"message": "회원 탈퇴가 완료되었습니다."}, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
