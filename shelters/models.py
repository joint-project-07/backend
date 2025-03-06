import uuid

from django.db import models
from common.models import BaseModel


class RegionChoices(models.TextChoices):
    SEOUL = "서울", "서울"
    BUSAN = "부산", "부산"
    DAEGU = "대구", "대구"
    INCHEON = "인천", "인천"
    GWANGJU = "광주", "광주"
    DAEJEON = "대전", "대전"
    ULSAN = "울산", "울산"
    SEJONG = "세종", "세종"
    GYEONGGI = "경기", "경기"
    GANGWON = "강원", "강원"
    CHUNGBUK = "충북", "충북"
    CHUNGNAM = "충남", "충남"
    JEONBUK = "전북", "전북"
    JEONNAM = "전남", "전남"
    GYEONGBUK = "경북", "경북"
    GYEONGNAM = "경남", "경남"
    JEJU = "제주", "제주"


class ShelterTypeChoices(models.TextChoices):
    CORPORATION = "corporation", "Corporation"
    INDIVIDUAL = "individual", "Individual"
    NON_PROFIT = "non_profit", "Non-Profit"


class Shelter(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    address = models.CharField(max_length=255, null=False)
    region = models.CharField(
        max_length=10, choices=RegionChoices.choices(), null=False
    )
    contact_number = models.CharField(max_length=20, null=False)
    shelter_type = models.CharField(
        max_length=20, choices=ShelterTypeChoices.choices(), null=False
    )
    owner_name = models.CharField(max_length=100, null=False)
    profile_image = models.URLField(max_length=255)
    business_registration_number = models.CharField(max_length=20, null=False)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, null=False)
    business_license_file = models.FileField(upload_to='business_licenses/', null=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "shelters"