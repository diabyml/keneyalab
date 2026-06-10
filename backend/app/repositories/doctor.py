"""Doctor repository - pure database access only."""

import uuid
from datetime import date

from sqlmodel import Session, col, func, or_, select

from app.models.lis import Doctor, DoctorCommissionConfig, SortOrder, Title

DOCTOR_SORT_COLUMNS = {
    "first_name": Doctor.first_name,
    "last_name": Doctor.last_name,
    "provenance": Doctor.provenance,
    "created_at": Doctor.created_at,
    "updated_at": Doctor.updated_at,
}

CONFIG_SORT_COLUMNS = {
    "effective_from": DoctorCommissionConfig.effective_from,
    "effective_until": DoctorCommissionConfig.effective_until,
    "commission_rate": DoctorCommissionConfig.commission_rate,
    "insurance_commission_rate": DoctorCommissionConfig.insurance_commission_rate,
    "created_at": DoctorCommissionConfig.created_at,
}


def get_by_id(*, session: Session, doctor_id: uuid.UUID) -> Doctor | None:
    return session.get(Doctor, doctor_id)


def get_with_title_by_id(
    *, session: Session, doctor_id: uuid.UUID
) -> tuple[Doctor, Title | None] | None:
    statement = (
        select(Doctor, Title)
        .join(Title, Doctor.title_id == Title.id, isouter=True)
        .where(Doctor.id == doctor_id)
    )
    return session.exec(statement).first()


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    title_id: uuid.UUID | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[tuple[Doctor, Title | None]], int]:
    conditions = []
    if is_deleted is not None:
        conditions.append(Doctor.is_deleted == is_deleted)
    elif not include_deleted:
        conditions.append(col(Doctor.is_deleted).is_(False))
    if title_id is not None:
        conditions.append(Doctor.title_id == title_id)
    if search:
        q = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(Doctor.first_name).ilike(q),
                col(Doctor.last_name).ilike(q),
                col(Doctor.provenance).ilike(q),
                col(Doctor.phone).ilike(q),
            )
        )

    base_query = select(Doctor, Title).join(Title, Doctor.title_id == Title.id, isouter=True)
    count_statement = select(func.count()).select_from(Doctor)
    if conditions:
        base_query = base_query.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    sort_column = DOCTOR_SORT_COLUMNS.get(sort_by or "created_at", Doctor.created_at)
    order_expr = col(sort_column).desc() if sort_order == SortOrder.desc else col(sort_column).asc()
    statement = base_query.order_by(order_expr, col(Doctor.last_name).asc()).offset(skip).limit(limit)
    return list(session.exec(statement).all()), count


def create(*, session: Session, db_obj: Doctor) -> Doctor:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj: Doctor, update_data: dict) -> Doctor:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def soft_delete(*, session: Session, db_obj: Doctor) -> None:
    db_obj.is_deleted = True
    session.add(db_obj)


def get_config_by_id(
    *, session: Session, config_id: uuid.UUID
) -> DoctorCommissionConfig | None:
    return session.get(DoctorCommissionConfig, config_id)


def get_configs(
    *,
    session: Session,
    doctor_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> tuple[list[DoctorCommissionConfig], int]:
    conditions = [DoctorCommissionConfig.doctor_id == doctor_id]
    count_statement = select(func.count()).select_from(DoctorCommissionConfig).where(*conditions)
    count = session.exec(count_statement).one()
    sort_column = CONFIG_SORT_COLUMNS.get(sort_by or "effective_from", DoctorCommissionConfig.effective_from)
    order_expr = col(sort_column).desc() if sort_order == SortOrder.desc else col(sort_column).asc()
    statement = (
        select(DoctorCommissionConfig)
        .where(*conditions)
        .order_by(order_expr, col(DoctorCommissionConfig.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all()), count


def get_overlapping_configs(
    *,
    session: Session,
    doctor_id: uuid.UUID,
    effective_from: date,
    effective_until: date | None,
    exclude_id: uuid.UUID | None = None,
) -> list[DoctorCommissionConfig]:
    new_end = effective_until or date.max
    statement = select(DoctorCommissionConfig).where(
        DoctorCommissionConfig.doctor_id == doctor_id,
        DoctorCommissionConfig.effective_from < new_end,
    )
    if exclude_id is not None:
        statement = statement.where(DoctorCommissionConfig.id != exclude_id)
    rows = session.exec(statement).all()
    return [
        row
        for row in rows
        if (row.effective_until or date.max) > effective_from
    ]


def create_config(
    *, session: Session, db_obj: DoctorCommissionConfig
) -> DoctorCommissionConfig:
    session.add(db_obj)
    session.flush()
    return db_obj


def update_config(
    *, session: Session, db_obj: DoctorCommissionConfig, update_data: dict
) -> DoctorCommissionConfig:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj
