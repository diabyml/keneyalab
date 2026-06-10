from fastapi.testclient import TestClient

from app.core.config import settings

PREFIX = f"{settings.API_V1_STR}/finance-settings"


def test_read_and_update_finance_settings(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(f"{PREFIX}/", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["discount_allocation_policy"] in {
        "proportional",
        "non_insured_first",
        "insured_first",
    }

    response = client.put(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"discount_allocation_policy": "proportional"},
    )
    assert response.status_code == 200
    assert response.json()["discount_allocation_policy"] == "proportional"

    response = client.put(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"discount_allocation_policy": "non_insured_first"},
    )
    assert response.status_code == 200


def test_finance_settings_forbidden_without_permission(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    response = client.get(f"{PREFIX}/", headers=normal_user_token_headers)
    assert response.status_code == 403
