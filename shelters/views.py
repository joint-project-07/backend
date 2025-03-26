from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import delete_file_from_s3, upload_file_to_s3, validate_file_extension

from .models import Shelter
from .serializers import (
    ShelterBusinessLicenseSerializer,
    ShelterCreateUpdateSerializer,
    ShelterSerializer,
)


@extend_schema(
    summary="보호소 검색",
    parameters=[
        OpenApiParameter(
            name="region", type=str, location=OpenApiParameter.QUERY, required=False
        ),
        OpenApiParameter(
            name="date", type=str, location=OpenApiParameter.QUERY, required=False
        ),
        OpenApiParameter(
            name="time", type=str, location=OpenApiParameter.QUERY, required=False
        ),
    ],
    responses={200: ShelterSerializer(many=True)},
)
class ShelterSearchView(APIView):
    def get(self, request):
        region = request.query_params.get("region")
        date = request.query_params.get("date")
        time = request.query_params.get("time")

        queryset = Shelter.objects.all()

        if region:
            queryset = queryset.filter(region=region)

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


@extend_schema(
    summary="보호소 전체 목록 조회", responses={200: ShelterSerializer(many=True)}
)
class ShelterListView(APIView):
    permission_classes = [AllowAny]  # 👈 여기에 추가

    def get(self, request):
        queryset = Shelter.objects.all()
        serializer = ShelterSerializer(queryset, many=True)
        return Response({"shelters": serializer.data}, status=status.HTTP_200_OK)


@extend_schema(summary="보호소 상세 조회", responses={200: ShelterSerializer})
class ShelterDetailView(APIView):
    def get(self, request, pk):
        instance = get_object_or_404(Shelter, pk=pk)
        serializer = ShelterSerializer(instance)
        return Response({"shelter": serializer.data}, status=status.HTTP_200_OK)


@extend_schema(summary="보호소 정보 조회", responses={200: ShelterSerializer})
@extend_schema(
    methods="patch",
    summary="보호소 정보 수정",
    request=ShelterCreateUpdateSerializer,
    responses={200: ShelterCreateUpdateSerializer},
)
class MyShelterDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        instance = get_object_or_404(Shelter, user=request.user)
        serializer = ShelterSerializer(instance)
        return Response({"shelter": serializer.data}, status=status.HTTP_200_OK)

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


class ShelterBusinessLicenseView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    # 보호소 사업자등록증 업로드
    @extend_schema(
        summary="보호소 사업자등록증 업로드",
        request={"multipart/form-data": {"business_license": "file"}},
        responses={201: ShelterBusinessLicenseSerializer(many=True)},
    )
    def post(self, request):
        user = request.user
        shelter = Shelter.objects.filter(user=user).first()

        if not shelter:
            return Response(
                {"error": "보호소 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        file = request.FILES.get("business_license")

        if not file:
            return Response(
                {"error": "파일을 업로드해야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_file_extension(file, "shelters")  # 파일 검증
            file_url = upload_file_to_s3(file, "shelters", shelter.id)  # S3 업로드

            # 기존 파일 삭제 후 새로운 파일 저장
            if shelter.business_license_file:
                delete_file_from_s3(shelter.business_license_file)

            shelter.business_license_file = file_url
            shelter.save()

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ShelterBusinessLicenseSerializer(shelter).data,
            status=status.HTTP_201_CREATED,
        )

    # 보호소 사업자등록증 조회
    @extend_schema(
        summary="보호소 사업자등록증 조회",
        responses={200: ShelterBusinessLicenseSerializer},
    )
    def get(self, request):
        user = request.user
        shelter = Shelter.objects.filter(user=user).first()

        if not shelter:
            return Response(
                {"error": {"보호소 정보를 찾을 수 없습니다."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            ShelterBusinessLicenseSerializer(shelter).data, status=status.HTTP_200_OK
        )

    # 보호소 사업자등록증 삭제
    @extend_schema(summary="보호소 사업자등록증 삭제", responses={204: None})
    def delete(self, request):
        user = request.user
        shelter = Shelter.objects.filter(user=user).first()

        if not shelter:
            return Response(
                {"error": "보호소 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not shelter.business_license_file:
            return Response(
                {"error": "등록된 사업자등록증이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            delete_file_from_s3(shelter.business_license_file)
            shelter.business_license_file = None
            shelter.save()
            return Response(
                {"message": "사업자등록증이 삭제되었습니다."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "삭제가 실패하였습니다.", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
