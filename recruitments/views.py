from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Recruitment
from .serializers import RecruitmentSerializer


# 🧀 봉사활동 검색
class RecruitmentSearchView(generics.ListAPIView):
    serializer_class = RecruitmentSerializer

    def get_queryset(self):
        queryset = Recruitment.objects.all()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        time = self.request.query_params.get('time')

        # ✅ 날짜 필터링 (범위 검색)
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        # ✅ 시간 필터링 (특정 시간 범위 검색)
        if time:
            queryset = queryset.filter(
                Q(start_time__lte=time) & Q(end_time__gte=time)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"error": "해당 조건에 맞는 봉사활동을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"recruitments": serializer.data}, status=status.HTTP_200_OK
        )


# 🧀 봉사활동 전체 조회
class RecruitmentListView(generics.ListAPIView):
    queryset = Recruitment.objects.all()
    serializer_class = RecruitmentSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"recruitments": serializer.data}, status=status.HTTP_200_OK
        )


# 🧀 봉사활동 상세 조회
class RecruitmentDetailView(generics.RetrieveAPIView):
    queryset = Recruitment.objects.all()
    serializer_class = RecruitmentSerializer
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            {"recruitment": serializer.data}, status=status.HTTP_200_OK
        )


# 🧀 봉사활동 등록 → shelter_id 자동 추출 수정됨
class RecruitmentCreateView(generics.CreateAPIView):
    serializer_class = RecruitmentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # ✅ shelter_id 자동 추출 추가
        shelter = request.user.shelter
        data = request.data.copy()
        data["shelter"] = shelter.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            {
                "code": 201,
                "message": "봉사활동이 성공적으로 등록되었습니다.",
                "recruitment_id": serializer.instance.id,
            },
            status=status.HTTP_201_CREATED,
        )


# 🧀 봉사활동 수정 → shelter_id 자동 추출 수정됨
class RecruitmentUpdateView(generics.UpdateAPIView):
    queryset = Recruitment.objects.all()
    serializer_class = RecruitmentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        shelter = self.request.user.shelter
        return self.get_queryset().get(pk=self.kwargs["pk"], shelter=shelter)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "code": 201,
                "message": "봉사활동이 성공적으로 수정되었습니다.",
                "recruitment_id": serializer.instance.id,
            },
            status=status.HTTP_201_CREATED,
        )
