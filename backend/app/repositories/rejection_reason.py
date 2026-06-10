"""RejectionReason repository — pure database access only. Never commits, never creates sessions."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import RejectionReason


def get_by_id(*, session: Session, rr_id: uuid.UUID) -> RejectionReason | None:
    return session.get(RejectionReason, rr_id)


def get_all(*, session: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> tuple[list[RejectionReason], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(RejectionReason.is_deleted).is_(False))
    base_query = select(RejectionReason)
    if conditions:
        base_query = base_query.where(*conditions)
    count_statement = select(func.count()).select_from(RejectionReason)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()
    statement = base_query.order_by(col(RejectionReason.created_at).desc()).offset(skip).limit(limit)
    return list(session.exec(statement).all()), count


def create(*, session: Session, db_obj: RejectionReason) -> RejectionReason:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj: RejectionReason, update_data: dict) -> RejectionReason:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def soft_delete(*, session: Session, db_obj: RejectionReason) -> None:
    db_obj.is_deleted = True
    session.add(db_obj)
