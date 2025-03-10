# Generated by Django 5.1.6 on 2025-03-10 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Shelter",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("address", models.CharField(max_length=255)),
                (
                    "region",
                    models.CharField(
                        choices=[
                            ("서울", "서울"),
                            ("부산", "부산"),
                            ("대구", "대구"),
                            ("인천", "인천"),
                            ("광주", "광주"),
                            ("대전", "대전"),
                            ("울산", "울산"),
                            ("세종", "세종"),
                            ("경기", "경기"),
                            ("강원", "강원"),
                            ("충북", "충북"),
                            ("충남", "충남"),
                            ("전북", "전북"),
                            ("전남", "전남"),
                            ("경북", "경북"),
                            ("경남", "경남"),
                            ("제주", "제주"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "shelter_type",
                    models.CharField(
                        choices=[
                            ("corporation", "Corporation"),
                            ("individual", "Individual"),
                            ("non_profit", "Non-Profit"),
                        ],
                        max_length=20,
                    ),
                ),
                ("business_registration_number", models.CharField(max_length=20)),
                ("business_registration_email", models.EmailField(max_length=255)),
                (
                    "business_license_file",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
            ],
            options={
                "db_table": "shelters",
            },
        ),
        migrations.CreateModel(
            name="ShelterImage",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "image_type",
                    models.CharField(
                        choices=[("profile", "Profile"), ("general", "General")],
                        default="general",
                        max_length=20,
                    ),
                ),
                ("image_url", models.CharField(max_length=255)),
            ],
            options={
                "db_table": "shelter_images",
            },
        ),
    ]
