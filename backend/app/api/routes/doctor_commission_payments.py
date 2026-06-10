import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    DoctorCommissionPayableLinesPublic,
    DoctorCommissionPaymentCreate,
    DoctorCommissionPaymentDetailPublic,
    DoctorCommissionPaymentListPublic,
    DoctorCommissionPaymentPreviewPublic,
    DoctorsPublic,
    DoctorWithTitlePublic,
    PaymentMethodsPublic,
    SortOrder,
)
from app.services import billing as billing_service
from app.services import doctor as doctor_service
from app.services import doctor_commission_payment as payment_service

router = APIRouter(
    prefix="/doctor-commission-payments",
    tags=["doctor-commission-payments"],
)


@router.get(
    "/",
    dependencies=[Depends(require_permission("commissions", "view"))],
    response_model=DoctorCommissionPaymentListPublic,
)
def read_payments(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    doctor_id: uuid.UUID | None = None,
    payment_method_id: uuid.UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    search: str | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    return payment_service.get_payments(
        session=session,
        skip=skip,
        limit=limit,
        doctor_id=doctor_id,
        payment_method_id=payment_method_id,
        created_from=created_from,
        created_to=created_to,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/doctor-options",
    dependencies=[Depends(require_permission("commissions", "view"))],
    response_model=DoctorsPublic,
)
def read_doctor_options(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> Any:
    rows, count = doctor_service.get_doctors(
        session=session, skip=skip, limit=limit, search=search
    )
    return DoctorsPublic(
        data=[
            DoctorWithTitlePublic(
                **doctor.model_dump(),
                title_name=title.name if title else None,
            )
            for doctor, title in rows
        ],
        count=count,
    )


@router.get(
    "/payment-method-options",
    dependencies=[Depends(require_permission("commissions", "view"))],
    response_model=PaymentMethodsPublic,
)
def read_payment_method_options(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> Any:
    return billing_service.get_payment_method_options(
        session=session, search=search, skip=skip, limit=limit
    )


@router.get(
    "/payable-lines",
    dependencies=[Depends(require_permission("commissions", "view"))],
    response_model=DoctorCommissionPayableLinesPublic,
)
def read_payable_lines(
    session: SessionDep,
    skip: int = 0,
    limit: int = 50,
    doctor_id: uuid.UUID | None = None,
    search: str | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    return payment_service.get_payable_lines(
        session=session,
        skip=skip,
        limit=limit,
        doctor_id=doctor_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post(
    "/preview",
    dependencies=[Depends(require_permission("commissions", "pay"))],
    response_model=DoctorCommissionPaymentPreviewPublic,
)
def preview_payment(
    *, session: SessionDep, payment_in: DoctorCommissionPaymentCreate
) -> Any:
    return payment_service.preview_payment(session=session, request=payment_in)


@router.post(
    "/",
    dependencies=[Depends(require_permission("commissions", "pay"))],
    response_model=DoctorCommissionPaymentDetailPublic,
)
def create_payment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    payment_in: DoctorCommissionPaymentCreate,
) -> Any:
    return payment_service.create_payment(
        session=session, request=payment_in, created_by=current_user.id
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("commissions", "view"))],
    response_model=DoctorCommissionPaymentDetailPublic,
)
def read_payment(session: SessionDep, id: uuid.UUID) -> Any:
    return payment_service.get_payment(session=session, payment_id=id)
