from django.db import models
from common.models import BaseModel
from users.models import User
from volunteer_application.models import VolunteerApplication

class VolunteerHistory(BaseModel):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1~5점

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="volunteer_history")
    application = models.ForeignKey(VolunteerApplication, on_delete=models.CASCADE, related_name="history")
    rating = models.IntegerField(choices=RATING_CHOICES, default=1)  # 만족도 평가

    def __str__(self):
        return f"{self.user.username} - {self.application.recruitment.date} (완료됨)"
