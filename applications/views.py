from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Application
from applications.serializers import (
    ApplicationCreateSerializer,
    ApplicationRejectSerializer,
    ApplicationSerializer,
)
from recruitments.models import Recruitment


class ApplicationListCreateView(APIView):
    # 신청한 봉사 목록 조회
    @extend_schema(
        summary="신청한 봉사 목록 조회",
        description="현재 로그인한 사용자의 봉사 신청 목록을 조회합니다.",
        responses={
            200: ApplicationSerializer(many=True),
            404: {"example": {"detail": "봉사 신청 내역을 찾을 수 없습니다."}},
        },
    )
    def get(self, request):
        try:
            applications = Application.objects.filter(user=request.user)
        except Application.DoesNotExist:
            return Response(
                {"detail": "봉사 신청 내역을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 봉사 신청
    @extend_schema(
        summary="봉사 신청 생성",
        description="봉사 모집 공고에 대한 신청을 생성합니다.",
        request=ApplicationCreateSerializer,
        responses={
            201: ApplicationSerializer,
            400: {
                "example": {
                    "error": "입력 데이터가 올바르지 않습니다.",
                    "details": {"recruitment": ["이 필드는 필수 항목입니다."]},
                }
            },
            403: {"example": {"error": "봉사활동 신청은 회원만 가능합니다."}},
            404: {"example": {"error": "해당 봉사활동을 찾을 수 없습니다."}},
            409: {
                "example": {
                    "error": "이미 신청한 봉사활동이거나, 기존 신청과 시간이 중복됩니다."
                }
            },
        },
    )
    def post(self, request):
        user = request.user  # 현재 로그인한 사용자 정보 가져오기

        # 봉사자로 회원가입한 사용자만 신청할 수 있도록 제한
        if user.is_shelter:
            return Response(
                {"error": "보호소 관계자는 봉사 신청을 할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ApplicationCreateSerializer(
            data=request.data, context={"request": request}
        )

        # serializer 가 유효하지 않을 경우, 필드별 오류 메세지 반환
        if not serializer.is_valid():
            return Response(
                {
                    "error": "입력 데이터가 올바르지 않습니다.",
                    "details": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        recruitments_id = request.data.get("recruitment")  # 신청할 봉사활동 ID 가져오기

        # 해당 봉사활동이 존재하는지 확인
        try:
            recruitment = Recruitment.objects.get(id=recruitments_id)
        except Recruitment.DoesNotExist:
            return Response(
                {"error": "해당 봉사활동을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 이미 해당 봉사활동에 신청했는지 확인
        if Application.objects.filter(
            user=request.user, recruitment=recruitment
        ).exists():
            return Response(
                {"error": "이미 신청한 봉사활동 입니다."},
                status=status.HTTP_409_CONFLICT,
            )

        # 기존 신청한 봉사활동과 시간이 겹치는지 확인
        overlapping_applications = Application.objects.filter(
            user=request.user,
            recruitment__start_time__lt=recruitment.end_time,
            recruitment__end_time__gt=recruitment.start_time,
        ).exists()

        if overlapping_applications:
            return Response(
                {"error": "중복된 시간에 신청한 봉사활동이 있습니다."},
                status=status.HTTP_409_CONFLICT,
            )

        try:
            application = serializer.save()
            return Response(
                ApplicationSerializer(application).data, status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {
                    "error": "신청을 처리하는 중 오류가 발생했습니다.",
                    "details": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class ApplicationDetailView(APIView):
    # 봉사 신청 내역 상세 조회
    @extend_schema(
        summary="봉사 신청 상세 조회",
        description="특정 봉사 신청 정보를 조회합니다.",
        responses={
            200: ApplicationSerializer(many=True),
            404: {"example": {"error": "해당 신청을 찾을 수 없습니다."}},
        },
    )
    def get(self, request, application_id):
        try:
            application = Application.objects.get(pk=application_id, user=request.user)
        except Application.DoesNotExist:
            return Response(
                {"error": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 봉사 신청 취소
    @extend_schema(
        summary="봉사 신청 취소",
        description="특정 봉사 신청을 취소(삭제)합니다.",
        responses={
            200: {"example": {"error": "신청이 취소되었습니다."}},
            404: {"example": {"error": "해당 봉사 신청 내역을 찾을 수 없습니다."}},
        },
    )
    def delete(self, request, application_id):
        try:
            application = Application.objects.get(pk=application_id, user=request.user)
        except Application.DoesNotExist:
            return Response(
                {"error": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplicationApproveRejectView(APIView):
    # 봉사 신청 승인
    @extend_schema(
        summary="봉사 신청 승인",
        description="보호소 관리자가 특정 봉사 신청을 승인합니다.",
        responses={
            200: ApplicationSerializer,
            403: {"example": {"error": "승인 권한이 없습니다."}},
            404: {"example": {"error": "해당 신청을 찾을 수 없습니다."}},
        },
    )
    def post(self, request, application_id):
        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response(
                {"error": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.shelter.user != request.user:
            return Response(
                {"error": "승인 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        application.status = "approved"
        application.save()
        return Response(
            ApplicationSerializer(application).data, status=status.HTTP_200_OK
        )


class ApplicationRejectView(APIView):
    # 봉사 신청 거절
    @extend_schema(
        summary="봉사 신청 거절",
        description="보호소 관리자가 특정 봉사 신청을 거절합니다.",
        request=ApplicationRejectSerializer,
        responses={
            200: ApplicationSerializer,
            400: {"example": {"error": "거절 사유를 입력해주세요."}},
            403: {"example": {"error": "거절 권한이 없습니다."}},
            404: {"example": {"error": "해당 신청을 찾을 수 없습니다."}},
        },
    )
    def post(self, request, application_id):
        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response(
                {"error": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.shelter.user != request.user:
            return Response(
                {"error": "거절 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        rejected_reason = request.data.get("rejected_reason", "").strip()
        if not rejected_reason:
            return Response(
                {"error": "거절 사유를 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.status = "rejected"
        application.rejected_reason = rejected_reason
        application.save()

        return Response(
            ApplicationSerializer(application).data, status=status.HTTP_200_OK
        )


class ApplicationAttendView(APIView):
    # 봉사 활동 완료
    @extend_schema(
        summary="봉사 활동 완료 ",
        description="보호소 관리자가 봉사 완료한 봉사자를 완료 처리합니다.",
        responses={
            200: ApplicationSerializer,
            403: {"example": {"error": "승인 권한이 없습니다."}},
            404: {"example": {"error": "해당 봉사 활동을 찾을 수 없습니다."}},
        },
    )
    def post(self, request, application_id):
        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response(
                {"error": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.shelter.user != request.user:
            return Response(
                {"error": "승인 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        application.status = "attended"
        application.save()
        return Response(
            ApplicationSerializer(application).data, status=status.HTTP_200_OK
        )


class ApplicationAbsenceView(APIView):
    # 봉사 활동 불참
    @extend_schema(
        summary="봉사 활동 불참",
        description="보호소 관리자가 불참한 봉사자를 불참 처리합니다.",
        responses={
            200: ApplicationSerializer,
            403: {"example": {"error": "승인 권한이 없습니다."}},
            404: {"example": {"error": "해당 봉사 활동을 찾을 수 없습니다."}},
        },
    )
    def post(self, request, application_id):
        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            return Response(
                {"error": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.shelter.user != request.user:
            return Response(
                {"error": "승인 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        application.status = "absence"
        application.save()
        return Response(
            ApplicationSerializer(application).data, status=status.HTTP_200_OK
        )
