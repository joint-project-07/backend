from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from common.models import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # 소셜 로그인을 지원하는 경우, 처음에 비밀번호 없이 계정을 생성할 수 있기 때문에 password=None
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(
            email
        )  # normalize_email: 이메일을 일관된 형식으로 변환하는 메서드
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class UserType(models.TextChoices):
    VOLUNTEER = "volunteer", "Volunteer"
    SHELTER_ADMIN = "shelter_admin", "Shelter Admin"


class SocialType(models.TextChoices):
    EMAIL = "email", "Email"
    KAKAO = "kakao", "Kakao"


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255, null=False)
    password = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=100, null=False)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=False)
    user_type = models.CharField(max_length=20, choices=UserType.choices, null=False)
    profile_image = models.URLField(max_length=255, null=True, blank=True)
    social_type = models.CharField(
        max_length=10, choices=SocialType.choices, null=False
    )
    social_id = models.CharField(mx_length=255, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "phone_number", "user_type"]

    def __str__(self):
        return self.email

    class Meta:
        db_table = "users"
