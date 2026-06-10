from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.lis import AnalyteDataType
from tests.utils.analyte import create_random_analyte
from tests.utils.patient_context import create_random_patient_context

PREFIX = f"{settings.API_V1_STR}/validation-rules"


def test_create_numeric_rule_and_simulate_critical(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.numeric)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "analyte_id": str(analyte.id),
            "priority": 10,
            "normal_min": "70",
            "normal_max": "110",
            "panic_min": "40",
            "panic_max": "400",
            "absurd_min": "10",
            "absurd_max": "800",
            "max_delta_percent": "25",
        },
    )
    assert response.status_code == 200
    content = response.json()
    assert content["analyte_id"] == str(analyte.id)
    assert content["analyte_code"] == analyte.code
    assert content["is_active"] is True

    simulation = client.post(
        f"{PREFIX}/simulate",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "result_value": "450"},
    )
    assert simulation.status_code == 200
    result = simulation.json()
    assert result["matched_rule"]["id"] == content["id"]
    assert result["classification"] == "critical"
    assert result["is_critical"] is True


def test_numeric_simulation_accepts_comma_decimal_inside_range(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.numeric)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "analyte_id": str(analyte.id),
            "normal_min": "3.50",
            "normal_max": "6.50",
            "panic_min": "2.00",
            "panic_max": "10.00",
            "absurd_min": "1.00",
            "absurd_max": "20.00",
        },
    )
    assert response.status_code == 200

    simulation = client.post(
        f"{PREFIX}/simulate",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "result_value": "5,20"},
    )
    assert simulation.status_code == 200
    result = simulation.json()
    assert result["classification"] == "normal"
    assert result["is_absurd"] is False


def test_priority_rule_wins(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.numeric)
    for priority, normal_max in [(1, "100"), (20, "200")]:
        response = client.post(
            f"{PREFIX}/",
            headers=superuser_token_headers,
            json={
                "analyte_id": str(analyte.id),
                "priority": priority,
                "normal_min": "0",
                "normal_max": normal_max,
            },
        )
        assert response.status_code == 200

    simulation = client.post(
        f"{PREFIX}/simulate",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "result_value": "150"},
    )
    assert simulation.status_code == 200
    result = simulation.json()
    assert result["matched_rule"]["priority"] == 20
    assert result["classification"] == "normal"


def test_inactive_rule_does_not_match(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.numeric)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "is_active": False, "normal_min": "1"},
    )
    assert response.status_code == 200

    simulation = client.post(
        f"{PREFIX}/simulate",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "result_value": "5"},
    )
    assert simulation.status_code == 200
    assert simulation.json()["classification"] == "no_rule"


def test_text_rule_regex_simulation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.text)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "analyte_id": str(analyte.id),
            "is_required": True,
            "regex_pattern": "^[A-Z]{3}$",
            "validation_message": "Format attendu: AAA",
        },
    )
    assert response.status_code == 200

    simulation = client.post(
        f"{PREFIX}/simulate",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "result_value": "abc"},
    )
    assert simulation.status_code == 200
    assert simulation.json()["classification"] == "invalid"
    assert simulation.json()["is_valid"] is False


def test_options_rule_classification(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.options)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "analyte_id": str(analyte.id),
            "allowed_values": ["Positif", "Négatif"],
            "critical_values": ["Positif"],
        },
    )
    assert response.status_code == 200

    simulation = client.post(
        f"{PREFIX}/simulate",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "result_value": "Positif"},
    )
    assert simulation.status_code == 200
    assert simulation.json()["classification"] == "critical"


def test_image_required_rule(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.image)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "is_required": True},
    )
    assert response.status_code == 200

    simulation = client.post(
        f"{PREFIX}/simulate",
        headers=superuser_token_headers,
        json={"analyte_id": str(analyte.id), "result_value": ""},
    )
    assert simulation.status_code == 200
    assert simulation.json()["classification"] == "missing"


def test_list_filters_by_context_and_age(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    analyte = create_random_analyte(db, AnalyteDataType.numeric)
    context = create_random_patient_context(db)
    response = client.post(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        json={
            "analyte_id": str(analyte.id),
            "required_context_id": str(context.id),
            "min_age_years": 18,
            "max_age_years": 65,
        },
    )
    assert response.status_code == 200
    created_id = response.json()["id"]

    list_response = client.get(
        f"{PREFIX}/?required_context_id={context.id}&age_years=30",
        headers=superuser_token_headers,
    )
    assert list_response.status_code == 200
    ids = [item["id"] for item in list_response.json()["data"]]
    assert created_id in ids
