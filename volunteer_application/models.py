from django.db import models
from users.models import User
from volunteer.models import VolunteerActivity

from common.models import BaseModel


class VolunteerApplication(BaseModel):
    STATUS_CHOICES = [
        ("pending", "승인 대기"),
        ("approved", "승인 완료"),
        ("rejected", "거절됨"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="applications"
    )
    volunteer_activity = models.ForeignKey(
        VolunteerActivity, on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    rejected_reason = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.volunteer_activity.activity_date} ({self.get_status_display()})"
