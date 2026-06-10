import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.models.lis import Doctor, GenderType, Order, Patient

PREFIX = f"{settings.API_V1_STR}/patients"


def _accession_number() -> str:
    return f"ORD-{uuid.uuid4().hex[:20]}"


def _patient(identifier: str, first_name: str, *, is_deleted: bool = False) -> Patient:
    return Patient(
        identifier=identifier,
        first_name=first_name,
        last_name="Historique",
        date_of_birth=date(1990, 1, 1),
        gender=GenderType.female,
        phone="+22370000000",
        is_deleted=is_deleted,
    )


def test_read_patients_filtered_by_doctor(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    doctor = Doctor(first_name="Awa", last_name="Traoré")
    other_doctor = Doctor(first_name="Moussa", last_name="Diallo")
    first = _patient(f"DOC-{uuid.uuid4()}", "Alpha")
    second = _patient(f"DOC-{uuid.uuid4()}", "Beta")
    other = _patient(f"DOC-{uuid.uuid4()}", "Gamma")
    deleted = _patient(f"DOC-{uuid.uuid4()}", "Delta", is_deleted=True)
    db.add_all([doctor, other_doctor, first, second, other, deleted])
    db.flush()

    creator = db.exec(select(User)).first()
    assert creator is not None
    orders = [
        Order(
            accession_number=_accession_number(),
            patient_id=first.id,
            doctor_id=doctor.id,
            created_by=creator.id,
        ),
        Order(
            accession_number=_accession_number(),
            patient_id=first.id,
            doctor_id=doctor.id,
            created_by=creator.id,
        ),
        Order(
            accession_number=_accession_number(),
            patient_id=second.id,
            doctor_id=doctor.id,
            created_by=creator.id,
        ),
        Order(
            accession_number=_accession_number(),
            patient_id=other.id,
            doctor_id=other_doctor.id,
            created_by=creator.id,
        ),
        Order(
            accession_number=_accession_number(),
            patient_id=deleted.id,
            doctor_id=doctor.id,
            created_by=creator.id,
        ),
    ]
    db.add_all(orders)
    db.commit()

    response = client.get(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        params={
            "doctor_id": str(doctor.id),
            "sort_by": "first_name",
            "sort_order": "asc",
            "limit": 1,
        },
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 2
    assert [item["id"] for item in content["data"]] == [str(first.id)]

    second_page = client.get(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        params={
            "doctor_id": str(doctor.id),
            "sort_by": "first_name",
            "sort_order": "asc",
            "skip": 1,
            "limit": 1,
        },
    )
    assert second_page.status_code == 200
    assert [item["id"] for item in second_page.json()["data"]] == [str(second.id)]

    search = client.get(
        f"{PREFIX}/",
        headers=superuser_token_headers,
        params={"doctor_id": str(doctor.id), "search": second.identifier},
    )
    assert search.status_code == 200
    assert search.json()["count"] == 1
    assert [item["id"] for item in search.json()["data"]] == [str(second.id)]

    for order in orders:
        db.delete(order)
    for patient in [first, second, other, deleted]:
        db.delete(patient)
    db.delete(doctor)
    db.delete(other_doctor)
    db.commit()
