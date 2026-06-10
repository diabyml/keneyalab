"""PatientContext repository — pure database access only. Never commits, never creates sessions."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import PatientContext


def get_by_id(*, session: Session, pc_id: uuid.UUID) -> PatientContext | None:
    return session.get(PatientContext, pc_id)


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[PatientContext], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(PatientContext.is_deleted).is_(False))
    if search:
        conditions.append(col(PatientContext.name).ilike(f"%{search.strip()}%"))
    base_query = select(PatientContext)
    if conditions:
        base_query = base_query.where(*conditions)
    count_statement = select(func.count()).select_from(PatientContext)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()
    statement = base_query.order_by(col(PatientContext.created_at).desc()).offset(skip).limit(limit)
    return list(session.exec(statement).all()), count


def create(*, session: Session, db_obj: PatientContext) -> PatientContext:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj: PatientContext, update_data: dict) -> PatientContext:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def soft_delete(*, session: Session, db_obj: PatientContext) -> None:
    db_obj.is_deleted = True
    session.add(db_obj)
