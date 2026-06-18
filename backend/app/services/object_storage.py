"""Private MinIO object storage for clinical result images."""

import io
import uuid
from datetime import timedelta

from minio import Minio

from app.core.config import settings
from app.core.exceptions import BusinessRuleError

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
LAB_LOGO_MAX_BYTES = 2 * 1024 * 1024


def client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
        region=settings.MINIO_REGION,
    )


def public_client() -> Minio:
    return Minio(
        settings.MINIO_PUBLIC_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
        region=settings.MINIO_REGION,
    )


def ensure_bucket() -> None:
    storage = client()
    if not storage.bucket_exists(settings.MINIO_BUCKET):
        storage.make_bucket(settings.MINIO_BUCKET)


def upload_result_image(
    *,
    order_id: uuid.UUID,
    order_item_id: uuid.UUID,
    analyte_id: uuid.UUID,
    content_type: str | None,
    data: bytes,
) -> str:
    suffix = ALLOWED_IMAGE_TYPES.get(content_type or "")
    if suffix is None:
        raise BusinessRuleError(
            "Format d'image non pris en charge (JPEG, PNG ou WebP)"
        )
    if not data:
        raise BusinessRuleError("Le fichier image est vide")
    if len(data) > settings.RESULT_IMAGE_MAX_BYTES:
        raise BusinessRuleError("L'image dépasse la taille maximale autorisée")
    ensure_bucket()
    object_key = (
        f"orders/{order_id}/items/{order_item_id}/analytes/{analyte_id}/"
        f"{uuid.uuid4()}{suffix}"
    )
    client().put_object(
        settings.MINIO_BUCKET,
        object_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_key


def upload_lab_logo(*, content_type: str | None, data: bytes) -> str:
    suffix = ALLOWED_IMAGE_TYPES.get(content_type or "")
    if suffix is None:
        raise BusinessRuleError(
            "Format de logo non pris en charge (JPEG, PNG ou WebP)"
        )
    if not data:
        raise BusinessRuleError("Le fichier du logo est vide")
    if len(data) > LAB_LOGO_MAX_BYTES:
        raise BusinessRuleError("Le logo dépasse la taille maximale de 2 Mo")
    ensure_bucket()
    object_key = f"lab-settings/logo/{uuid.uuid4()}{suffix}"
    client().put_object(
        settings.MINIO_BUCKET,
        object_key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return object_key


def delete_object(object_key: str | None) -> None:
    if not object_key:
        return
    client().remove_object(settings.MINIO_BUCKET, object_key)


def presigned_url(object_key: str | None) -> str | None:
    if not object_key:
        return None
    return public_client().presigned_get_object(
        settings.MINIO_BUCKET,
        object_key,
        expires=timedelta(seconds=settings.RESULT_IMAGE_URL_EXPIRE_SECONDS),
    )
