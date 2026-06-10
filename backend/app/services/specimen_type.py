"""SpecimenType business logic — CRUD for reference data."""

import uuid
from sqlmodel import Session
from app.core.exceptions import NotFoundError
from app.models.lis import SpecimenType, SpecimenTypeCreate, SpecimenTypeUpdate
from app.repositories import specimen_type as st_repo


def create_specimen_type(*, session: Session, st_in: SpecimenTypeCreate) -> SpecimenType:
    db_obj = SpecimenType.model_validate(st_in)
    st_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_specimen_types(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[SpecimenType], int]:
    search = search.strip() if search else None
    return st_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search or None,
    )


def get_specimen_type(*, session: Session, st_id: uuid.UUID) -> SpecimenType:
    db_obj = st_repo.get_by_id(session=session, st_id=st_id)
    if db_obj is None:
        raise NotFoundError("Type de prélèvement non trouvé")
    return db_obj


def update_specimen_type(*, session: Session, st_id: uuid.UUID, st_in: SpecimenTypeUpdate) -> SpecimenType:
    db_obj = st_repo.get_by_id(session=session, st_id=st_id)
    if db_obj is None:
        raise NotFoundError("Type de prélèvement non trouvé")
    st_repo.update(session=session, db_obj=db_obj, update_data=st_in.model_dump(exclude_unset=True))
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_specimen_type(*, session: Session, st_id: uuid.UUID) -> None:
    db_obj = st_repo.get_by_id(session=session, st_id=st_id)
    if db_obj is None:
        raise NotFoundError("Type de prélèvement non trouvé")
    st_repo.soft_delete(session=session, db_obj=db_obj)
    session.commit()


def restore_specimen_type(*, session: Session, st_id: uuid.UUID) -> SpecimenType:
    db_obj = st_repo.get_by_id(session=session, st_id=st_id)
    if db_obj is None:
        raise NotFoundError("Type de prélèvement non trouvé")
    st_repo.update(session=session, db_obj=db_obj, update_data={"is_deleted": False})
    session.commit()
    session.refresh(db_obj)
    return db_obj
