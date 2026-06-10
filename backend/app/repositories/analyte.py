"""Analyte repository - pure database access only."""

import uuid

from sqlmodel import Session, col, func, or_, select

from app.models.lis import Analyte, AnalyteDataType


def get_by_id(*, session: Session, analyte_id: uuid.UUID) -> Analyte | None:
    return session.get(Analyte, analyte_id)


def get_by_code(*, session: Session, code: str) -> Analyte | None:
    statement = select(Analyte).where(Analyte.code == code)
    return session.exec(statement).first()


def get_by_codes(*, session: Session, codes: list[str]) -> list[Analyte]:
    if not codes:
        return []
    statement = select(Analyte).where(col(Analyte.code).in_(codes))
    return list(session.exec(statement).all())


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    data_type: AnalyteDataType | None = None,
    is_calculated: bool | None = None,
) -> tuple[list[Analyte], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(Analyte.is_deleted).is_(False))
    elif is_deleted is not None:
        conditions.append(col(Analyte.is_deleted).is_(is_deleted))
    if search:
        q = f"%{search.strip()}%"
        conditions.append(or_(col(Analyte.code).ilike(q), col(Analyte.name).ilike(q)))
    if data_type is not None:
        conditions.append(Analyte.data_type == data_type)
    if is_calculated is not None:
        conditions.append(Analyte.is_calculated == is_calculated)

    base_query = select(Analyte)
    if conditions:
        base_query = base_query.where(*conditions)

    count_statement = select(func.count()).select_from(Analyte)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()

    statement = (
        base_query.order_by(col(Analyte.code).asc(), col(Analyte.name).asc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return list(items), count


def create(*, session: Session, db_obj: Analyte) -> Analyte:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_analyte: Analyte, update_data: dict) -> Analyte:
    db_analyte.sqlmodel_update(update_data)
    session.add(db_analyte)
    return db_analyte


def soft_delete(*, session: Session, db_analyte: Analyte) -> None:
    db_analyte.is_deleted = True
    session.add(db_analyte)
