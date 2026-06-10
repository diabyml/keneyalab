"""Unit business logic — CRUD for reference data (no ownership checks)."""

import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import Unit, UnitCreate, UnitUpdate
from app.repositories import unit as unit_repo


def create_unit(*, session: Session, unit_in: UnitCreate) -> Unit:
    db_unit = Unit.model_validate(unit_in)
    unit_repo.create(session=session, db_obj=db_unit)
    session.commit()
    session.refresh(db_unit)
    return db_unit


def get_units(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[Unit], int]:
    search = search.strip() if search else None
    return unit_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search or None,
    )


def get_unit(*, session: Session, unit_id: uuid.UUID) -> Unit:
    db_unit = unit_repo.get_by_id(session=session, unit_id=unit_id)
    if db_unit is None:
        raise NotFoundError("Unité non trouvée")
    return db_unit


def update_unit(
    *, session: Session, unit_id: uuid.UUID, unit_in: UnitUpdate
) -> Unit:
    db_unit = unit_repo.get_by_id(session=session, unit_id=unit_id)
    if db_unit is None:
        raise NotFoundError("Unité non trouvée")

    update_data = unit_in.model_dump(exclude_unset=True)
    unit_repo.update(session=session, db_unit=db_unit, update_data=update_data)
    session.commit()
    session.refresh(db_unit)
    return db_unit


def delete_unit(*, session: Session, unit_id: uuid.UUID) -> None:
    db_unit = unit_repo.get_by_id(session=session, unit_id=unit_id)
    if db_unit is None:
        raise NotFoundError("Unité non trouvée")

    unit_repo.soft_delete(session=session, db_unit=db_unit)
    session.commit()


def restore_unit(*, session: Session, unit_id: uuid.UUID) -> Unit:
    """Restore a soft-deleted unit."""
    db_unit = unit_repo.get_by_id(session=session, unit_id=unit_id)
    if db_unit is None:
        raise NotFoundError("Unité non trouvée")

    unit_repo.update(
        session=session, db_unit=db_unit, update_data={"is_deleted": False}
    )
    session.commit()
    session.refresh(db_unit)
    return db_unit
