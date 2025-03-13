from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
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
    """
    🍒봉사자 회원가입 API
    """

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        # 유효성 검사 및 데이터 저장
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"code": 201, "message": "회원가입이 완료되었습니다."},
                status=status.HTTP_201_CREATED,
            )

        # 유효성 검사 실패 시, 오류 반환
        errors = serializer.errors

        # errors에서 code가 있으면 그 값을 상태 코드로 설정
        if errors:
            code = errors.get("code", 400)  # code없으면 기본적으로 400 설정
            return Response(errors, status=code)


class ShelterSignupView(APIView):
    """
    🍒보호소 회원가입 API
    """

    def post(self, request):
        # 시리얼라이저에 요청 데이터 전달
        serializer = ShelterSignupSerializer(data=request.data)

        # 유효성 검사 및 데이터 저장
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"code": 201, "message": "보호소 회원가입이 완료되었습니다."},
                status=status.HTTP_201_CREATED,
            )

        # 유효성 검사 실패 시, 오류 반환
        errors = serializer.errors

        # errors에서 code가 있으면 그 값을 상태 코드로 설정
        if errors:
            code = errors.get("code", 400)  # code없으면 기본적으로 400 설정
            return Response(errors, status=code)


class EmailLoginView(APIView):
    """
    🍒이메일 로그인 API
    """

    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)

        if serializer.is_valid():
            # 로그인 성공 시, 시리얼라이저에 작성된 validated_data 반환
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시, 오류 반환
        errors = serializer.errors

        # errors에서 code가 있으면 그 값을 상태 코드로 설정
        if errors:
            code = errors.get("code", 400)  # code없으면 기본적으로 400 설정
            return Response(errors, status=code)


class KakaoLoginView(APIView):
    """
    🍒 카카오 로그인과 회원가입API
    """

    def post(self, request):
        # 카카오 로그인 시리얼라이저를 통해 요청 데이터 검증
        serializer = KakaoLoginSerializer(data=request.data)

        # 시리얼라이저 검증
        if serializer.is_valid():
            # 유효성 검사를 통과하면 validated_data에 접근하여 JWT 토큰 반환
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시, 오류 반환
        errors = serializer.errors

        # errors에서 code가 있으면 그 값을 상태 코드로 설정
        if errors:
            code = errors.get("code", 400)  # code없으면 기본적으로 400 설정
            return Response(errors, status=code)


class FindEmailView(APIView):
    """
    🍒 아이디 찾기 API
    """

    def post(self, request):
        # 아이디 찾기 시리얼라이저를 통해 요청 데이터 검증
        serializer = FindEmailSerializer(data=request.data)

        # 시리얼라이저 검증
        if serializer.is_valid():
            # 유효성 검사를 통과하면 validated_data에 접근하여 이메일 반환
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시, 오류 반환
        errors = serializer.errors

        # errors에서 code가 있으면 그 값을 상태 코드로 설정
        if errors:
            code = errors.get("code", 400)  # code없으면 기본적으로 400 설정
            return Response(errors, status=code)


class ResetPasswordView(APIView):
    """
    🍒 비밀번호 재설정 API
    """

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            # 비밀번호 재설정 성공 시, 시리얼라이저에서 반환된 데이터
            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시, 오류 반환
        errors = serializer.errors

        # errors에서 code가 있으면 그 값을 상태 코드로 설정
        if errors:
            code = errors.get("code", 400)  # code가 없으면 기본적으로 400 설정
            return Response(errors, status=code)


class UserView(APIView):
    """
    🍒 사용자 정보 조회/수정 API
    """

    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get(self, request):
        # 인증된 사용자 정보 가져오기
        user = request.user

        # 사용자의 정보를 반환
        serializer = UserSerializer(user)

        # 원하는 형식으로 응답 데이터
        response_data = {
            "code": 200,
            "user": serializer.data,  # user 정보는 시리얼라이저에서 반환된 데이터
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def put(self, request):
        # 인증된 사용자 정보 가져오기
        user = request.user

        # UserUpdateSerializer에 현재 사용자 정보와 업데이트할 데이터를 전달하여 시리얼라이징
        serializer = UserUpdateSerializer(user, data=request.data)

        # 시리얼라이저 유효성 검사
        if serializer.is_valid():
            # 정보가 유효하면, 업데이트 작업 후 결과 반환
            updated_data = serializer.save()  # 성공적으로 저장된 데이터 반환
            return Response(updated_data, status=status.HTTP_200_OK)

        # 유효성 검사 실패 시, 오류 반환
        errors = serializer.errors

        # errors에서 code가 있으면 그 값을 상태 코드로 설정
        if errors:
            code = errors.get("code", 400)  # code없으면 기본적으로 400 설정
            return Response(errors, status=code)


class LogoutView(APIView):
    """
    🍒 로그아웃 API
    """

    def post(self, request):
        # 사용자 인증 정보 확인 (Authorization 헤더에서 토큰 추출)
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return Response(
                    {"code": 400, "message": "refresh_token이 필요합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Refresh Token을 받아서 만료 처리
            token = RefreshToken(refresh_token)
            token.blacklist()  # 토큰을 블랙리스트에 추가하여 만료시킴

            # 성공 응답
            return Response(
                {"code": 200, "message": "성공적으로 로그아웃 되었습니다."},
                status=status.HTTP_200_OK,
            )
        # 예기치 않은 예외들을 처리
        except Exception as e:
            return Response(
                {"code": 400, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
