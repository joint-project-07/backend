from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Application
from applications.serializers import ApplicationCreateSerializer, ApplicationSerializer, ApplicationRejectSerializer
from recruitments.models import Recruitment


class ApplicationListCreateView(APIView):
    # 신청한 봉사 목록 조회
    @extend_schema(
        summary="신청한 봉사 목록 조회",
        description="현재 로그인한 사용자의 봉사 신청 목록을 조회합니다.",
        responses={200: ApplicationSerializer(many=True),
                   404: {"example": {"detail": "봉사 신청 내역을 찾을 수 없습니다."}}
        },
    )
    def get(self, request):
        try:
            applications = Application.objects.filter(user=request.user)
        except Application.DoesNotExist:
            return Response({"detail": "봉사 신청 내역을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 봉사 신청
    @extend_schema(
        summary="봉사 신청 생성",
        description="봉사 모집 공고에 대한 신청을 생성합니다.",
        request=ApplicationCreateSerializer,
        responses={
            201: ApplicationSerializer,
            403: {"example": {"detail": "봉사활동 신청은 회원만 가능합니다."}},
            404: {"example": {"detail": "해당 봉사활동을 찾을 수 없습니다."}},
            409: {"example": {"detail": "이미 신청한 봉사활동이거나, 기존 신청과 시간이 중복됩니다."}},
        },
    )
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "봉사활동 신청은 회원만 가능합니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ApplicationCreateSerializer(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        recruitments_id = request.data.get("recruitment")

        try:
            recruitment = Recruitment.objects.get(id=recruitments_id)
        except Recruitment.DoesNotExist:
            return Response({"detail": "해당 봉사활동을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 이미 해당 봉사활동에 신청했는지 확인
        if Application.objects.filter(user=request.user, recruitment=recruitment).exists():
            return Response({"detail": "이미 신청한 봉사활동 입니다."}, status=status.HTTP_409_CONFLICT)

        # 기존 신청한 봉사활동과 시간이 겹치는지 확인
        user_applications = Application.objects.filter(user=request.user)
        for application in user_applications:
            existing_recruitment = application.recruitment
            if (existing_recruitment.start_time < recruitment.end_time and recruitment.start_time < existing_recruitment.end_time):
                return Response({"detail": "중복된 시간에 신청한 봉사활동이 있습니다."}, status=status.HTTP_409_CONFLICT)

            application = serializer.save()
            return Response(
                ApplicationSerializer(application).data, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicationDetailView(APIView):
    # 봉사 신청 내역 상세 조회
    @extend_schema(
        summary="봉사 신청 상세 조회",
        description="특정 봉사 신청 정보를 조회합니다.",
        responses={200: ApplicationSerializer(many=True),
                   404: {"example": {"detail": "해당 신청을 찾을 수 없습니다."}},
        },
    )
    def get(self, request, pk):
        try:
            application = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response(
                {"detail": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 봉사 신청 취소
    @extend_schema(
        summary="봉사 신청 취소",
        description="특정 봉사 신청을 취소(삭제)합니다.",
        responses={
            200: {"example": {"detail": "신청이 취소되었습니다."}},
            404: {"example": {"detail": "해당 봉사 신청 내역을 찾을 수 없습니다."}},
        },
    )
    def delete(self, request, pk):
        try:
            application = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response(
                {"detail": "해당 신청을 찾을 수 없습니다."},
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
            403: {"example": {"detail": "승인 권한이 없습니다."}},
            404: {"example": {"detail": "해당 신청을 찾을 수 없습니다."}},
        },
    )
    def post(self, request, pk):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {"detail": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.shelter.user != request.user:
            return Response(
                {"detail": "승인 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
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
            403: {"example": {"detail": "거절 권한이 없습니다."}},
            404: {"example": {"detail": "해당 신청을 찾을 수 없습니다."}},
        },
    )
    def post(self, request, pk):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response(
                {"detail": "해당 신청을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.shelter.user != request.user:
            return Response(
                {"detail": "거절 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )

        rejected_reason = request.data.get("rejected_reason", "").strip()
        if not rejected_reason:
            return Response({"detail": "거절 사유를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        application.status = "rejected"
        application.rejected_reason = rejected_reason
        application.save()

        return Response(
            ApplicationSerializer(application).data, status=status.HTTP_200_OK
        )
