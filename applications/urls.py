from django.urls import path

from applications.views import (
    ApplicationAbsenceView,
    ApplicationApproveRejectView,
    ApplicationAttendView,
    ApplicationDetailView,
    ApplicationListCreateView,
    ApplicationRejectView,
)

urlpatterns = [
    path("", ApplicationListCreateView.as_view(), name="application-list-create"),
    path("<int:pk>/", ApplicationDetailView.as_view(), name="application-detail"),
    path(
        "<int:pk>/approved/",
        ApplicationApproveRejectView.as_view(),
        name="application-approve",
    ),
    path(
        "<int:pk>/rejected/", ApplicationRejectView.as_view(), name="application-reject"
    ),
    path(
        "<int:pk>/attended/", ApplicationAttendView.as_view(), name="application-attend"
    ),
    path(
        "<int:pk>/absence/",
        ApplicationAbsenceView.as_view(),
        name="application-absence",
    ),
]
