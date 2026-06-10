"""RejectionReason business logic — CRUD for reference data."""

import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import RejectionReason, RejectionReasonCreate, RejectionReasonUpdate
from app.repositories import rejection_reason as rr_repo


def create_rejection_reason(*, session: Session, rr_in: RejectionReasonCreate) -> RejectionReason:
    db_obj = RejectionReason.model_validate(rr_in)
    rr_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_rejection_reasons(*, session: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> tuple[list[RejectionReason], int]:
    return rr_repo.get_all(session=session, skip=skip, limit=limit, include_deleted=include_deleted)


def get_rejection_reason(*, session: Session, rr_id: uuid.UUID) -> RejectionReason:
    db_obj = rr_repo.get_by_id(session=session, rr_id=rr_id)
    if db_obj is None:
        raise NotFoundError("Motif de rejet non trouvé")
    return db_obj


def update_rejection_reason(*, session: Session, rr_id: uuid.UUID, rr_in: RejectionReasonUpdate) -> RejectionReason:
    db_obj = rr_repo.get_by_id(session=session, rr_id=rr_id)
    if db_obj is None:
        raise NotFoundError("Motif de rejet non trouvé")
    rr_repo.update(session=session, db_obj=db_obj, update_data=rr_in.model_dump(exclude_unset=True))
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_rejection_reason(*, session: Session, rr_id: uuid.UUID) -> None:
    db_obj = rr_repo.get_by_id(session=session, rr_id=rr_id)
    if db_obj is None:
        raise NotFoundError("Motif de rejet non trouvé")
    rr_repo.soft_delete(session=session, db_obj=db_obj)
    session.commit()


def restore_rejection_reason(*, session: Session, rr_id: uuid.UUID) -> RejectionReason:
    db_obj = rr_repo.get_by_id(session=session, rr_id=rr_id)
    if db_obj is None:
        raise NotFoundError("Motif de rejet non trouvé")
    rr_repo.update(session=session, db_obj=db_obj, update_data={"is_deleted": False})
    session.commit()
    session.refresh(db_obj)
    return db_obj
