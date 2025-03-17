from django.urls import path

from .views import (
    RecruitmentCreateView,
    RecruitmentDetailView,
    RecruitmentListView,
    RecruitmentUpdateView,
)

urlpatterns = [
    path("", RecruitmentCreateView.as_view(), name="recruitment_create"),
    path("", RecruitmentListView.as_view(), name="recruitment-list"),
    path("<int:pk>/", RecruitmentDetailView.as_view(), name="recruitment-detail"),
    path("<int:pk>/", RecruitmentUpdateView.as_view(), name="recruitment-update"),
]
