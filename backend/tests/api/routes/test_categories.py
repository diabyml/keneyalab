import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.category import create_random_category

PREFIX = f"{settings.API_V1_STR}/categories"


def test_create_category(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"name": "Biochimie", "sort_order": 10},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Biochimie"
    assert content["sort_order"] == 10
    assert content["is_deleted"] is False


def test_read_categories_sorted(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    third = create_random_category(db, sort_order=30)
    first = create_random_category(db, sort_order=10)
    second = create_random_category(db, sort_order=20)

    response = client.get(f"{PREFIX}/", headers=superuser_token_headers)
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["data"]]
    assert ids.index(str(first.id)) < ids.index(str(second.id))
    assert ids.index(str(second.id)) < ids.index(str(third.id))


def test_search_categories(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"name": "Biochimie recherche", "sort_order": 50},
    )
    assert response.status_code == 200
    created_id = response.json()["id"]

    search_response = client.get(
        f"{PREFIX}/?search=recherche&limit=20",
        headers=superuser_token_headers,
    )
    assert search_response.status_code == 200
    ids = [item["id"] for item in search_response.json()["data"]]
    assert created_id in ids


def test_read_category(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    category = create_random_category(db)
    response = client.get(
        f"{PREFIX}/{category.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == category.name
    assert content["id"] == str(category.id)


def test_read_category_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{PREFIX}/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Catégorie non trouvée"


def test_update_category(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    category = create_random_category(db)
    response = client.put(
        f"{PREFIX}/{category.id}",
        headers=superuser_token_headers,
        json={"name": "Hématologie", "sort_order": 5},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Hématologie"
    assert content["sort_order"] == 5


def test_update_category_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.put(
        f"{PREFIX}/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json={"name": "X"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Catégorie non trouvée"


def test_delete_category(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    category = create_random_category(db)
    response = client.delete(
        f"{PREFIX}/{category.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Catégorie supprimée avec succès"

    list_response = client.get(f"{PREFIX}/", headers=superuser_token_headers)
    ids = [item["id"] for item in list_response.json()["data"]]
    assert str(category.id) not in ids

    deleted_response = client.get(
        f"{PREFIX}/?include_deleted=true",
        headers=superuser_token_headers,
    )
    deleted_ids = [item["id"] for item in deleted_response.json()["data"]]
    assert str(category.id) in deleted_ids


def test_restore_category(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    category = create_random_category(db)
    client.delete(f"{PREFIX}/{category.id}", headers=superuser_token_headers)

    response = client.post(
        f"{PREFIX}/{category.id}/restore",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(category.id)
    assert content["is_deleted"] is False


def test_delete_category_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{PREFIX}/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Catégorie non trouvée"


def test_create_category_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{PREFIX}/",
        headers=normal_user_token_headers,
        json={"name": "Biochimie", "sort_order": 0},
    )
    assert response.status_code == 403


def test_reorder_categories(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    first = create_random_category(db, sort_order=1)
    second = create_random_category(db, sort_order=2)
    third = create_random_category(db, sort_order=3)

    response = client.put(
        f"{PREFIX}/reorder",
        headers=superuser_token_headers,
        json={
            "items": [
                {"id": str(third.id), "sort_order": 1},
                {"id": str(first.id), "sort_order": 2},
                {"id": str(second.id), "sort_order": 3},
            ]
        },
    )
    assert response.status_code == 200

    list_response = client.get(f"{PREFIX}/", headers=superuser_token_headers)
    items = list_response.json()["data"]
    ids = [item["id"] for item in items]
    assert ids.index(str(third.id)) < ids.index(str(first.id))
    assert ids.index(str(first.id)) < ids.index(str(second.id))
    assert next(item for item in items if item["id"] == str(third.id))[
        "sort_order"
    ] == 1


def test_reorder_category_not_found(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    category = create_random_category(db)
    response = client.put(
        f"{PREFIX}/reorder",
        headers=superuser_token_headers,
        json={
            "items": [
                {"id": str(category.id), "sort_order": 1},
                {"id": str(uuid.uuid4()), "sort_order": 2},
            ]
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Catégorie non trouvée"
