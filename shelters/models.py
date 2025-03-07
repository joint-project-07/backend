import uuid

from django.db import models

from common.models import BaseModel
from users.models import User


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


class ShelterFileTypeChoices(models.TextChoices):
    PROFILE = "profile", "Profile"
    GENERAL = "general", "General"
    BUSINESS_LICENSE = "business_license", "Business License"


def shelter_images_path(instance, filename):
    shelter_id = instance.shelter.id if instance.shelter.id else str(uuid.uuid4())
    return f"shelters/{shelter_id}/images/{filename}w"


def shelter_file_path(instance, filename):
    shelter_id = instance.shelter.id if instance.shelter.id else str(uuid.uuid4())
    return f"shelters/{shelter_id}/license/{filename}"


class Shelter(BaseModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=False)
    address = models.CharField(max_length=255, null=False)
    region = models.CharField(max_length=10, choices=RegionChoices.choices, null=False)
    shelter_type = models.CharField(
        max_length=20, choices=ShelterTypeChoices.choices, null=False
    )
    business_registration_number = models.CharField(max_length=20, null=False)
    business_license_file = models.FileField(upload_to=shelter_file_path, null=False)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="shelter")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "shelters"


class ShelterImage(BaseModel):
    id = models.AutoField(primary_key=True)
    shelter = models.ForeignKey(
        Shelter, on_delete=models.CASCADE, related_name="images"
    )
    image_type = models.CharField(
        max_length=20,
        choices=ShelterFileTypeChoices.choices,
        default=ShelterFileTypeChoices.GENERAL,  # 기본값: 일반 이미지
    )
    image = models.ImageField(upload_to=shelter_images_path, null=False)

    def __str__(self):
        return f"{self.shelter.name} - {self.image_type} - Image {self.id}"

    class Meta:
        db_table = "shelters_images"


class ShelterFile(BaseModel):
    id = models.AutoField(primary_key=True)
    shelter = models.ForeignKey(Shelter, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=shelter_file_path, null=False)

    def __str__(self):
        return f"{self.shelter.name} - Business License"

    class Meta:
        db_table = "shelters_files"
