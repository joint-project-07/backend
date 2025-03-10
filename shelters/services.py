from django.core.files.storage import default_storage

from common.utils import (
    generate_shelter_image_path,
    generate_shelter_license_path,
    generate_shelter_profile_image_path,
    validate_image,
    validate_license_file,
)

from .models import ShelterFileTypeChoices, ShelterImage


def upload_shelter_profile_image(shelter, file):
    # 파일 검증
    validate_image(file)

    file_path = generate_shelter_profile_image_path(shelter.id, file.name)

    uploaded_path = default_storage.save(file_path, file)
    shelter.profile_image_url = default_storage.url(uploaded_path)
    shelter.save()

    return shelter.profile_image_url


def upload_shelter_license_file(shelter, file):
    validate_license_file(file)  # 파일 검증

    file_path = generate_shelter_license_path(shelter.id, file.name)

    uploaded_path = default_storage.save(file_path, file)
    shelter.business_license_file_url = default_storage.url(uploaded_path)
    shelter.save()

    return shelter.business_license_file_url


def upload_shelter_images(shelter, files):
    image_urls = []

    for file in files:
        validate_image(file)  # 파일 검증

        file_path = generate_shelter_image_path(shelter.id, file.name)

        uploaded_path = default_storage.save(file_path, file)
        image_url = default_storage.url(uploaded_path)

        ShelterImage.objects.create(
            shelter=shelter,
            image_url=image_url,
            image_type=ShelterFileTypeChoices.GENERAL,
        )
        image_urls.append(image_url)

    return image_urls
