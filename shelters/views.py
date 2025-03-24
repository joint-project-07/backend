from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Shelter
from .serializers import ShelterCreateUpdateSerializer, ShelterSerializer


# 🧀 보호소 검색 (GET /api/shelters/search)
class ShelterSearchView(APIView):
    def get(self, request):
        region = request.query_params.get("region")
        date = request.query_params.get("date")
        time = request.query_params.get("time")

        queryset = Shelter.objects.all()

        if region:
            queryset = queryset.filter(region=region)

        # ✅ 날짜 및 시간 조건 필터링
        if date:
            queryset = queryset.filter(recruitments__date=date).distinct()

        if time:
            queryset = queryset.filter(
                Q(recruitments__start_time__lte=time)
                & Q(recruitments__end_time__gte=time)
            ).distinct()

        if not queryset.exists():
            return Response(
                {"error": "해당 조건에 맞는 보호소를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ShelterSerializer(queryset, many=True)
        return Response({"shelters": serializer.data}, status=status.HTTP_200_OK)


# 🧀 보호소 목록 조회 (GET /api/shelters/)
class ShelterListView(APIView):
    def get(self, request):
        queryset = Shelter.objects.all()
        serializer = ShelterSerializer(queryset, many=True)
        return Response({"shelters": serializer.data}, status=status.HTTP_200_OK)


# 🧀 보호소 상세 조회 (GET /api/shelters/{shelter_id}/)
class ShelterDetailView(APIView):
    def get(self, request, pk):
        instance = get_object_or_404(Shelter, pk=pk)
        serializer = ShelterSerializer(instance)
        return Response({"shelter": serializer.data}, status=status.HTTP_200_OK)


# # 🧀 보호소 생성 (POST /api/shelters/create/)
# class ShelterCreateView(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def post(self, request):
#         serializer = ShelterCreateUpdateSerializer(
#             data=request.data, context={"request": request}
#         )
#         if serializer.is_valid():
#             serializer.save()
#             return Response(
#                 {
#
#                     "message": "보호소가 성공적으로 생성되었습니다.",
#                     "shelter_id": serializer.instance.id,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )
#         return Response(
#             {"message": serializer.errors},
#             status=status.HTTP_400_BAD_REQUEST,
#         )


class MyShelterDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # 🧀 보호소 정보 조회 (GET /api/shelters/me/)
    def get(self, request):
        instance = get_object_or_404(Shelter, user=request.user)
        serializer = ShelterSerializer(instance)
        return Response({"shelter": serializer.data}, status=status.HTTP_200_OK)

    # 🧀 보호소 수정 (PATCH /api/shelters/{shelter_id}/update/)
    def patch(self, request):
        instance = get_object_or_404(Shelter, user=request.user)
        serializer = ShelterCreateUpdateSerializer(
            instance, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "보호소 정보가 수정되었습니다.",
                    "shelter": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
