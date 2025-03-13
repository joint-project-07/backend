from django.urls import path

from .views import (
    EmailLoginView,
    FindEmailView,
    KakaoLoginView,
    LogoutView,
    ResetPasswordView,
    ShelterSignupView,
    SignupView,
    UserView,
)

urlpatterns = [
    path("", SignupView.as_view(), name=""),
    path("", ShelterSignupView.as_view(), name=""),
    path("", EmailLoginView.as_view(), name=""),
    path("", KakaoLoginView.as_view(), name=""),
    path("", FindEmailView.as_view(), name=""),
    path("", ResetPasswordView.as_view(), name=""),
    path("", UserView.as_view(), name=""),
    path("", LogoutView.as_view(), name=""),
]
