from django.urls import path

from .views import (
    EmailCheckView,
    EmailConfirmationView,
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
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/shelter/", ShelterSignupView.as_view(), name="signup-shelter"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("kakao-login/", KakaoLoginView.as_view(), name="kakao-login"),
    path("find-email/", FindEmailView.as_view(), name="find-email"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    path("me/", UserView.as_view(), name="me"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("email-check/", EmailCheckView.as_view(), name="email-check"),
    path(
        "email-confirmation/",
        EmailConfirmationView.as_view(),
        name="email-confirmation",
    ),
]
