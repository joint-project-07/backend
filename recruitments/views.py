from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Application
from applications.serializers import ApplicationSerializer
from common.utils import delete_file_from_s3, upload_file_to_s3, validate_file_extension

from .models import Recruitment, RecruitmentImage
from .serializers import (  # RecruitmentImageUploadSerializer,
    RecruitmentApplicantSerializer,
    RecruitmentCreateUpdateSerializer,
    RecruitmentImageSerializer,
    RecruitmentSerializer,
)


# 🧀 봉사활동 검색 (GET /api/recruitments/search)
@extend_schema(
    summary="봉사활동 검색",
    parameters=[
        OpenApiParameter(
            name="region",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="쉼표로 구분된 최대 3개 지역 (예: 서울,경기,인천)",
        ),
        OpenApiParameter(
            name="start_date", type=str, location=OpenApiParameter.QUERY, required=False
        ),
        OpenApiParameter(
            name="end_date", type=str, location=OpenApiParameter.QUERY, required=False
        ),
        OpenApiParameter(
            name="time", type=str, location=OpenApiParameter.QUERY, required=False
        ),
    ],
    responses={200: RecruitmentSerializer(many=True)},
)
class RecruitmentSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Recruitment.objects.all()

        # ✅ 지역 필터링
        region_param = request.query_params.get("region")
        regions = region_param.split(",") if region_param else []

        if regions:
            q = Q()
            for region in regions[:3]:  # 최대 3개까지 처리
                q |= Q(shelter__region=region.strip())
            queryset = queryset.filter(q)

        # ✅ 날짜 범위 필터링
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        # ✅ 시간 필터링
        time = request.query_params.get("time")
        if time:
            queryset = queryset.filter(Q(start_time__lte=time) & Q(end_time__gte=time))

        if not queryset.exists():
            return Response(
                {"error": "해당 조건에 맞는 봉사활동을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RecruitmentSerializer(queryset, many=True)
        return Response({"recruitments": serializer.data}, status=status.HTTP_200_OK)


# 🧀 봉사활동 전체 조회
@extend_schema(
    summary="봉사활동 전체 목록 조회",
    responses={200: RecruitmentSerializer(many=True)},
)
class RecruitmentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        queryset = Recruitment.objects.all()
        serializer = RecruitmentSerializer(queryset, many=True)
        return Response({"recruitments": serializer.data}, status=status.HTTP_200_OK)


# 🧀 봉사활동 상세 조회
@extend_schema(summary="봉사활동 상세 조회", responses={200: RecruitmentSerializer})
class RecruitmentDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        recruitment = Recruitment.objects.filter(pk=pk).first()
        if not recruitment:
            return Response(
                {"error": "봉사활동을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = RecruitmentSerializer(recruitment)
        return Response({"recruitment": serializer.data}, status=status.HTTP_200_OK)


# 🧀 봉사활동 등록
@extend_schema(
    summary="봉사활동 등록",
    request=RecruitmentCreateUpdateSerializer,
    responses={201: dict},
)
class RecruitmentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        shelter = request.user.shelter
        data = request.data.copy()
        data["shelter"] = shelter.id

        serializer = RecruitmentCreateUpdateSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "code": 201,
                    "message": "봉사활동이 성공적으로 등록되었습니다.",
                    "recruitment_id": serializer.instance.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"code": 400, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


# 등록한 봉사활동 목록 조회
class MyRecruitmentListView(APIView):
    @extend_schema(
        summary="등록한 봉사활동 조회",
        responses={200: RecruitmentSerializer(many=True)},
    )
    def get(self, request):
        shelter = request.user.shelter  # 현재 로그인한 사용자의 보호소 정보 가져오기
        if not shelter:
            return Response(
                {"error": "보호소 관리자만 조회할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = Recruitment.objects.filter(shelter=shelter)
        if not queryset.exists():
            return Response(
                {"message": "등록한 봉사활동이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RecruitmentSerializer(queryset, many=True)
        return Response({"recruitments": serializer.data}, status=status.HTTP_200_OK)


# 특정 봉사활동 신청자 목록 조회
class RecruitmentApplicantView(APIView):
    @extend_schema(
        summary="특정 봉사활동 신청자 목록 조회",
        responses={200: RecruitmentApplicantSerializer(many=True)},
    )
    def get(self, request, recruitment_id):
        shelter = request.user.shelter
        recruitment = Recruitment.objects.filter(
            id=recruitment_id, shelter=shelter
        ).first()

        if not recruitment:
            return Response(
                {"error": "해당 봉사활동을 찾을 수 없습니다."},
                status.HTTP_404_NOT_FOUND,
            )

        applications = Application.objects.filter(
            recruitment=recruitment
        ).select_related("user")
        if not applications.exists():
            return Response(
                {"message": "신청한 봉사자가 없습니다."}, status.HTTP_404_NOT_FOUND
            )

        users = [app.user for app in applications]
        serializer = RecruitmentApplicantSerializer(users, many=True)
        return Response({"applicants": serializer.data}, status=status.HTTP_200_OK)


# 🧀 봉사활동 수정
@extend_schema(
    summary="봉사활동 수정", request=RecruitmentSerializer, responses={200: dict}
)
class RecruitmentUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        shelter = request.user.shelter
        recruitment = Recruitment.objects.filter(pk=pk, shelter=shelter).first()

        if not recruitment:
            return Response(
                {"error": "봉사활동을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RecruitmentSerializer(recruitment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "code": 200,
                    "message": "봉사활동이 성공적으로 수정되었습니다.",
                    "recruitment_id": serializer.instance.id,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"code": 400, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RecruitmentImageView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    # 특정 봉사활동의 모든 이미지 조회
    @extend_schema(
        summary="봉사활동 이미지 조회",
        responses={200: RecruitmentImageSerializer(many=True)},
    )
    def get(self, request, recruitment_id):
        images = RecruitmentImage.objects.filter(recruitment_id=recruitment_id)

        if not images.exists():
            return Response(
                {"error": "해당 봉사활동에 등록된 이미지가 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            RecruitmentImageSerializer(images, many=True).data,
            status=status.HTTP_200_OK,
        )


class RecruitmentImageDeleteView(APIView):
    # 봉사 활동 이미지 개별 삭제
    @extend_schema(summary="봉사활동 이미지 삭제", responses={204: None})
    def delete(self, request, image_id):
        image = RecruitmentImage.objects.filter(id=image_id).first()

        if not image:
            return Response(
                {"error": "해당 이미지를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # S3 에서 삭제
        try:
            delete_file_from_s3(image.image_url)
            image.delete()
            return Response(
                {"message": "이미지 삭제가 완료되었습니다."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "이미지 삭제에 실패하였습니다.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
