from django.urls import path

from .views import (
    ChangePasswordView,
    EmailCheckView,
    EmailConfirmationView,
    EmailLoginView,
    FindEmailView,
    KakaoLoginView,
    LogoutView,
    ProfileImageUploadDeleteView,
    ResetPasswordView,
    ShelterSignupView,
    SignupView,
    UserDeleteView,
    UserProfileImageView,
    UserView,
    VerifyEmailView,
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
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path(
        "profile_image/detail/",
        ProfileImageUploadDeleteView.as_view(),
        name="profile-image-detail",
    ),
    path("profile_image/", UserProfileImageView.as_view(), name="profile-image"),
    path("verify/email-code/", VerifyEmailView.as_view(), name="verify-email-code"),
    path("delete/", UserDeleteView.as_view(), name="user-delete"),
]
