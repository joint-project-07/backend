from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from histories.models import History
from histories.serializers import HistoryRatingSerializer, HistorySerializer


class HistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="봉사활동 이력 조회",
        description="봉사활동 이력을 조회합니다.",
        responses={200: HistorySerializer(many=True)},
    )
    def get(self, request):
        histories = History.objects.filter(user=request.user)
        if not histories.exists():
            return Response(
                {"message": "완료한 봉사활동 기록이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = HistorySerializer(histories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HistoryRatingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="봉사활동 평가",
        description="봉사활동에 대한 만족도 평가를 1 ~ 5 까지 등록합니다.",
        responses={
            200: HistoryRatingSerializer,
            400: {"description": "잘못된 평가 값"},
            404: {"description": "해당 봉사 이력이 없음"},
        },
    )
    def post(self, request, history_id):
        try:
            history = History.objects.get(id=history_id, user=request.user)
        except History.DoesNotExist:
            return Response(
                {"message": "해당 봉사 이력을 찾을 수 없습니다."},
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
