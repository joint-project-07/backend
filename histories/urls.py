from django.urls import path

from histories.views import HistoryAPIView, HistoryRatingAPIView

urlpatterns = [
    path("", HistoryAPIView.as_view(), name="history-list"),
    path("<int:history_id>/rate/", HistoryRatingAPIView.as_view(), name="history-rate"),
]
