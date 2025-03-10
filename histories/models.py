from django.db import models

from applications.models import Application
from common.models import BaseModel
from shelters.models import Shelter
from users.models import User


class History(BaseModel):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1~5점

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="histories")
    shelter = models.ForeignKey(
        Shelter, on_delete=models.CASCADE, related_name="histories"
    )
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="history"
    )
    rating = models.IntegerField(choices=RATING_CHOICES, default=1)  # 만족도 평가

    def __str__(self):
        return f"{self.user.name} - {self.application.recruitment.date} (완료됨)"
