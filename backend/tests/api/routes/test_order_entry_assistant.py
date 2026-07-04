import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models.lis import (
    CatalogType,
    DoctorCreate,
    GenderType,
    PatientCreate,
)
from app.services import ai_order_entry
from app.services.doctor import create_doctor
from app.services.patient import create_patient
from tests.utils.catalog import create_random_catalog, random_lower_string

PREFIX = f"{settings.API_V1_STR}/orders/entry-assistant/intake"


def test_order_entry_assistant_forbidden_for_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        PREFIX,
        headers=normal_user_token_headers,
        json={"text": "Créer une demande NFS pour Aminata Traoré"},
    )

    assert response.status_code == 403


def test_order_entry_assistant_requires_configured_ai(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        PREFIX,
        headers=superuser_token_headers,
        json={"text": "Créer une demande NFS pour Aminata Traoré"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Assistant IA non configuré"


def test_order_entry_assistant_returns_validated_intake(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    monkeypatch,
) -> None:
    catalog = create_random_catalog(
        db,
        type=CatalogType.item,
        price=Decimal("1500.00"),
    )
    patient = create_patient(
        session=db,
        patient_in=PatientCreate(
            identifier=f"PAT-{random_lower_string(8).upper()}",
            first_name="Aminata",
            last_name="Traoré",
            date_of_birth=date(1990, 5, 12),
            gender=GenderType.female,
            phone="+22370000001",
            address="Bamako",
        ),
    )
    doctor = create_doctor(
        session=db,
        doctor_in=DoctorCreate(
            first_name="Moussa",
            last_name="Diallo",
            provenance="Clinique Soleil",
            phone="+22370000002",
            title_id=None,
        ),
    )

    class FakeProvider:
        def extract_intake(self, *, text, catalog_options):
            assert "Aminata" in text
            assert any(option.id == catalog.id for option in catalog_options)
            return ai_order_entry.AIIntakeResult(
                patient=ai_order_entry.AIIntakePatient(
                    first_name=patient.first_name,
                    last_name=patient.last_name,
                    date_of_birth=patient.date_of_birth,
                    gender=patient.gender,
                    phone=patient.phone,
                    confidence=0.92,
                ),
                doctor=ai_order_entry.AIIntakeDoctor(
                    first_name=doctor.first_name,
                    last_name=doctor.last_name,
                    phone=doctor.phone,
                    confidence=0.9,
                ),
                catalog_suggestions=[
                    ai_order_entry.AIIntakeCatalogSuggestion(
                        catalog_id=catalog.id,
                        confidence=0.94,
                        reason="Demande de NFS détectée",
                        matched_terms=["NFS"],
                    ),
                    ai_order_entry.AIIntakeCatalogSuggestion(
                        catalog_id=uuid.uuid4(),
                        confidence=0.99,
                        reason="Suggestion hallucinee",
                    ),
                    ai_order_entry.AIIntakeCatalogSuggestion(
                        catalog_id=catalog.id,
                        confidence=0.4,
                        reason="Doublon faible",
                    ),
                ],
                unmatched_phrases=["test inconnu"],
                warnings=["Vérifier la date de naissance"],
            )

    monkeypatch.setattr(
        ai_order_entry,
        "get_order_entry_provider",
        lambda: FakeProvider(),
    )

    response = client.post(
        PREFIX,
        headers=superuser_token_headers,
        json={"text": "Aminata Traoré, Dr Moussa Diallo, demander NFS et test inconnu"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_draft"]["first_name"] == "Aminata"
    assert payload["patient_matches"][0]["id"] == str(patient.id)
    assert payload["doctor_draft"]["last_name"] == "Diallo"
    assert payload["doctor_matches"][0]["id"] == str(doctor.id)
    assert len(payload["catalog_suggestions"]) == 1
    assert payload["catalog_suggestions"][0]["catalog"]["id"] == str(catalog.id)
    assert payload["unmatched_phrases"] == ["test inconnu"]
    assert "Certaines suggestions IA ont été ignorées" in payload["warnings"][1]


def test_order_entry_assistant_marks_low_confidence_suggestion(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    monkeypatch,
) -> None:
    catalog = create_random_catalog(db)

    class FakeProvider:
        def extract_intake(self, *, text, catalog_options):
            return ai_order_entry.AIIntakeResult(
                catalog_suggestions=[
                    ai_order_entry.AIIntakeCatalogSuggestion(
                        catalog_id=catalog.id,
                        confidence=0.2,
                        reason="Correspondance faible",
                    )
                ],
            )

    monkeypatch.setattr(
        ai_order_entry,
        "get_order_entry_provider",
        lambda: FakeProvider(),
    )

    response = client.post(
        PREFIX,
        headers=superuser_token_headers,
        json={"text": "faire peut-être un examen proche"},
    )

    assert response.status_code == 200
    warnings = response.json()["catalog_suggestions"][0]["warnings"]
    assert "Correspondance à vérifier" in warnings
