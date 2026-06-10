import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentUser,
    SessionDep,
    require_any_permission,
    require_permission,
)
from app.models import (
    InsuranceProvidersPublic,
    InvoiceDetailPublic,
    InvoiceListPublic,
    InvoiceReissueRequest,
    InvoiceSummaryPublic,
    PaymentCollect,
    PaymentMethodsPublic,
    PaymentRefundCreate,
    PaymentStatus,
    SortOrder,
)
from app.services import billing as billing_service

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _filters(
    *,
    search: str | None,
    payment_status: PaymentStatus | None,
    insurance_provider_id: uuid.UUID | None,
    payment_method_id: uuid.UUID | None,
    is_voided: bool | None,
    created_from: datetime | None,
    created_to: datetime | None,
    min_net_amount: Decimal | None,
    max_net_amount: Decimal | None,
):
    return {
        "search": search,
        "payment_status": payment_status,
        "insurance_provider_id": insurance_provider_id,
        "payment_method_id": payment_method_id,
        "is_voided": is_voided,
        "created_from": created_from,
        "created_to": created_to,
        "min_net_amount": min_net_amount,
        "max_net_amount": max_net_amount,
    }


@router.get(
    "/",
    dependencies=[Depends(require_permission("invoices", "view"))],
    response_model=InvoiceListPublic,
)
def read_invoices(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    payment_status: PaymentStatus | None = None,
    insurance_provider_id: uuid.UUID | None = None,
    payment_method_id: uuid.UUID | None = None,
    is_voided: bool | None = False,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    min_net_amount: Decimal | None = None,
    max_net_amount: Decimal | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    return billing_service.get_invoices(
        session=session,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **_filters(
            search=search,
            payment_status=payment_status,
            insurance_provider_id=insurance_provider_id,
            payment_method_id=payment_method_id,
            is_voided=is_voided,
            created_from=created_from,
            created_to=created_to,
            min_net_amount=min_net_amount,
            max_net_amount=max_net_amount,
        ),
    )


@router.get(
    "/summary",
    dependencies=[Depends(require_permission("invoices", "view"))],
    response_model=InvoiceSummaryPublic,
)
def read_invoice_summary(
    session: SessionDep,
    search: str | None = None,
    payment_status: PaymentStatus | None = None,
    insurance_provider_id: uuid.UUID | None = None,
    payment_method_id: uuid.UUID | None = None,
    is_voided: bool | None = False,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    min_net_amount: Decimal | None = None,
    max_net_amount: Decimal | None = None,
) -> Any:
    return billing_service.get_summary(
        session=session,
        **_filters(
            search=search,
            payment_status=payment_status,
            insurance_provider_id=insurance_provider_id,
            payment_method_id=payment_method_id,
            is_voided=is_voided,
            created_from=created_from,
            created_to=created_to,
            min_net_amount=min_net_amount,
            max_net_amount=max_net_amount,
        ),
    )


@router.get(
    "/payment-method-options",
    dependencies=[
        Depends(
            require_any_permission(
                ("invoices", "view"),
                ("payments", "collect"),
                ("payments", "refund"),
            )
        )
    ],
    response_model=PaymentMethodsPublic,
)
def read_invoice_payment_method_options(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> Any:
    return billing_service.get_payment_method_options(
        session=session, search=search, skip=skip, limit=limit
    )


@router.get(
    "/insurance-provider-options",
    dependencies=[Depends(require_permission("invoices", "view"))],
    response_model=InsuranceProvidersPublic,
)
def read_invoice_insurance_provider_options(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> Any:
    return billing_service.get_insurance_provider_options(
        session=session, search=search, skip=skip, limit=limit
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("invoices", "view"))],
    response_model=InvoiceDetailPublic,
)
def read_invoice(session: SessionDep, id: uuid.UUID) -> Any:
    return billing_service.get_invoice_detail(session=session, invoice_id=id)


@router.post(
    "/{id}/payments",
    dependencies=[Depends(require_permission("payments", "collect"))],
    response_model=InvoiceDetailPublic,
)
def collect_invoice_payment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    payment_in: PaymentCollect,
) -> Any:
    return billing_service.collect_payment(
        session=session,
        invoice_id=id,
        payment_in=payment_in,
        collected_by_id=current_user.id,
    )


@router.post(
    "/{id}/payments/{payment_id}/refunds",
    dependencies=[Depends(require_permission("payments", "refund"))],
    response_model=InvoiceDetailPublic,
)
def refund_invoice_payment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    payment_id: uuid.UUID,
    refund_in: PaymentRefundCreate,
) -> Any:
    return billing_service.refund_payment(
        session=session,
        invoice_id=id,
        payment_id=payment_id,
        request=refund_in,
        refunded_by_id=current_user.id,
    )


@router.post(
    "/{id}/reissue",
    dependencies=[
        Depends(require_permission("invoices", "edit")),
        Depends(require_permission("invoices", "void")),
    ],
    response_model=InvoiceDetailPublic,
)
def reissue_invoice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    reissue_in: InvoiceReissueRequest,
) -> Any:
    return billing_service.reissue_invoice(
        session=session,
        invoice_id=id,
        request=reissue_in,
        created_by_id=current_user.id,
    )
