import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    PaymentStatus,
    RejectionReasonsPublic,
    SortOrder,
    SpecimenCollectRequest,
    SpecimenQueuePublic,
    SpecimenRejectRequest,
    SpecimenTypesPublic,
    SpecimenWorkspacePublic,
)
from app.services import specimen as specimen_service

router = APIRouter(prefix="/specimens", tags=["specimens"])


@router.get(
    "/type-options",
    dependencies=[Depends(require_permission("specimens", "view"))],
    response_model=SpecimenTypesPublic,
)
def read_specimen_type_options(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> Any:
    return specimen_service.get_specimen_type_options(
        session=session, search=search, skip=skip, limit=limit
    )


@router.get(
    "/queue",
    dependencies=[Depends(require_permission("specimens", "view"))],
    response_model=SpecimenQueuePublic,
)
def read_collection_queue(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    view: Literal["waiting", "history"] = "waiting",
    specimen_type_id: uuid.UUID | None = None,
    payment_status: PaymentStatus | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    return specimen_service.get_queue(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        view=view,
        specimen_type_id=specimen_type_id,
        payment_status=payment_status,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/rejection-reason-options",
    dependencies=[Depends(require_permission("specimens", "reject"))],
    response_model=RejectionReasonsPublic,
)
def read_rejection_reason_options(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> Any:
    return specimen_service.get_rejection_reason_options(
        session=session, search=search, skip=skip, limit=limit
    )


@router.get(
    "/orders/{order_id}",
    dependencies=[Depends(require_permission("specimens", "view"))],
    response_model=SpecimenWorkspacePublic,
)
def read_collection_workspace(
    session: SessionDep, order_id: uuid.UUID
) -> Any:
    return specimen_service.get_workspace(session=session, order_id=order_id)


@router.post(
    "/collect",
    dependencies=[Depends(require_permission("specimens", "collect"))],
    response_model=SpecimenWorkspacePublic,
)
def collect_specimens(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request_in: SpecimenCollectRequest,
) -> Any:
    return specimen_service.collect(
        session=session,
        request=request_in,
        collected_by_id=current_user.id,
    )


@router.post(
    "/orders/{order_id}/collect-all",
    dependencies=[Depends(require_permission("specimens", "collect"))],
    response_model=SpecimenWorkspacePublic,
)
def collect_all_specimens(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
) -> Any:
    return specimen_service.collect_all(
        session=session,
        order_id=order_id,
        collected_by_id=current_user.id,
    )


@router.post(
    "/{specimen_id}/reject",
    dependencies=[Depends(require_permission("specimens", "reject"))],
    response_model=SpecimenWorkspacePublic,
)
def reject_specimen(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    specimen_id: uuid.UUID,
    request_in: SpecimenRejectRequest,
) -> Any:
    return specimen_service.reject(
        session=session,
        specimen_id=specimen_id,
        request=request_in,
        rejected_by_id=current_user.id,
    )
