"""PaymentMethod repository — pure database access only. Never commits, never creates sessions."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import PaymentMethod


def get_by_id(*, session: Session, pm_id: uuid.UUID) -> PaymentMethod | None:
    return session.get(PaymentMethod, pm_id)


def get_all(*, session: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> tuple[list[PaymentMethod], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(PaymentMethod.is_deleted).is_(False))
    base_query = select(PaymentMethod)
    if conditions:
        base_query = base_query.where(*conditions)
    count_statement = select(func.count()).select_from(PaymentMethod)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()
    statement = base_query.order_by(col(PaymentMethod.created_at).desc()).offset(skip).limit(limit)
    return list(session.exec(statement).all()), count


def create(*, session: Session, db_obj: PaymentMethod) -> PaymentMethod:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj: PaymentMethod, update_data: dict) -> PaymentMethod:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def soft_delete(*, session: Session, db_obj: PaymentMethod) -> None:
    db_obj.is_deleted = True
    session.add(db_obj)
