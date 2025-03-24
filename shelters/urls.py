from django.urls import path

from .views import (
    MyShelterDetailView,
    ShelterDetailView,
    ShelterListView,
    ShelterSearchView,
)

urlpatterns = [
    # 🧀 보호소 전체 목록 조회 (GET)
    path("", ShelterListView.as_view(), name="shelter-list"),
    # 🧀 보호소 검색 (GET)
    path("search/", ShelterSearchView.as_view(), name="shelter-search"),
    # 🧀 보호소 상세 조회 (GET)
    path("<int:pk>/", ShelterDetailView.as_view(), name="shelter-detail"),
    # 🧀 보호소 정보 조회 및 수정(GET,PATCH)
    path("me/", MyShelterDetailView.as_view(), name="my-shelter-detail"),
]
