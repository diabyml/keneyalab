import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.analyte import create_random_analyte, random_lower_string

PREFIX = f"{settings.API_V1_STR}/analytes"


def test_create_analyte(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    code = random_lower_string(8).upper()
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"code": code.lower(), "name": "Glucose", "data_type": "numeric"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["code"] == code
    assert content["name"] == "Glucose"
    assert content["data_type"] == "numeric"
    assert content["is_deleted"] is False


def test_read_analytes(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_analyte(db)
    create_random_analyte(db)
    response = client.get(f"{PREFIX}/", headers=superuser_token_headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 2


def test_search_analytes(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    code = f"SRCH{random_lower_string(6).upper()}"
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"code": code, "name": "Glycémie recherche", "data_type": "numeric"},
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


def test_filter_analytes_by_type_and_calculated(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    calculated_response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "code": f"CALC{random_lower_string(6).upper()}",
            "name": "Analyte calculé",
            "data_type": "numeric",
            "is_calculated": True,
            "calculation_formula": "A + B",
        },
    )
    assert calculated_response.status_code == 200
    calculated_id = calculated_response.json()["id"]

    text_response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "code": f"TXT{random_lower_string(6).upper()}",
            "name": "Analyte texte",
            "data_type": "text",
        },
    )
    assert text_response.status_code == 200

    response = client.get(
        f"{PREFIX}/?data_type=numeric&is_calculated=true&limit=20",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    rows = response.json()["data"]
    assert calculated_id in [item["id"] for item in rows]
    assert all(item["data_type"] == "numeric" for item in rows)
    assert all(item["is_calculated"] is True for item in rows)


def test_read_analyte(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db)
    response = client.get(f"{PREFIX}/{analyte.id}", headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(analyte.id)
    assert content["code"] == analyte.code


def test_read_analyte_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Analyte non trouvé"


def test_update_analyte(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db)
    response = client.put(
        f"{PREFIX}/{analyte.id}",
        headers=superuser_token_headers,
        json={"name": "Glycémie", "reference_text": "<p>Normal</p>"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Glycémie"
    assert content["reference_text"] == "<p>Normal</p>"


def test_delete_analyte(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db)
    response = client.delete(f"{PREFIX}/{analyte.id}", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Analyte supprimé avec succès"

    list_response = client.get(f"{PREFIX}/", headers=superuser_token_headers)
    ids = [item["id"] for item in list_response.json()["data"]]
    assert str(analyte.id) not in ids

    deleted_response = client.get(
        f"{PREFIX}/?include_deleted=true&is_deleted=true",
        headers=superuser_token_headers,
    )
    deleted_ids = [item["id"] for item in deleted_response.json()["data"]]
    assert str(analyte.id) in deleted_ids


def test_restore_analyte(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db)
    client.delete(f"{PREFIX}/{analyte.id}", headers=superuser_token_headers)
    response = client.post(f"{PREFIX}/{analyte.id}/restore", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["is_deleted"] is False


def test_create_analyte_forbidden(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{PREFIX}/",
        headers=normal_user_token_headers,
        json={"code": "GLU", "name": "Glucose", "data_type": "numeric"},
    )
    assert response.status_code == 403


def test_duplicate_code_returns_conflict(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"code": analyte.code.lower(), "name": "Duplicate", "data_type": "text"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Code d'analyte déjà utilisé"


def test_options_data_required_for_options_type(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"code": "OPT", "name": "Option", "data_type": "options", "options_data": []},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Les options doivent être une liste non vide"


def test_calculated_analyte_requires_formula(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "code": "CALC",
            "name": "Calculé",
            "data_type": "numeric",
            "is_calculated": True,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "La formule de calcul est requise"
