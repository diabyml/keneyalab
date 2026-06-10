import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    Message,
    RejectionReasonCreate,
    RejectionReasonPublic,
    RejectionReasonsPublic,
    RejectionReasonUpdate,
)
from app.services import rejection_reason as rr_service

router = APIRouter(prefix="/rejection-reasons", tags=["rejection-reasons"])


@router.get("/", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=RejectionReasonsPublic)
def read_rejection_reasons(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> Any:
    items, count = rr_service.get_rejection_reasons(session=session, skip=skip, limit=limit, include_deleted=include_deleted)
    return RejectionReasonsPublic(data=[RejectionReasonPublic.model_validate(i) for i in items], count=count)


@router.get("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=RejectionReasonPublic)
def read_rejection_reason(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return rr_service.get_rejection_reason(session=session, rr_id=id)


@router.post("/", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=RejectionReasonPublic)
def create_rejection_reason(*, session: SessionDep, current_user: CurrentUser, rr_in: RejectionReasonCreate) -> Any:
    return rr_service.create_rejection_reason(session=session, rr_in=rr_in)


@router.put("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=RejectionReasonPublic)
def update_rejection_reason(*, session: SessionDep, current_user: CurrentUser, id: uuid.UUID, rr_in: RejectionReasonUpdate) -> Any:
    return rr_service.update_rejection_reason(session=session, rr_id=id, rr_in=rr_in)


@router.delete("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))])
def delete_rejection_reason(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Message:
    rr_service.delete_rejection_reason(session=session, rr_id=id)
    return Message(message="Motif de rejet supprimé avec succès")


@router.post("/{id}/restore", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=RejectionReasonPublic)
def restore_rejection_reason(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return rr_service.restore_rejection_reason(session=session, rr_id=id)
