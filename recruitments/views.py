from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import delete_file_from_s3, upload_file_to_s3, validate_file_extension

from .models import Recruitment, RecruitmentImage
from .serializers import RecruitmentImageSerializer, RecruitmentSerializer


# 🧀 봉사활동 검색
@extend_schema(
    summary="봉사활동 검색",
    parameters=[
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
    def get(self, request):
        queryset = Recruitment.objects.all()
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        time = request.query_params.get("time")

        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])
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
    summary="봉사활동 전체 목록 조회", responses={200: RecruitmentSerializer(many=True)}
)
class RecruitmentListView(APIView):
    def get(self, request):
        queryset = Recruitment.objects.all()
        serializer = RecruitmentSerializer(queryset, many=True)
        return Response({"recruitments": serializer.data}, status=status.HTTP_200_OK)


# 🧀 봉사활동 상세 조회
@extend_schema(summary="봉사활동 상세 조회", responses={200: RecruitmentSerializer})
class RecruitmentDetailView(APIView):
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
    summary="봉사활동 등록", request=RecruitmentSerializer, responses={201: dict}
)
class RecruitmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        shelter = request.user.shelter
        data = request.data.copy()
        data["shelter"] = shelter.id

        serializer = RecruitmentSerializer(data=data)
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


# 🧀 봉사활동 이미지 업로드 & 조회
class RecruitmentImageView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="봉사활동 이미지 업로드",
        request={"multipart/form-data": {"image": "file[]"}},
        responses={201: RecruitmentImageSerializer(many=True)},
    )
    def post(self, request, recruitment_id):
        files = request.FILES.getlist("image")

        if not files:
            return Response(
                {"error": "이미지를 업로드해야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recruitment = Recruitment.objects.filter(id=recruitment_id).first()
        if not recruitment:
            return Response(
                {"error": "해당 봉사활동을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        uploaded_images = []
        for file in files:
            try:
                validate_file_extension(file, "recruitments")
                image_url = upload_file_to_s3(file, "recruitments", recruitment_id)
                image = RecruitmentImage.objects.create(
                    recruitment=recruitment, image_url=image_url
                )
                uploaded_images.append(image)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            RecruitmentImageSerializer(uploaded_images, many=True).data,
            status=status.HTTP_201_CREATED,
        )

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


# 🧀 봉사활동 이미지 삭제
@extend_schema(summary="봉사활동 이미지 삭제", responses={204: None})
class RecruitmentImageDeleteView(APIView):
    def delete(self, request, image_id):
        image = RecruitmentImage.objects.filter(id=image_id).first()

        if not image:
            return Response(
                {"error": "해당 이미지를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            delete_file_from_s3(image.image_url)
            image.delete()
            return Response(
                {"message": "이미지 삭제가 완료되었습니다."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "이미지 삭제에 실패했습니다.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
