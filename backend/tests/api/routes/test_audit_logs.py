import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlmodel import Session

from app.core.config import settings

PREFIX = f"{settings.API_V1_STR}/audit-logs"


def test_mutation_is_captured_with_request_context(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    request_id = f"audit-test-{uuid.uuid4()}"
    name = f"Audit {uuid.uuid4().hex[:8]}"
    response = client.post(
        f"{settings.API_V1_STR}/titles/",
        headers={**superuser_token_headers, "X-Request-ID": request_id},
        json={"name": name},
    )

    assert response.status_code == 200
    title_id = response.json()["id"]
    logs = client.get(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        params={"table_name": "titles", "record_id": title_id},
    )
    assert logs.status_code == 200
    event = logs.json()["data"][0]
    assert event["action"] == "insert"
    assert event["category"] == "configuration"
    assert event["record_label"] == name
    assert event["request_id"] == request_id
    assert event["source"] == "api"
    assert event["actor_email"]
    assert event["new_values"]["name"] == name
    assert logs.json()["count"] == 1


def test_summary_detail_and_export(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    summary = client.get(
        f"{PREFIX}/summary",
        headers=superuser_token_headers,
        params={"category": "configuration"},
    )
    assert summary.status_code == 200
    assert summary.json()["total"] >= 1

    logs = client.get(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        params={"category": "configuration", "limit": 1},
    )
    event_id = logs.json()["data"][0]["id"]
    detail = client.get(
        f"{PREFIX}/{event_id}",
        headers=superuser_token_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == event_id

    exported = client.get(
        f"{PREFIX}/export",
        headers=superuser_token_headers,
        params={"category": "configuration"},
    )
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert "Catégorie" in exported.text


def test_audit_access_requires_permission(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    viewed = client.get(f"{PREFIX}/", headers=normal_user_token_headers)
    exported = client.get(f"{PREFIX}/export", headers=normal_user_token_headers)

    assert viewed.status_code == 403
    assert exported.status_code == 403


def test_failed_login_is_audited(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    email = f"failed-{uuid.uuid4().hex[:8]}@example.com"
    failed = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": "incorrect-password"},
    )
    assert failed.status_code == 401

    logs = client.get(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        params={
            "category": "security",
            "action": "login_failed",
            "search": email,
        },
    )
    assert logs.status_code == 200
    assert logs.json()["count"] == 1
    assert logs.json()["data"][0]["record_label"] == email


def test_audit_rows_are_immutable(db: Session) -> None:
    audit_id = db.exec(
        text("SELECT id FROM audit_logs ORDER BY performed_at DESC LIMIT 1")
    ).scalar_one()

    try:
        db.exec(
            text("UPDATE audit_logs SET record_label = 'interdit' WHERE id = :id"),
            params={"id": audit_id},
        )
        db.commit()
    except DBAPIError:
        db.rollback()
    else:
        raise AssertionError("La mise à jour d'un événement d'audit aurait dû échouer")
