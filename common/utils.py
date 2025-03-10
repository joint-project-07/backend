import uuid

from django.core.exceptions import ValidationError

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "png"}
LICENSE_ALLOWED_EXTENSIONS = {"pdf", "png", "jpg"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# 이미지 확장자 검증
def validate_image_image(file):
    file_extension = file.name.split(".")[-1].lower()

    if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("이미지는 JPG, PNG 형식만 가능합니다.")

    if file.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"파일 크기는 {MAX_FILE_SIZE_MB}MB를 초과할 수 없습니다.")


# 사업자등록증 확장자 검증
def validate_license_file(file):
    file_extension = file.name.split(".")[-1].lower()
    if file_extension not in LICENSE_ALLOWED_EXTENSIONS:
        raise ValidationError("사업자등록증은 PDF, PNG, JPG 형식만 가능합니다.")


# user image 경로
def generate_user_profile_image_path(user_id, filename):
    file_extension = filename.split(".")[-1]
    return f"users/{user_id}/{uuid.uuid4()}.{file_extension}"


# shelter profile image 경로
def generate_shelter_profile_image_path(shelter_id, filename):
    shelter_folder = shelter_id if shelter_id else uuid.uuid4()
    file_extension = filename.split(".")[-1]
    return f"shelters/{shelter_folder}/profile/{uuid.uuid4()}.{file_extension}"


# shelter image 경로
def generate_shelter_image_path(shelter_id, filename):
    shelter_folder = shelter_id if shelter_id else uuid.uuid4()
    file_extension = filename.split(".")[-1]
    return f"shelters/{shelter_folder}/images/{uuid.uuid4()}.{file_extension}"


# shelter_license 경로
def generate_shelter_license_path(shelter_id, filename):
    shelter_folder = shelter_id if shelter_id else uuid.uuid4()
    file_extension = filename.split(".")[-1]
    return f"shelters/{shelter_folder}/licenses/{uuid.uuid4()}.{file_extension}"
