from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from histories.models import History
from histories.serializers import HistoryRatingSerializer, HistorySerializer


class HistoryAPIView(APIView):
    # 봉사자가 완료한 봉사 이력 조회
    @extend_schema(
        summary="완료한 봉사활동 이력 조회",
        description="봉사자가 완료한 봉사활동 이력을 조회합니다.",
        responses={
            200: HistorySerializer(many=True),
            404: {"example": {"error": "완료한 봉사활동 기록이 없습니다."}},
        },
    )
    def get(self, request):
        histories = History.objects.filter(
            user=request.user, application__status="attended"
        )

        if not histories.exists():
            return Response(
                {"error": "완료한 봉사활동 기록이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HistorySerializer(histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HistoryRatingAPIView(APIView):
    # 보호소 평가
    @extend_schema(
        summary="보호소 평가",
        description="봉사자가 자신이 완료한 봉사활동을 기반으로 보호소에 점수를 부여합니다.",
        responses={
            200: HistoryRatingSerializer,
            404: {"example": {"error": "해당 봉사 이력을 찾을 수 없습니다."}},
        },
    )
    def post(self, request, history_id):
        try:
            history = History.objects.get(id=history_id, user=request.user)

            if history.application.status != "attended":
                return Response(
                    {"error": "완료된 봉사활동에 대해서만 평가할 수 있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except History.DoesNotExist:
            return Response(
                {"error": "해당 봉사 이력을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HistoryRatingSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        history.rating = request.validated_data["rating"]
        history.save()

        return Response(
            {"message": "만족도 평가가 등록되었습니다."}, status=status.HTTP_200_OK
        )
