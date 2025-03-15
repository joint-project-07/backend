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
    ResetPasswordSerializer,
    ShelterSignupSerializer,
    SignupSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class SignupView(APIView):
    permission_classes = [AllowAny]
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
    """
    🍒이메일 중복 확인 API
    """

    @extend_schema(request=EmailCheckSerializer)
    def post(self, request):
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
    permission_classes = [AllowAny]
    """
    🍒이메일 인증 확인 API
    """

    @extend_schema(request=EmailConfirmationSerializer)
    def post(self, request):
        serializer = EmailConfirmationSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            serializer.send_confirmation_email(email)
            return Response(
                {"message": "이메일 인증을 위한 링크가 전송되었습니다."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShelterSignupView(APIView):
    permission_classes = [AllowAny]
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
    """
    🍒 아이디 찾기 API
    """

    permission_classes = [AllowAny]  # 로그인 여부 상관없이 누구나 접근 가능하도록 설정

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
    """
    🍒 임시비밀번호  API
    """

    @extend_schema(request=ResetPasswordSerializer)
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            # 비밀번호 재설정 성공 시, 시리얼라이저에서 반환된 데이터
            return Response(
                serializer.validated_data,  # 유효한 데이터를 그대로 반환
                status=status.HTTP_200_OK,
            )
        # 유효성 검사 실패 시, 오류 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    🍒 비밀번호 변경 API
    """

    permission_classes = [IsAuthenticated]

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
    """
    🍒 사용자 정보 조회/수정 API
    """

    permission_classes = [IsAuthenticated]

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
    """
    🍒 로그아웃 API
    """

    @extend_schema()
    def post(self, request):
        # 사용자 인증 정보 확인 (Authorization 헤더에서 토큰 추출)
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"message": "refresh_token이 필요합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Refresh Token을 받아서 만료 처리
            token = RefreshToken(refresh_token)
            token.blacklist()  # 토큰을 블랙리스트에 추가하여 만료시킴

            # 성공 응답
            return Response(
                {"message": "성공적으로 로그아웃 되었습니다."},
                status=status.HTTP_200_OK,
            )
        # 예기치 않은 예외들을 처리
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
