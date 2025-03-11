from django.urls import path
from applications.views import (
    ApplicationListCreateView,
    ApplicationDetailView,
    ApplicationApproveRejectView,
    ApplicationRejectView,
)

urlpatterns = [
    path("", ApplicationListCreateView.as_view(), name="application-list-create"),
    path("<int:pk>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("<int:pk>/approved/", ApplicationApproveRejectView.as_view(), name="application-approve"),
    path("<int:pk>/rejected/", ApplicationRejectView.as_view(), name="application-reject"),
]