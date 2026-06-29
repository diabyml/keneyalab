from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.core.config import settings

PREFIX = f"{settings.API_V1_STR}/reagents"


def _create_reagent(
    client: TestClient,
    headers: dict[str, str],
    code: str = "GLU",
    minimum_stock_level: str | None = "5",
) -> dict:
    response = client.post(
        f"{PREFIX}/",
        headers=headers,
        json={
            "code": code,
            "name": f"Réactif {code}",
            "unit_label": "mL",
            "supplier": "BioSupply",
            "minimum_stock_level": minimum_stock_level,
        },
    )
    assert response.status_code == 200
    return response.json()


def _create_lot(
    client: TestClient,
    headers: dict[str, str],
    reagent_id: str,
    lot_number: str = "LOT-1",
    quantity: str = "10",
    expiry_date: date | None = None,
) -> dict:
    response = client.post(
        f"{PREFIX}/lots",
        headers=headers,
        json={
            "reagent_id": reagent_id,
            "lot_number": lot_number,
            "expiry_date": str(expiry_date or (date.today() + timedelta(days=90))),
            "received_date": str(date.today()),
            "initial_quantity": quantity,
            "unit_cost": "125.50",
            "supplier_name": "BioSupply",
            "location": "Frigo A",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_reagent_crud_and_duplicate_code(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    reagent = _create_reagent(client, superuser_token_headers, code="CRP")
    assert reagent["code"] == "CRP"
    assert reagent["is_deleted"] is False

    duplicate = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"code": "CRP", "name": "Duplicate", "unit_label": "kit"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Un réactif avec ce code existe déjà"

    update = client.put(
        f"{PREFIX}/{reagent['id']}",
        headers=superuser_token_headers,
        json={"name": "CRP Latex"},
    )
    assert update.status_code == 200
    assert update.json()["name"] == "CRP Latex"

    delete = client.delete(
        f"{PREFIX}/{reagent['id']}", headers=superuser_token_headers
    )
    assert delete.status_code == 200
    assert delete.json()["message"] == "Réactif supprimé avec succès"

    restore = client.post(
        f"{PREFIX}/{reagent['id']}/restore", headers=superuser_token_headers
    )
    assert restore.status_code == 200
    assert restore.json()["is_deleted"] is False


def test_receive_lot_creates_initial_movement_and_usage_updates_balance(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    reagent = _create_reagent(client, superuser_token_headers, code="UREE")
    lot = _create_lot(client, superuser_token_headers, reagent["id"])
    assert lot["current_quantity"] == "10.000"

    movement = client.post(
        f"{PREFIX}/movements",
        headers=superuser_token_headers,
        json={
            "lot_id": lot["id"],
            "movement_type": "used",
            "quantity": "4",
            "reason": "Contrôle quotidien",
        },
    )
    assert movement.status_code == 200
    assert movement.json()["balance_after"] == "6.000"

    lots = client.get(
        f"{PREFIX}/lots?reagent_id={reagent['id']}",
        headers=superuser_token_headers,
    )
    assert lots.status_code == 200
    assert lots.json()["data"][0]["current_quantity"] == "6.000"


def test_stock_cannot_be_negative(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    reagent = _create_reagent(client, superuser_token_headers, code="ALT")
    lot = _create_lot(
        client, superuser_token_headers, reagent["id"], lot_number="ALT-1", quantity="2"
    )

    response = client.post(
        f"{PREFIX}/movements",
        headers=superuser_token_headers,
        json={
            "lot_id": lot["id"],
            "movement_type": "used",
            "quantity": "3",
            "reason": "Saisie erronée",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Le stock ne peut pas devenir négatif"


def test_expired_lot_usage_is_blocked_and_alert_summary_counts(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    reagent = _create_reagent(client, superuser_token_headers, code="AST")
    lot = _create_lot(
        client,
        superuser_token_headers,
        reagent["id"],
        lot_number="AST-OLD",
        expiry_date=date.today() - timedelta(days=1),
    )

    response = client.post(
        f"{PREFIX}/movements",
        headers=superuser_token_headers,
        json={
            "lot_id": lot["id"],
            "movement_type": "used",
            "quantity": "1",
            "reason": "Test",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Impossible d'utiliser un lot expiré"

    summary = client.get(
        f"{PREFIX}/alerts/summary", headers=superuser_token_headers
    )
    assert summary.status_code == 200
    assert summary.json()["expired_count"] >= 1


def test_reagent_settings_update(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.put(
        f"{PREFIX}/settings",
        headers=superuser_token_headers,
        json={
            "default_expiry_warning_days": 45,
            "expiry_alerts_enabled": True,
            "low_stock_alerts_enabled": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["default_expiry_warning_days"] == 45
    assert response.json()["low_stock_alerts_enabled"] is False


def test_reagents_forbidden_without_permission(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.get(f"{PREFIX}/", headers=normal_user_token_headers)
    assert response.status_code == 403
