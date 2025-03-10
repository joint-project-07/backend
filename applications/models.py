from django.db import models

from common.models import BaseModel
from recruitments.models import Recruitment
from shelters.models import Shelter
from users.models import User


class Application(BaseModel):
    STATUS_CHOICES = [
        ("pending", "승인 대기"),
        ("approved", "승인 완료"),
        ("rejected", "거절됨"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications"
    )
    recruitment = models.ForeignKey(
        Recruitment, on_delete=models.CASCADE, related_name="applications"
    )
    shelter = models.ForeignKey(
        Shelter, on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    rejected_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.name} - {self.recruitment.date} ({self.status})"
