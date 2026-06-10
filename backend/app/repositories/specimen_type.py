"""SpecimenType repository — pure database access only."""

import uuid

from sqlmodel import Session, col, func, or_, select

from app.models.lis import SpecimenType


def get_by_id(*, session: Session, st_id: uuid.UUID) -> SpecimenType | None:
    return session.get(SpecimenType, st_id)


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[SpecimenType], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(SpecimenType.is_deleted).is_(False))
    if search:
        q = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(SpecimenType.name).ilike(q),
                col(SpecimenType.description).ilike(q),
            )
        )
    base_query = select(SpecimenType)
    if conditions:
        base_query = base_query.where(*conditions)
    count_statement = select(func.count()).select_from(SpecimenType)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()
    statement = (
        base_query.order_by(col(SpecimenType.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all()), count


def create(*, session: Session, db_obj: SpecimenType) -> SpecimenType:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj: SpecimenType, update_data: dict) -> SpecimenType:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def soft_delete(*, session: Session, db_obj: SpecimenType) -> None:
    db_obj.is_deleted = True
    session.add(db_obj)
