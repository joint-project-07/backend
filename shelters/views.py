from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Shelter
from .serializers import ShelterSerializer, ShelterUpdateSerializer


# 🧀 보호소 검색 (GET /api/shelters/search)
class ShelterSearchView(generics.ListAPIView):
    serializer_class = ShelterSerializer

    def get_queryset(self):
        region = self.request.query_params.get("region")
        queryset = Shelter.objects.all()

        if region:
            queryset = queryset.filter(region=region)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "해당 조건에 맞는 보호소를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response({"shelters": serializer.data}, status=status.HTTP_200_OK)


# 🧀 보호소 목록 조회 (GET /api/shelters/)
class ShelterListView(generics.ListAPIView):
    queryset = Shelter.objects.all()
    serializer_class = ShelterSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"shelters": serializer.data}, status=status.HTTP_200_OK)


# 🧀 보호소 상세 조회 (GET /api/shelters/{shelter_id}/)
class ShelterDetailView(generics.RetrieveAPIView):
    queryset = Shelter.objects.all()
    serializer_class = ShelterSerializer
    lookup_field = "pk"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"shelter": serializer.data}, status=status.HTTP_200_OK)


# 🧀 보호소 정보 수정 (PATCH /api/shelters/me/)
class ShelterUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShelterUpdateSerializer

    def get_object(self):
        return get_object_or_404(Shelter, user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "code": 200,
                "message": "보호소 정보가 수정되었습니다.",
                "shelter": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# 🧀 보호소 정보 조회 (GET /api/shelters/me/)
class MyShelterDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ShelterSerializer

    def get_object(self):
        return get_object_or_404(Shelter, user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"code": 200, "shelter": serializer.data}, status=status.HTTP_200_OK
        )
