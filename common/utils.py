import os
import uuid

import boto3
from django.core.exceptions import ValidationError

from Dangnyang_Heroes.settings import base

# 🌸 허용 확장자 및 파일 크기 제한
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "png"}
LICENSE_ALLOWED_EXTENSIONS = {"pdf", "png", "jpg"}
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# 🌸 s3_client 생성 함수
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=base.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=base.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=base.AWS_SECRET_ACCESS_KEY,
        region_name=base.AWS_S3_REGION_NAME,
    )


# 🌸 파일 확장자 및 크기 검사
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


# 🌸 UUID + 원본 파일명 + 확장자로 파일명 생성하는 함수"
def generate_unique_filename(filename):
    name, ext = os.path.splitext(filename)  # 파일명과 확장자 분리
    return f"{uuid.uuid4()}_{name}{ext}"


# 🌸 파일 업로드 (S3에 저장 후 URL 반환)
def upload_file_to_s3(file, instance_type, object_identifier):
    s3_client = get_s3_client()
    validate_file_extension(file, instance_type)
    unique_filename = generate_unique_filename(file.name)

    # S3 저장 경로 설정
    if instance_type == "users":
        s3_path = f"users/{object_identifier}/{unique_filename}"
    elif instance_type == "shelters":
        s3_path = f"shelters/{object_identifier}/{unique_filename}"
    elif instance_type == "recruitments":
        s3_path = f"recruitments/{object_identifier}/{unique_filename}"
    else:
        raise ValueError(f"Invalid instance type: {instance_type}")

    try:
        s3_client.upload_fileobj(
            file,
            base.AWS_STORAGE_BUCKET_NAME,
            s3_path,
            ExtraArgs={"ACL": "public-read"},
        )
        return f"{base.MEDIA_URL}{s3_path}"
    except Exception as e:
        raise RuntimeError(f"S3 Upload Error: {e}")


# 🌸 파일 삭제
def delete_file_from_s3(image_url):
    s3_client = get_s3_client()

    try:
        s3_path = image_url.replace(base.MEDIA_URL, "")
        s3_client.delete_object(Bucket=base.AWS_STORAGE_BUCKET_NAME, Key=s3_path)
        return True
    except Exception as e:
        raise RuntimeError(f"S3 Delete Error: {e}")


# 🌸 ACL 권한 부여 (필요시 공개 권한 부여 등)
def set_s3_object_acl(file_path, acl="public-read-write"):
    s3_client = get_s3_client()
    try:
        s3_client.put_object_acl(
            Bucket=base.AWS_STORAGE_BUCKET_NAME, Key=file_path, ACL=acl
        )
        return True
    except Exception as e:
        raise RuntimeError(f"S3 ACL 설정 오류: {e}")


# 🌸 CORS 설정
def configure_s3_cors():
    s3_client = get_s3_client()
    cors_configuration = {
        "CORSRules": [
            {
                "AllowedOrigins": ["*"],
                "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
                "AllowedHeaders": ["*"],
                "ExposeHeaders": ["ETag"],
                "MaxAgeSeconds": 3000,
            }
        ]
    }
    try:
        s3_client.put_bucket_cors(
            Bucket=base.AWS_STORAGE_BUCKET_NAME, CORSConfiguration=cors_configuration
        )
        return True
    except Exception as e:
        raise RuntimeError(f"S3 CORS 설정 오류: {e}")


# 🌸 객체 접근용 Signed URL 생성 (다운로드 등)
def generate_signed_url(object_url, expiration=300):
    if not object_url:
        s3_client = get_s3_client()
        if not object_url:
            return None
        try:
            object_key = object_url.replace(base.MEDIA_URL, "")
            return s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": base.AWS_STORAGE_BUCKET_NAME, "Key": object_key},
                ExpiresIn=expiration,
            )
        except Exception as e:
            raise RuntimeError(f"Signed URL 생성 실패: {e}")
