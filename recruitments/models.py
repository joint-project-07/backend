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
    description = models.TextField(null=True, blank=True)  # 봉사 설명
    supplies = models.CharField(max_length=200, null=True, blank=True)  # 봉사 준비물
    status = models.CharField(
        max_length=20, choices=RecruitmentStatus.choices, default=RecruitmentStatus.OPEN
    )  # 모집 상태 (진행 중 / 마감)

    def __str__(self):
        return f"{self.shelter.name} - {self.date} ({self.get_status_display()})"

    class Meta:
        db_table = "recruitments"
