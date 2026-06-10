import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    DoctorCommissionAdjustmentCreate,
    DoctorCommissionEntryDetailPublic,
    DoctorCommissionEntryListPublic,
    PayoutStatus,
    SortOrder,
)
from app.services import doctor_commission_entry as entry_service

router = APIRouter(
    prefix="/doctor-commission-entries",
    tags=["doctor-commission-entries"],
)


@router.get(
    "/",
    dependencies=[Depends(require_permission("commissions", "view"))],
    response_model=DoctorCommissionEntryListPublic,
)
def read_entries(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    doctor_id: uuid.UUID | None = None,
    payout_status: PayoutStatus | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    return entry_service.get_entries(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        doctor_id=doctor_id,
        payout_status=payout_status,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("commissions", "view"))],
    response_model=DoctorCommissionEntryDetailPublic,
)
def read_entry(session: SessionDep, id: uuid.UUID) -> Any:
    return entry_service.get_entry(session=session, entry_id=id)


@router.post(
    "/{id}/adjustments",
    dependencies=[Depends(require_permission("commissions", "adjust"))],
    response_model=DoctorCommissionEntryDetailPublic,
)
def create_adjustment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    adjustment_in: DoctorCommissionAdjustmentCreate,
) -> Any:
    return entry_service.create_adjustment(
        session=session,
        entry_id=id,
        request=adjustment_in,
        created_by_id=current_user.id,
    )
