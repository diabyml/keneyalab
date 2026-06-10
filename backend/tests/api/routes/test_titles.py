import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.title import create_random_title


def test_create_title(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Dr"}
    response = client.post(
        f"{settings.API_V1_STR}/titles/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert "id" in content
    assert content["is_deleted"] is False


def test_read_titles(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_title(db)
    create_random_title(db)
    response = client.get(
        f"{settings.API_V1_STR}/titles/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2
    assert "count" in content


def test_read_title(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    title = create_random_title(db)
    response = client.get(
        f"{settings.API_V1_STR}/titles/{title.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == title.name
    assert content["id"] == str(title.id)


def test_read_title_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/titles/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Titre non trouvé"


def test_update_title(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    title = create_random_title(db)
    data = {"name": "Pr"}
    response = client.put(
        f"{settings.API_V1_STR}/titles/{title.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["id"] == str(title.id)


def test_update_title_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"name": "Pr"}
    response = client.put(
        f"{settings.API_V1_STR}/titles/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Titre non trouvé"


def test_delete_title(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    title = create_random_title(db)
    response = client.delete(
        f"{settings.API_V1_STR}/titles/{title.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Titre supprimé avec succès"

    # Verify soft-deleted: excluded from default list
    list_response = client.get(
        f"{settings.API_V1_STR}/titles/",
        headers=superuser_token_headers,
    )
    list_content = list_response.json()
    ids = [t["id"] for t in list_content["data"]]
    assert str(title.id) not in ids

    # Verify retrievable with include_deleted=true
    list_with_deleted = client.get(
        f"{settings.API_V1_STR}/titles/?include_deleted=true",
        headers=superuser_token_headers,
    )
    deleted_content = list_with_deleted.json()
    deleted_ids = [t["id"] for t in deleted_content["data"]]
    assert str(title.id) in deleted_ids


def test_restore_title(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    title = create_random_title(db)
    # Soft-delete first
    client.delete(
        f"{settings.API_V1_STR}/titles/{title.id}",
        headers=superuser_token_headers,
    )
    # Restore
    response = client.post(
        f"{settings.API_V1_STR}/titles/{title.id}/restore",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_deleted"] is False
    assert content["id"] == str(title.id)


def test_delete_title_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/titles/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Titre non trouvé"


def test_create_title_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """User without reference_data:manage permission should get 403."""
    data = {"name": "Dr"}
    response = client.post(
        f"{settings.API_V1_STR}/titles/",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
