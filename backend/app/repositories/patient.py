"""Patient repository - pure database access only."""

import uuid

from sqlalchemy import exists
from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    GenderType,
    InsuranceProvider,
    Order,
    Patient,
    PatientInsurance,
    SortOrder,
)

PATIENT_SORT_COLUMNS = {
    "identifier": Patient.identifier,
    "first_name": Patient.first_name,
    "last_name": Patient.last_name,
    "date_of_birth": Patient.date_of_birth,
    "created_at": Patient.created_at,
    "updated_at": Patient.updated_at,
}

INSURANCE_SORT_COLUMNS = {
    "policy_number": PatientInsurance.policy_number,
    "is_primary": PatientInsurance.is_primary,
    "created_at": PatientInsurance.created_at,
    "updated_at": PatientInsurance.updated_at,
}


def get_by_id(*, session: Session, patient_id: uuid.UUID) -> Patient | None:
    return session.get(Patient, patient_id)


def get_by_identifier(*, session: Session, identifier: str) -> Patient | None:
    statement = select(Patient).where(Patient.identifier == identifier)
    return session.exec(statement).first()


def get_all(
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
    conditions = []
    if is_deleted is not None:
        conditions.append(Patient.is_deleted == is_deleted)
    elif not include_deleted:
        conditions.append(col(Patient.is_deleted).is_(False))
    if gender is not None:
        conditions.append(Patient.gender == gender)
    if doctor_id is not None:
        conditions.append(
            exists().where(
                Order.patient_id == Patient.id,
                Order.doctor_id == doctor_id,
            )
        )
    if search:
        q = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(Patient.identifier).ilike(q),
                col(Patient.first_name).ilike(q),
                col(Patient.last_name).ilike(q),
                col(Patient.phone).ilike(q),
            )
        )

    base_query = select(Patient)
    count_statement = select(func.count()).select_from(Patient)
    if conditions:
        base_query = base_query.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    sort_column = PATIENT_SORT_COLUMNS.get(sort_by or "created_at", Patient.created_at)
    order_expr = (
        col(sort_column).desc()
        if sort_order == SortOrder.desc
        else col(sort_column).asc()
    )
    statement = (
        base_query.order_by(order_expr, col(Patient.last_name).asc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all()), count


def create(*, session: Session, db_obj: Patient) -> Patient:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj: Patient, update_data: dict) -> Patient:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def soft_delete(*, session: Session, db_obj: Patient) -> None:
    db_obj.is_deleted = True
    session.add(db_obj)


def get_insurance_by_id(
    *, session: Session, patient_id: uuid.UUID, insurance_id: uuid.UUID
) -> PatientInsurance | None:
    statement = select(PatientInsurance).where(
        PatientInsurance.id == insurance_id,
        PatientInsurance.patient_id == patient_id,
    )
    return session.exec(statement).first()


def get_insurance_with_provider_by_id(
    *, session: Session, patient_id: uuid.UUID, insurance_id: uuid.UUID
) -> tuple[PatientInsurance, InsuranceProvider] | None:
    statement = (
        select(PatientInsurance, InsuranceProvider)
        .join(
            InsuranceProvider,
            PatientInsurance.insurance_provider_id == InsuranceProvider.id,
        )
        .where(
            PatientInsurance.id == insurance_id,
            PatientInsurance.patient_id == patient_id,
        )
    )
    return session.exec(statement).first()


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
    conditions = [PatientInsurance.patient_id == patient_id]
    if is_deleted is not None:
        conditions.append(PatientInsurance.is_deleted == is_deleted)
    elif not include_deleted:
        conditions.append(col(PatientInsurance.is_deleted).is_(False))

    base_query = (
        select(PatientInsurance, InsuranceProvider)
        .join(
            InsuranceProvider,
            PatientInsurance.insurance_provider_id == InsuranceProvider.id,
        )
        .where(*conditions)
    )
    count_statement = (
        select(func.count()).select_from(PatientInsurance).where(*conditions)
    )
    count = session.exec(count_statement).one()
    sort_column = INSURANCE_SORT_COLUMNS.get(
        sort_by or "is_primary", PatientInsurance.is_primary
    )
    order_expr = (
        col(sort_column).desc()
        if sort_order == SortOrder.desc
        else col(sort_column).asc()
    )
    statement = (
        base_query.order_by(order_expr, col(PatientInsurance.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all()), count


def create_insurance(*, session: Session, db_obj: PatientInsurance) -> PatientInsurance:
    session.add(db_obj)
    session.flush()
    return db_obj


def update_insurance(
    *, session: Session, db_obj: PatientInsurance, update_data: dict
) -> PatientInsurance:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def unset_primary_insurances(
    *, session: Session, patient_id: uuid.UUID, exclude_id: uuid.UUID | None = None
) -> None:
    conditions = [
        PatientInsurance.patient_id == patient_id,
        PatientInsurance.is_primary == True,  # noqa: E712
        PatientInsurance.is_deleted == False,  # noqa: E712
    ]
    if exclude_id is not None:
        conditions.append(PatientInsurance.id != exclude_id)
    statement = select(PatientInsurance).where(*conditions)
    for db_obj in session.exec(statement).all():
        db_obj.is_primary = False
        session.add(db_obj)


def soft_delete_insurance(*, session: Session, db_obj: PatientInsurance) -> None:
    db_obj.is_deleted = True
    db_obj.is_primary = False
    session.add(db_obj)
