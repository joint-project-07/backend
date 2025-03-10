from django.core.files.storage import default_storage

from common.utils import generate_user_profile_image_path, validate_image_image


def upload_user_profile_image(user, file):
    # 파일 검증
    validate_image_image(file)

    file_path = generate_user_profile_image_path(user.id, file.name)

    # NCP 에 파일 저장
    uploaded_path = default_storage.save(file_path, file)

    # 저장된 URL 을 DB 에 저장
    user.profile_image_url = default_storage.url(uploaded_path)
    user.save()

    return user.profile_image_url
