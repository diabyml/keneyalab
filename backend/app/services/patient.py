"""Patient business logic."""

import uuid

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    GenderType,
    InsuranceProvider,
    Patient,
    PatientCreate,
    PatientInsurance,
    PatientInsuranceCreate,
    PatientInsuranceUpdate,
    PatientUpdate,
    SortOrder,
)
from app.repositories import patient as patient_repo


def _normalize_identifier(identifier: str) -> str:
    return identifier.strip()


def _ensure_identifier_available(
    *, session: Session, identifier: str, patient_id: uuid.UUID | None = None
) -> None:
    existing = patient_repo.get_by_identifier(session=session, identifier=identifier)
    if existing is not None and existing.id != patient_id:
        raise ConflictError("Un patient avec cet identifiant existe déjà")


def _get_active_patient(*, session: Session, patient_id: uuid.UUID) -> Patient:
    db_patient = patient_repo.get_by_id(session=session, patient_id=patient_id)
    if db_patient is None:
        raise NotFoundError("Patient non trouvé")
    if db_patient.is_deleted:
        raise BusinessRuleError(
            "Le patient supprimé doit être restauré avant modification"
        )
    return db_patient


def _get_active_insurance_provider(
    *, session: Session, provider_id: uuid.UUID
) -> InsuranceProvider:
    provider = session.get(InsuranceProvider, provider_id)
    if provider is None or provider.is_deleted:
        raise NotFoundError("Assureur non trouvé")
    return provider


def create_patient(*, session: Session, patient_in: PatientCreate) -> Patient:
    data = patient_in.model_dump()
    data["identifier"] = _normalize_identifier(data["identifier"])
    _ensure_identifier_available(session=session, identifier=data["identifier"])
    db_obj = Patient.model_validate(data)
    patient_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_patients(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    gender: GenderType | None = None,
    doctor_id: uuid.UUID | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[Patient], int]:
    return patient_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        gender=gender,
        doctor_id=doctor_id,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_patient(*, session: Session, patient_id: uuid.UUID) -> Patient:
    db_obj = patient_repo.get_by_id(session=session, patient_id=patient_id)
    if db_obj is None:
        raise NotFoundError("Patient non trouvé")
    return db_obj


def update_patient(
    *, session: Session, patient_id: uuid.UUID, patient_in: PatientUpdate
) -> Patient:
    db_obj = _get_active_patient(session=session, patient_id=patient_id)
    data = patient_in.model_dump(exclude_unset=True)
    if "identifier" in data and data["identifier"] is not None:
        data["identifier"] = _normalize_identifier(data["identifier"])
        _ensure_identifier_available(
            session=session, identifier=data["identifier"], patient_id=patient_id
        )
    patient_repo.update(session=session, db_obj=db_obj, update_data=data)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_patient(*, session: Session, patient_id: uuid.UUID) -> None:
    db_obj = patient_repo.get_by_id(session=session, patient_id=patient_id)
    if db_obj is None:
        raise NotFoundError("Patient non trouvé")
    patient_repo.soft_delete(session=session, db_obj=db_obj)
    session.commit()


def restore_patient(*, session: Session, patient_id: uuid.UUID) -> Patient:
    db_obj = patient_repo.get_by_id(session=session, patient_id=patient_id)
    if db_obj is None:
        raise NotFoundError("Patient non trouvé")
    patient_repo.update(
        session=session, db_obj=db_obj, update_data={"is_deleted": False}
    )
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_patient_insurances(
    *,
    session: Session,
    patient_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[tuple[PatientInsurance, InsuranceProvider]], int]:
    get_patient(session=session, patient_id=patient_id)
    return patient_repo.get_patient_insurances(
        session=session,
        patient_id=patient_id,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        sort_by=sort_by,
        sort_order=sort_order,
    )


def get_patient_insurance_with_provider(
    *, session: Session, patient_id: uuid.UUID, insurance_id: uuid.UUID
) -> tuple[PatientInsurance, InsuranceProvider]:
    db_obj = patient_repo.get_insurance_with_provider_by_id(
        session=session, patient_id=patient_id, insurance_id=insurance_id
    )
    if db_obj is None:
        raise NotFoundError("Assurance patient non trouvée")
    return db_obj


def create_patient_insurance(
    *, session: Session, patient_id: uuid.UUID, insurance_in: PatientInsuranceCreate
) -> PatientInsurance:
    _get_active_patient(session=session, patient_id=patient_id)
    _get_active_insurance_provider(
        session=session, provider_id=insurance_in.insurance_provider_id
    )
    if insurance_in.is_primary:
        patient_repo.unset_primary_insurances(session=session, patient_id=patient_id)
        session.flush()
    db_obj = PatientInsurance.model_validate(
        {
            **insurance_in.model_dump(),
            "patient_id": patient_id,
        }
    )
    patient_repo.create_insurance(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_patient_insurance(
    *,
    session: Session,
    patient_id: uuid.UUID,
    insurance_id: uuid.UUID,
    insurance_in: PatientInsuranceUpdate,
) -> PatientInsurance:
    _get_active_patient(session=session, patient_id=patient_id)
    db_obj = patient_repo.get_insurance_by_id(
        session=session, patient_id=patient_id, insurance_id=insurance_id
    )
    if db_obj is None:
        raise NotFoundError("Assurance patient non trouvée")
    if db_obj.is_deleted:
        raise BusinessRuleError(
            "L'assurance supprimée doit être restaurée avant modification"
        )
    data = insurance_in.model_dump(exclude_unset=True)
    if data.get("is_primary") is True:
        patient_repo.unset_primary_insurances(
            session=session, patient_id=patient_id, exclude_id=insurance_id
        )
        session.flush()
    patient_repo.update_insurance(session=session, db_obj=db_obj, update_data=data)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_patient_insurance(
    *, session: Session, patient_id: uuid.UUID, insurance_id: uuid.UUID
) -> None:
    _get_active_patient(session=session, patient_id=patient_id)
    db_obj = patient_repo.get_insurance_by_id(
        session=session, patient_id=patient_id, insurance_id=insurance_id
    )
    if db_obj is None:
        raise NotFoundError("Assurance patient non trouvée")
    patient_repo.soft_delete_insurance(session=session, db_obj=db_obj)
    session.commit()


def restore_patient_insurance(
    *, session: Session, patient_id: uuid.UUID, insurance_id: uuid.UUID
) -> PatientInsurance:
    _get_active_patient(session=session, patient_id=patient_id)
    db_obj = patient_repo.get_insurance_by_id(
        session=session, patient_id=patient_id, insurance_id=insurance_id
    )
    if db_obj is None:
        raise NotFoundError("Assurance patient non trouvée")
    if db_obj.is_primary:
        patient_repo.unset_primary_insurances(
            session=session, patient_id=patient_id, exclude_id=insurance_id
        )
        session.flush()
    patient_repo.update_insurance(
        session=session, db_obj=db_obj, update_data={"is_deleted": False}
    )
    session.commit()
    session.refresh(db_obj)
    return db_obj
