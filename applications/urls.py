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
    path("<int:application_id>/", ApplicationDetailView.as_view(), name="application-detail"),
    path(
        "<int:application_id>/approved/",
        ApplicationApproveRejectView.as_view(),
        name="application-approve",
    ),
    path(
        "<int:application_id>/rejected/", ApplicationRejectView.as_view(), name="application-reject"
    ),
    path(
        "<int:application_id>/attended/", ApplicationAttendView.as_view(), name="application-attend"
    ),
    path(
        "<int:application_id>/absence/",
        ApplicationAbsenceView.as_view(),
        name="application-absence",
    ),
]
