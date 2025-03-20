import uuid

from django.core.exceptions import ValidationError

from Dangnyang_Heroes.settings import base

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "png"}
LICENSE_ALLOWED_EXTENSIONS = {"pdf", "png", "jpg"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# 파일 확장자 검증
def validate_file_extension(file, instance_type):
    file_extension = file.name.split(".")[-1].lower()

    if instance_type == "users":
        if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError("이미지는 JPG, PNG 형식만 가능합니다.")

        if file.size > MAX_FILE_SIZE_BYTES:
            raise ValidationError(
                f"파일 크기는 {MAX_FILE_SIZE_MB}MB를 초과할 수 없습니다."
            )

    elif instance_type == "shelters":
        if file_extension not in LICENSE_ALLOWED_EXTENSIONS:
            raise ValidationError("사업자등록증은 PDF, PNG, JPG 형식만 가능합니다.")

    elif instance_type == "recruitments":
        if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError("이미지는 JPG, PNG 형식만 가능합니다.")


# S3 에 이미지 업로드 후 URL 반환
def upload_file_to_s3(file, instance_type, object_identifier):
    validation_result = validate_file_extension(file, instance_type)
    if validation_result is None:
        raise ValueError(f"Invalid file extension: {file.name.split(".")[-1].lower()}")

    file_name, file_extension = validation_result
    new_filename = f"{uuid.uuid4()}.{file_extension}"

    # S3 저장 경로 설정
    if instance_type == "users":
        s3_path = f"users/{object_identifier}/{new_filename}"
    elif instance_type == "shelters":
        s3_path = f"shelters/{object_identifier}/{new_filename}"
    elif instance_type == "recruitments":
        s3_path = f"recruitments/{object_identifier}/{new_filename}"
    else:
        raise ValueError(f"Invalid instance type: {instance_type}")

    try:
        base.s3_client.upload_fileobj(file, base.AWS_STORAGE_BUCKET_NAME, s3_path)
        return f"{base.AWS_S3_CUSTOM_DOMAIN}/{s3_path}"
    except Exception as e:
        raise RuntimeError(f"S3 Upload Error: {e}")


# 이미지 삭제
def delete_file_from_s3(image_url):
    try:
        s3_path = image_url.replace(base.AWS_S3_CUSTOM_DOMAIN + "/", "")
        base.s3_client.delete_object(Bucket=base.AWS_STORAGE_BUCKET_NAME, Key=s3_path)
        return True
    except Exception as e:
        raise RuntimeError(f"S3 Delete Error: {e}")
