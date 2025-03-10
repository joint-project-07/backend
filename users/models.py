from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from common.models import BaseModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_shelter=False, **extra_fields):
        if not email:
            raise ValueError("이메일은 필수입니다.")
        email = self.normalize_email(email)
        user = self.model(email=email, is_shelter=is_shelter, **extra_fields)
        if password:  # 비밀번호가 있을 경우만 설정 (소셜 로그인 고려)
            user.set_password(password)
        else:
            user.set_unusable_password()  # 소셜 로그인 사용자의 경우
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("슈퍼유저는 is_staff=True 이어야 합니다.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("슈퍼유저는 is_superuser=True 이어야 합니다.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True, max_length=255, null=False)
    password = models.CharField(max_length=255, null=False)
    name = models.CharField(max_length=100, null=False)
    birth_date = models.DateField(null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=False)
    profile_image = models.CharField(max_length=255, null=True, blank=True)  # ERD와 통일
    is_shelter = models.BooleanField(default=False)  # 보호소 관리자 여부
    kakao_login = models.BooleanField(default=False)  # ERD에 맞게 수정
    provider_id = models.CharField(max_length=255, null=True, blank=True)  # ERD에 맞게 수정

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django 관리 권한

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "contact_number"]

    def __str__(self):
        return self.email

    class Meta:
        db_table = "users"
