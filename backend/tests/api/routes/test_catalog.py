import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.lis import CatalogType
from tests.utils.analyte import create_random_analyte
from tests.utils.catalog import create_random_catalog, random_lower_string
from tests.utils.specimen_type import create_random_specimen_type

PREFIX = f"{settings.API_V1_STR}/catalog"


def test_create_catalog_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    code = random_lower_string(8).upper()
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "type": "item",
            "code": code.lower(),
            "name": "Glycémie",
            "price": "2500.00",
            "is_orderable": True,
        },
    )
    assert response.status_code == 200
    content = response.json()
    assert content["code"] == code
    assert content["name"] == "Glycémie"
    assert content["type"] == "item"
    assert content["price"] == "2500.00"
    assert content["is_deleted"] is False


def test_create_catalog_panel_without_manual_price(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    code = random_lower_string(8).upper()
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "type": "panel",
            "code": code.lower(),
            "name": "Bilan rénal",
            "is_orderable": True,
        },
    )
    assert response.status_code == 200
    content = response.json()
    assert content["code"] == code
    assert content["type"] == "panel"
    assert content["price"] == "0.00"


def test_create_catalog_panel_rejects_manual_price(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "type": "panel",
            "code": random_lower_string(8),
            "name": "Bilan avec prix manuel",
            "price": "2500.00",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Le prix d'un panel est calculé à partir de ses tests"


def test_read_catalog_server_side_filters(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_catalog(db, type=CatalogType.item, price=Decimal("100.00"))
    panel = create_random_catalog(db, type=CatalogType.panel)

    search_response = client.get(
        f"{PREFIX}/?search={item.code.lower()}&type=item&limit=10",
        headers=superuser_token_headers,
    )
    assert search_response.status_code == 200
    payload = search_response.json()
    ids = [row["id"] for row in payload["data"]]
    assert str(item.id) in ids
    assert str(panel.id) not in ids
    assert payload["count"] >= 1

    page_response = client.get(
        f"{PREFIX}/?skip=0&limit=1&sort_by=price&sort_order=desc",
        headers=superuser_token_headers,
    )
    assert page_response.status_code == 200
    assert len(page_response.json()["data"]) == 1


def test_read_catalog_detail(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    catalog = create_random_catalog(db)
    response = client.get(f"{PREFIX}/{catalog.id}", headers=superuser_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(catalog.id)
    assert content["analytes"] == []
    assert content["specimen_requirements"] == []
    assert content["panel_items"] == []


def test_read_catalog_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(f"{PREFIX}/{uuid.uuid4()}", headers=superuser_token_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Entrée catalogue non trouvée"


def test_update_catalog(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    catalog = create_random_catalog(db)
    response = client.put(
        f"{PREFIX}/{catalog.id}",
        headers=superuser_token_headers,
        json={"name": "Glycémie à jeun", "price": "3000.00"},
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == "Glycémie à jeun"
    assert content["price"] == "3000.00"


def test_update_catalog_panel_rejects_manual_price(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    panel = create_random_catalog(db, type=CatalogType.panel)
    response = client.put(
        f"{PREFIX}/{panel.id}",
        headers=superuser_token_headers,
        json={"price": "3000.00"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Le prix d'un panel est calculé à partir de ses tests"


def test_delete_and_restore_catalog(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    catalog = create_random_catalog(db)
    response = client.delete(f"{PREFIX}/{catalog.id}", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Entrée catalogue supprimée avec succès"

    list_response = client.get(f"{PREFIX}/", headers=superuser_token_headers)
    ids = [row["id"] for row in list_response.json()["data"]]
    assert str(catalog.id) not in ids

    restore_response = client.post(
        f"{PREFIX}/{catalog.id}/restore", headers=superuser_token_headers
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["is_deleted"] is False


def test_duplicate_catalog_code_returns_conflict(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    catalog = create_random_catalog(db)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "type": "item",
            "code": catalog.code.lower(),
            "name": "Duplicate",
            "price": "1000.00",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Code catalogue déjà utilisé"


def test_catalog_forbidden_for_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(f"{PREFIX}/", headers=normal_user_token_headers)
    assert response.status_code == 403


def test_add_reorder_and_remove_catalog_analyte(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    catalog = create_random_catalog(db, type=CatalogType.item)
    analyte = create_random_analyte(db)

    add_response = client.post(
        f"{PREFIX}/{catalog.id}/analytes",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "sort_order": 2},
    )
    assert add_response.status_code == 200
    attachment = add_response.json()["analytes"][0]
    assert attachment["analyte_code"] == analyte.code

    reorder_response = client.put(
        f"{PREFIX}/{catalog.id}/analytes/reorder",
        headers=superuser_token_headers,
        json={"items": [{"id": attachment["id"], "sort_order": 1}]},
    )
    assert reorder_response.status_code == 200
    assert reorder_response.json()["analytes"][0]["sort_order"] == 1

    delete_response = client.delete(
        f"{PREFIX}/{catalog.id}/analytes/{attachment['id']}",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["analytes"] == []


def test_analyte_attachment_rejects_panel(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    panel = create_random_catalog(db, type=CatalogType.panel)
    analyte = create_random_analyte(db)
    response = client.post(
        f"{PREFIX}/{panel.id}/analytes",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "sort_order": 1},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Cette action est réservée aux tests catalogue"


def test_upsert_and_remove_specimen_requirement(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    catalog = create_random_catalog(db, type=CatalogType.item)
    specimen_type = create_random_specimen_type(db)
    response = client.put(
        f"{PREFIX}/{catalog.id}/specimen-requirements/{specimen_type.id}",
        headers=superuser_token_headers,
        json={"volume_ml": "2.50", "instructions": "Tube sec"},
    )
    assert response.status_code == 200
    requirement = response.json()["specimen_requirements"][0]
    assert requirement["specimen_type_name"] == specimen_type.name
    assert requirement["volume_ml"] == "2.50"

    delete_response = client.delete(
        f"{PREFIX}/{catalog.id}/specimen-requirements/{specimen_type.id}",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["specimen_requirements"] == []


def test_add_reorder_and_remove_panel_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    panel = create_random_catalog(db, type=CatalogType.panel)
    test = create_random_catalog(db, type=CatalogType.item)

    add_response = client.post(
        f"{PREFIX}/{panel.id}/panel-items",
        headers=superuser_token_headers,
        json={"test_id": str(test.id), "sort_order": 2},
    )
    assert add_response.status_code == 200
    assert add_response.json()["price"] == "1000.00"
    panel_item = add_response.json()["panel_items"][0]
    assert panel_item["test_code"] == test.code

    reorder_response = client.put(
        f"{PREFIX}/{panel.id}/panel-items/reorder",
        headers=superuser_token_headers,
        json={"items": [{"id": panel_item["id"], "sort_order": 1}]},
    )
    assert reorder_response.status_code == 200
    assert reorder_response.json()["panel_items"][0]["sort_order"] == 1

    delete_response = client.delete(
        f"{PREFIX}/{panel.id}/panel-items/{panel_item['id']}",
        headers=superuser_token_headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["price"] == "0.00"
    assert delete_response.json()["panel_items"] == []


def test_catalog_panel_price_is_computed_and_sortable(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    prefix = random_lower_string(8).upper()
    low_panel = create_random_catalog(db, type=CatalogType.panel)
    low_panel.code = f"{prefix}A"
    low_panel.name = f"{prefix} low"
    high_panel = create_random_catalog(db, type=CatalogType.panel)
    high_panel.code = f"{prefix}B"
    high_panel.name = f"{prefix} high"
    low_test = create_random_catalog(db, type=CatalogType.item, price=Decimal("100.00"))
    high_test = create_random_catalog(db, type=CatalogType.item, price=Decimal("300.00"))
    db.add(low_panel)
    db.add(high_panel)
    db.commit()

    low_add = client.post(
        f"{PREFIX}/{low_panel.id}/panel-items",
        headers=superuser_token_headers,
        json={"test_id": str(low_test.id), "sort_order": 1},
    )
    assert low_add.status_code == 200
    assert low_add.json()["price"] == "100.00"

    high_add = client.post(
        f"{PREFIX}/{high_panel.id}/panel-items",
        headers=superuser_token_headers,
        json={"test_id": str(high_test.id), "sort_order": 1},
    )
    assert high_add.status_code == 200
    assert high_add.json()["price"] == "300.00"

    list_response = client.get(
        f"{PREFIX}/?search={prefix}&type=panel&sort_by=price&sort_order=desc",
        headers=superuser_token_headers,
    )
    assert list_response.status_code == 200
    rows = list_response.json()["data"]
    assert [row["id"] for row in rows[:2]] == [str(high_panel.id), str(low_panel.id)]
    assert [row["price"] for row in rows[:2]] == ["300.00", "100.00"]


def test_panel_item_rejects_panel_as_child(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    panel = create_random_catalog(db, type=CatalogType.panel)
    child_panel = create_random_catalog(db, type=CatalogType.panel)
    response = client.post(
        f"{PREFIX}/{panel.id}/panel-items",
        headers=superuser_token_headers,
        json={"test_id": str(child_panel.id), "sort_order": 1},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Seuls les tests actifs peuvent être ajoutés au panel"
