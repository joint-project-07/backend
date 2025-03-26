from django.db import models

from common.models import BaseModel
from shelters.models import Shelter


class RecruitmentTypeChoices(models.TextChoices):
    CLEANING = "cleaning", "Cleaning"
    WALKING = "walking", "Walking"
    FEEDING = "feeding", "Feeding"
    OTHER = "other", "Other"


class RecruitmentStatus(models.TextChoices):
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"


# ✅ description 필드를 선택형 필드로 수정
class DescriptionChoices(models.TextChoices):
    CLEANING = "cleaning", "견사청소"
    GROOMING = "grooming", "미용"
    BATHING = "bathing", "목욕"
    WALKING = "walking", "산책"
    FEEDING = "feeding", "밥주기"
    OTHER = "other", "기타"


class Recruitment(BaseModel):
    id = models.AutoField(primary_key=True)
    shelter = models.ForeignKey(
        Shelter, on_delete=models.CASCADE, related_name="recruitments"
    )  # 보호소 연결 (1:N 관계)
    date = models.DateField(null=False)  # 봉사 날짜
    start_time = models.TimeField(null=False)  # 시작 시간
    end_time = models.TimeField(null=False)  # 종료 시간
    type = models.CharField(
        max_length=50, choices=RecruitmentTypeChoices.choices, null=False
    )  # 봉사 종류
    description = models.CharField(
        max_length=50,
        choices=DescriptionChoices.choices,
        null=True,
        blank=True,
        default="",
    )  # ✅ 선택형 필드
    supplies = models.CharField(max_length=200, null=True, blank=True)  # 봉사 준비물
    status = models.CharField(
        max_length=20, choices=RecruitmentStatus.choices, default=RecruitmentStatus.OPEN
    )  # 모집 상태 (진행 중 / 마감)

    def __str__(self):
        return f"{self.shelter.name} - {self.date} ({self.get_status_display()})"

    class Meta:
        db_table = "recruitments"


class RecruitmentImage(BaseModel):
    id = models.AutoField(primary_key=True)
    recruitment = models.ForeignKey(Recruitment, on_delete=models.CASCADE)
    image_url = models.URLField()

    def __str__(self):
        return f"Recruitment ID {self.recruitment.id} - Image {self.id}"

    class Meta:
        db_table = "recruitment_images"
