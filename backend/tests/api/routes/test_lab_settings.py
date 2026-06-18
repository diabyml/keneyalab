from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models.lis import AuditLog, LabSettings
from app.services import object_storage

PREFIX = f"{settings.API_V1_STR}/lab-settings"


def test_authenticated_users_can_read_lab_settings(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(f"{PREFIX}/", headers=normal_user_token_headers)

    assert response.status_code == 200
    assert response.json()["display_name"]


def test_update_lab_settings_is_audited(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    response = client.put(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "display_name": "Laboratoire Test",
            "primary_phone": "+223 20 00 00 00",
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Laboratoire Test"
    audit = db.exec(
        select(AuditLog)
        .where(AuditLog.table_name == "lab_settings")
        .order_by(AuditLog.created_at.desc())
    ).first()
    assert audit is not None
    assert audit.new_values["display_name"] == "Laboratoire Test"

    client.put(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"display_name": "KENEYA LAB", "primary_phone": None},
    )


def test_update_lab_settings_forbidden_without_permission(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.put(
        f"{PREFIX}/",
        headers=normal_user_token_headers,
        json={"display_name": "Interdit"},
    )

    assert response.status_code == 403


def test_lab_settings_validates_identity_fields(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    blank_name = client.put(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"display_name": "   "},
    )
    invalid_email = client.put(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"email": "adresse-invalide"},
    )
    invalid_website = client.put(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"website": "site sans protocole"},
    )

    assert blank_name.status_code == 400
    assert invalid_email.status_code == 422
    assert invalid_website.status_code == 422


def test_logo_replacement_and_removal(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    monkeypatch,
) -> None:
    uploaded = iter(["lab-settings/logo/first.png", "lab-settings/logo/second.png"])
    removed: list[str] = []
    monkeypatch.setattr(
        object_storage,
        "upload_lab_logo",
        lambda **_kwargs: next(uploaded),
    )
    monkeypatch.setattr(object_storage, "delete_object", removed.append)
    monkeypatch.setattr(
        object_storage,
        "presigned_url",
        lambda key: f"https://files.test/{key}" if key else None,
    )

    first = client.post(
        f"{PREFIX}/logo",
        headers=superuser_token_headers,
        files={"file": ("logo.png", b"first", "image/png")},
    )
    second = client.post(
        f"{PREFIX}/logo",
        headers=superuser_token_headers,
        files={"file": ("logo.png", b"second", "image/png")},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["logo_url"].endswith("/lab-settings/logo/second.png")
    assert removed == ["lab-settings/logo/first.png"]

    deleted = client.delete(
        f"{PREFIX}/logo",
        headers=superuser_token_headers,
    )
    assert deleted.status_code == 200
    assert deleted.json()["logo_url"] is None
    assert removed == [
        "lab-settings/logo/first.png",
        "lab-settings/logo/second.png",
    ]
    db.expire_all()
    assert db.get(LabSettings, 1).logo_object_key is None
