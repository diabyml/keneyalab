import uuid

import pytest

from app.core.exceptions import BusinessRuleError
from app.services import object_storage


class FakeStorage:
    def __init__(self) -> None:
        self.uploaded: list[tuple[str, str, int, str | None]] = []
        self.removed: list[tuple[str, str]] = []

    def bucket_exists(self, _bucket: str) -> bool:
        return True

    def put_object(
        self,
        bucket: str,
        key: str,
        _stream,
        *,
        length: int,
        content_type: str | None,
    ) -> None:
        self.uploaded.append((bucket, key, length, content_type))

    def remove_object(self, bucket: str, key: str) -> None:
        self.removed.append((bucket, key))


def test_result_image_upload_validates_and_uses_private_key(monkeypatch) -> None:
    storage = FakeStorage()
    monkeypatch.setattr(object_storage, "client", lambda: storage)
    order_id = uuid.uuid4()
    item_id = uuid.uuid4()
    analyte_id = uuid.uuid4()

    key = object_storage.upload_result_image(
        order_id=order_id,
        order_item_id=item_id,
        analyte_id=analyte_id,
        content_type="image/png",
        data=b"png",
    )

    assert key.startswith(
        f"orders/{order_id}/items/{item_id}/analytes/{analyte_id}/"
    )
    assert key.endswith(".png")
    assert storage.uploaded[0][2:] == (3, "image/png")

    with pytest.raises(BusinessRuleError):
        object_storage.upload_result_image(
            order_id=order_id,
            order_item_id=item_id,
            analyte_id=analyte_id,
            content_type="image/svg+xml",
            data=b"<svg/>",
        )


def test_lab_logo_upload_validates_size_and_location(monkeypatch) -> None:
    storage = FakeStorage()
    monkeypatch.setattr(object_storage, "client", lambda: storage)

    key = object_storage.upload_lab_logo(
        content_type="image/webp",
        data=b"logo",
    )

    assert key.startswith("lab-settings/logo/")
    assert key.endswith(".webp")
    assert storage.uploaded[0][2:] == (4, "image/webp")

    with pytest.raises(BusinessRuleError):
        object_storage.upload_lab_logo(
            content_type="image/svg+xml",
            data=b"<svg/>",
        )

    with pytest.raises(BusinessRuleError):
        object_storage.upload_lab_logo(
            content_type="image/png",
            data=b"x" * (object_storage.LAB_LOGO_MAX_BYTES + 1),
        )
