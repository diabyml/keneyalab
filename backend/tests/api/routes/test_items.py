import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.repositories import user as user_repo
from app.services.permission import assign_default_roles
from tests.utils.item import create_random_item
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


@pytest.fixture(scope="module")
def user_with_items_perms_headers(
    client: TestClient, db: Session
) -> dict[str, str]:
    """Normal user WITH items permissions (has receptionist role).

    Needed because after RBAC gating, users without permissions cannot
    access items endpoints at all.  This user passes the RBAC gate but
    still fails ownership checks on items they don't own.
    """
    email = random_email()
    headers = authentication_token_from_email(
        client=client, email=email, db=db
    )
    user = user_repo.get_by_email(session=db, email=email)
    superuser = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if user and superuser:
        assign_default_roles(session=db, user=user, assigned_by=superuser)
    return headers


def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_read_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Tâche non trouvée"


def test_read_item_not_enough_permissions(
    client: TestClient, user_with_items_perms_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=user_with_items_perms_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Permissions insuffisantes"


def test_read_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_update_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Tâche non trouvée"


def test_update_item_not_enough_permissions(
    client: TestClient, user_with_items_perms_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=user_with_items_perms_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Permissions insuffisantes"


def test_delete_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Tâche supprimée avec succès"


def test_delete_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Tâche non trouvée"


def test_delete_item_not_enough_permissions(
    client: TestClient, user_with_items_perms_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=user_with_items_perms_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Permissions insuffisantes"
