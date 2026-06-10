"""PatientContext business logic — CRUD for reference data."""

import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import PatientContext, PatientContextCreate, PatientContextUpdate
from app.repositories import patient_context as pc_repo


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def create_patient_context(*, session: Session, pc_in: PatientContextCreate) -> PatientContext:
    db_obj = PatientContext.model_validate(pc_in)
    pc_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_patient_contexts(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[PatientContext], int]:
    return pc_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=_clean_text(search),
    )


def get_patient_context(*, session: Session, pc_id: uuid.UUID) -> PatientContext:
    db_obj = pc_repo.get_by_id(session=session, pc_id=pc_id)
    if db_obj is None:
        raise NotFoundError("Contexte patient non trouvé")
    return db_obj


def update_patient_context(*, session: Session, pc_id: uuid.UUID, pc_in: PatientContextUpdate) -> PatientContext:
    db_obj = pc_repo.get_by_id(session=session, pc_id=pc_id)
    if db_obj is None:
        raise NotFoundError("Contexte patient non trouvé")
    pc_repo.update(session=session, db_obj=db_obj, update_data=pc_in.model_dump(exclude_unset=True))
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_patient_context(*, session: Session, pc_id: uuid.UUID) -> None:
    db_obj = pc_repo.get_by_id(session=session, pc_id=pc_id)
    if db_obj is None:
        raise NotFoundError("Contexte patient non trouvé")
    pc_repo.soft_delete(session=session, db_obj=db_obj)
    session.commit()


def restore_patient_context(*, session: Session, pc_id: uuid.UUID) -> PatientContext:
    db_obj = pc_repo.get_by_id(session=session, pc_id=pc_id)
    if db_obj is None:
        raise NotFoundError("Contexte patient non trouvé")
    pc_repo.update(session=session, db_obj=db_obj, update_data={"is_deleted": False})
    session.commit()
    session.refresh(db_obj)
    return db_obj
