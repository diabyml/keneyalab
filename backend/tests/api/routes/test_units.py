import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.unit import create_random_unit


def test_create_unit(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "mg/dL"}
    response = client.post(
        f"{settings.API_V1_STR}/units/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content
    assert content["is_deleted"] is False


def test_read_units(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_unit(db)
    create_random_unit(db)
    response = client.get(
        f"{settings.API_V1_STR}/units/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2
    assert "count" in content


def test_search_units(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/units/",
        headers=superuser_token_headers,
        json={"name": "mmol recherche"},
    )
    assert response.status_code == 200
    created_id = response.json()["id"]

    search_response = client.get(
        f"{settings.API_V1_STR}/units/?search=recherche&limit=20",
        headers=superuser_token_headers,
    )
    assert search_response.status_code == 200
    ids = [item["id"] for item in search_response.json()["data"]]
    assert created_id in ids


def test_read_unit(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    unit = create_random_unit(db)
    response = client.get(
        f"{settings.API_V1_STR}/units/{unit.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == unit.name
    assert content["id"] == str(unit.id)


def test_read_unit_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/units/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Unité non trouvée"


def test_update_unit(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    unit = create_random_unit(db)
    data = {"name": "g/L"}
    response = client.put(
        f"{settings.API_V1_STR}/units/{unit.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["id"] == str(unit.id)


def test_update_unit_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "g/L"}
    response = client.put(
        f"{settings.API_V1_STR}/units/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Unité non trouvée"


def test_delete_unit(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    unit = create_random_unit(db)
    response = client.delete(
        f"{settings.API_V1_STR}/units/{unit.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Unité supprimée avec succès"

    # Verify soft-deleted: excluded from default list
    list_response = client.get(
        f"{settings.API_V1_STR}/units/",
        headers=superuser_token_headers,
    )
    list_content = list_response.json()
    ids = [u["id"] for u in list_content["data"]]
    assert str(unit.id) not in ids

    # Verify retrievable with include_deleted=true
    list_with_deleted = client.get(
        f"{settings.API_V1_STR}/units/?include_deleted=true",
        headers=superuser_token_headers,
    )
    deleted_content = list_with_deleted.json()
    deleted_ids = [u["id"] for u in deleted_content["data"]]
    assert str(unit.id) in deleted_ids


def test_restore_unit(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    unit = create_random_unit(db)
    # Soft-delete first
    client.delete(
        f"{settings.API_V1_STR}/units/{unit.id}",
        headers=superuser_token_headers,
    )
    # Restore
    response = client.post(
        f"{settings.API_V1_STR}/units/{unit.id}/restore",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_deleted"] is False
    assert content["id"] == str(unit.id)


def test_delete_unit_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/units/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Unité non trouvée"


def test_create_unit_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"name": "mg/dL"}
    response = client.post(
        f"{settings.API_V1_STR}/units/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
