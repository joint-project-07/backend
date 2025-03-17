from django.urls import path

from .views import (
    RecruitmentCreateView,
    RecruitmentDetailView,
    RecruitmentListView,
    RecruitmentSearchView,
    RecruitmentUpdateView,
)

urlpatterns = [
    path("", RecruitmentListView.as_view(), name="recruitment-list"),
    path("search/", RecruitmentSearchView.as_view(), name="recruitment-search"),
    path("<int:pk>/", RecruitmentDetailView.as_view(), name="recruitment-detail"),
    path("create/", RecruitmentCreateView.as_view(), name="recruitment-create"),
    path(
        "update/<int:pk>/", RecruitmentUpdateView.as_view(), name="recruitment-update"
    ),
]
