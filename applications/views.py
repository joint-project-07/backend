from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from applications.models import Application
from applications.serializers import ApplicationSerializer, ApplicationCreateSerializer


class ApplicationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # 신청한 봉사 목록 조회
    @extend_schema(
        summary="신청한 봉사 목록 조회",
        description = "현재 로그인한 사용자의 봉사 신청 목록을 조회합니다.",
    )
    def get(self, request):
        applications = Application.objects.filter(user=request.user)
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 봉사 신청
    @extend_schema(
        summary="봉사 신청 생성",
        description="봉사 모집 공고에 대한 신청을 생성합니다.",
    )
    def post(self, request):
        serializer = ApplicationCreateSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            application = serializer.save()
            return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # 봉사 신청 내역 상세 조회
    @extend_schema(
        summary="봉사 신청 상세 조회",
        description="특정 봉사 신청 정보를 조회합니다.",
    )
    def get(self, request, pk):
        try:
            application = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response({"detail": "해당 신청을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 봉사 신청 취소
    @extend_schema(
        summary="봉사 신청 취소",
        description="특정 봉사 신청을 취소(삭제)합니다.",
    )
    def delete(self, request, pk):
        try:
            application = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response({"detail": "해당 신청을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplicationApproveRejectView(APIView):
    permission_classes = [IsAuthenticated]

    # 봉사 신청 승인
    @extend_schema(
        summary="봉사 신청 승인",
        description="보호소 관리자가 특정 봉사 신청을 승인합니다.",
    )
    def post(self, request, pk):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response({"detail": "해당 신청을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if application.shelter.user != request.user:
            return Response({"detail": "승인 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        application.status = "approved"
        application.save()
        return Response(ApplicationSerializer(application).data, status=status.HTTP_200_OK)


class ApplicationRejectView(APIView):
    permission_classes = [IsAuthenticated]

    # 봉사 신청 거절
    @extend_schema(
        summary="봉사 신청 거절",
        description="보호소 관리자가 특정 봉사 신청을 거절합니다.",
    )
    def post(self, request, pk):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response({"detail": "해당 신청을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if application.shelter.user != request.user:
            return Response({"detail": "거절 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        rejected_reason = request.data("rejected_reason", "")
        application.status = "rejected"
        application.rejected_reason = rejected_reason
        application.save()

        return Response(ApplicationSerializer(application).data, status=status.HTTP_200_OK)