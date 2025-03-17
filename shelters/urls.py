from django.urls import path

from .views import (
    MyShelterDetailView,
    ShelterDetailView,
    ShelterListView,
    ShelterSearchView,
    ShelterUpdateView,
)

urlpatterns = [
    # 🧀 보호소 전체 목록 조회 (GET)
    path("shelters/", ShelterListView.as_view(), name="shelter-list"),
    # 🧀 보호소 검색 (GET)
    path("shelters/search/", ShelterSearchView.as_view(), name="shelter-search"),
    # 🧀 보호소 상세 조회 (GET)
    path("shelters/<int:pk>/", ShelterDetailView.as_view(), name="shelter-detail"),
    # 🧀 보호소 정보 수정 (PATCH)
    path("shelters/me/", ShelterUpdateView.as_view(), name="shelter-update"),
    # 🧀 보호소 정보 조회 (GET)
    path("shelters/me/", MyShelterDetailView.as_view(), name="my-shelter-detail"),
]
