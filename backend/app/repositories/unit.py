"""Unit repository — pure database access only. Never commits, never creates sessions."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import Unit


def get_by_id(*, session: Session, unit_id: uuid.UUID) -> Unit | None:
    return session.get(Unit, unit_id)


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[Unit], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(Unit.is_deleted).is_(False))
    if search:
        conditions.append(col(Unit.name).ilike(f"%{search.strip()}%"))

    base_query = select(Unit)
    if conditions:
        base_query = base_query.where(*conditions)

    count_statement = select(func.count()).select_from(Unit)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()

    statement = (
        base_query.order_by(col(Unit.created_at).desc()).offset(skip).limit(limit)
    )
    items = session.exec(statement).all()
    return list(items), count


def create(*, session: Session, db_obj: Unit) -> Unit:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_unit: Unit, update_data: dict) -> Unit:
    db_unit.sqlmodel_update(update_data)
    session.add(db_unit)
    return db_unit


def soft_delete(*, session: Session, db_unit: Unit) -> None:
    db_unit.is_deleted = True
    session.add(db_unit)
