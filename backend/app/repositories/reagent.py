"""Reagent inventory repository - pure database access only."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import (
    Reagent,
    ReagentLot,
    ReagentLotStatus,
    ReagentStockMovement,
)


def get_reagent(*, session: Session, reagent_id: uuid.UUID) -> Reagent | None:
    return session.get(Reagent, reagent_id)


def get_lot(*, session: Session, lot_id: uuid.UUID) -> ReagentLot | None:
    return session.get(ReagentLot, lot_id)


def get_reagent_by_code(*, session: Session, code: str) -> Reagent | None:
    statement = select(Reagent).where(col(Reagent.code) == code)
    return session.exec(statement).first()


def get_lot_by_number(
    *, session: Session, reagent_id: uuid.UUID, lot_number: str
) -> ReagentLot | None:
    statement = select(ReagentLot).where(
        ReagentLot.reagent_id == reagent_id,
        col(ReagentLot.lot_number) == lot_number,
    )
    return session.exec(statement).first()


def list_reagents(
    *,
    session: Session,
    skip: int,
    limit: int,
    include_deleted: bool,
    is_deleted: bool | None,
    search: str | None,
) -> tuple[list[Reagent], int]:
    conditions = []
    if is_deleted is not None:
        conditions.append(col(Reagent.is_deleted).is_(is_deleted))
    elif not include_deleted:
        conditions.append(col(Reagent.is_deleted).is_(False))
    if search:
        pattern = f"%{search.strip()}%"
        conditions.append(col(Reagent.name).ilike(pattern) | col(Reagent.code).ilike(pattern))

    statement = select(Reagent)
    count_statement = select(func.count()).select_from(Reagent)
    if conditions:
        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    items = session.exec(
        statement.order_by(col(Reagent.name).asc()).offset(skip).limit(limit)
    ).all()
    return list(items), count


def list_lots(
    *,
    session: Session,
    skip: int,
    limit: int,
    reagent_id: uuid.UUID | None,
    status: ReagentLotStatus | None,
    search: str | None,
) -> tuple[list[tuple[ReagentLot, Reagent]], int]:
    conditions = []
    if reagent_id:
        conditions.append(ReagentLot.reagent_id == reagent_id)
    if status:
        conditions.append(ReagentLot.status == status)
    if search:
        pattern = f"%{search.strip()}%"
        conditions.append(
            col(ReagentLot.lot_number).ilike(pattern) | col(Reagent.name).ilike(pattern)
        )

    statement = select(ReagentLot, Reagent).join(Reagent, Reagent.id == ReagentLot.reagent_id)
    count_statement = select(func.count()).select_from(ReagentLot).join(
        Reagent, Reagent.id == ReagentLot.reagent_id
    )
    if conditions:
        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    rows = session.exec(
        statement.order_by(col(ReagentLot.expiry_date).asc()).offset(skip).limit(limit)
    ).all()
    return list(rows), count


def list_movements(
    *,
    session: Session,
    skip: int,
    limit: int,
    reagent_id: uuid.UUID | None,
    lot_id: uuid.UUID | None,
) -> tuple[list[tuple[ReagentStockMovement, Reagent, ReagentLot]], int]:
    conditions = []
    if reagent_id:
        conditions.append(ReagentStockMovement.reagent_id == reagent_id)
    if lot_id:
        conditions.append(ReagentStockMovement.lot_id == lot_id)

    statement = (
        select(ReagentStockMovement, Reagent, ReagentLot)
        .join(Reagent, Reagent.id == ReagentStockMovement.reagent_id)
        .join(ReagentLot, ReagentLot.id == ReagentStockMovement.lot_id)
    )
    count_statement = select(func.count()).select_from(ReagentStockMovement)
    if conditions:
        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    rows = session.exec(
        statement.order_by(col(ReagentStockMovement.performed_at).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), count


def active_lots_for_reagents(
    *, session: Session, reagent_ids: list[uuid.UUID]
) -> list[ReagentLot]:
    if not reagent_ids:
        return []
    statement = select(ReagentLot).where(
        col(ReagentLot.reagent_id).in_(reagent_ids),
        ReagentLot.status == ReagentLotStatus.active,
    )
    return list(session.exec(statement).all())


def create(*, session: Session, db_obj):
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_obj, update_data: dict):
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj
