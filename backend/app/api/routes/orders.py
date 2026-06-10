import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import col, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    require_any_permission,
    require_permission,
)
from app.models import (
    CatalogDetailPublic,
    CatalogSummariesPublic,
    CatalogType,
    OrderCreate,
    OrderDetailPublic,
    OrderListPublic,
    OrderPreviewPublic,
    OrderPreviewRequest,
    OrderRevisionsPublic,
    OrderStatus,
    OrderUpdate,
    PaymentCollect,
    PaymentMethod,
    PaymentMethodPublic,
    PaymentMethodsPublic,
    PaymentTransactionPublic,
    SortOrder,
    SuggestedIdentifierPublic,
)
from app.services import catalog as catalog_service
from app.services import order as order_service
from app.services import permission as permission_service

router = APIRouter(prefix="/orders", tags=["orders"])
invoice_router = APIRouter(prefix="/invoices", tags=["invoices"])


def _can(session: SessionDep, user: CurrentUser, resource: str, action: str) -> bool:
    return permission_service.check_permission(
        session=session, user=user, resource=resource, action=action
    )


@router.get(
    "/",
    dependencies=[Depends(require_permission("orders", "view"))],
    response_model=OrderListPublic,
)
def read_orders(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    status: OrderStatus | None = None,
    patient_id: uuid.UUID | None = None,
    doctor_id: uuid.UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    items, count = order_service.get_orders(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        patient_id=patient_id,
        doctor_id=doctor_id,
        created_from=created_from,
        created_to=created_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return OrderListPublic(data=items, count=count)


@router.get(
    "/catalog-options",
    dependencies=[
        Depends(
            require_any_permission(
                ("orders", "create"),
                ("orders", "edit"),
            )
        )
    ],
    response_model=CatalogSummariesPublic,
)
def read_order_catalog_options(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    type: CatalogType | None = None,
    category_id: uuid.UUID | None = None,
) -> Any:
    items, count = catalog_service.get_catalogs(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        type=type,
        category_id=category_id,
        is_orderable=True,
        is_deleted=False,
        exclude_empty_panels=True,
        sort_by="code",
    )
    return CatalogSummariesPublic(data=items, count=count)


@router.get(
    "/payment-method-options",
    dependencies=[
        Depends(
            require_any_permission(
                ("orders", "create"),
                ("payments", "collect"),
            )
        )
    ],
    response_model=PaymentMethodsPublic,
)
def read_payment_method_options(session: SessionDep) -> Any:
    methods = list(
        session.exec(
            select(PaymentMethod)
            .where(PaymentMethod.is_deleted == False)  # noqa: E712
            .order_by(col(PaymentMethod.name).asc())
        ).all()
    )
    return PaymentMethodsPublic(
        data=[PaymentMethodPublic.model_validate(item) for item in methods],
        count=len(methods),
    )


@router.get(
    "/catalog-options/{id}",
    dependencies=[
        Depends(
            require_any_permission(
                ("orders", "create"),
                ("orders", "edit"),
            )
        )
    ],
    response_model=CatalogDetailPublic,
)
def read_order_catalog_option(session: SessionDep, id: uuid.UUID) -> Any:
    detail = catalog_service.get_catalog(session=session, catalog_id=id)
    if detail.type == CatalogType.panel and not detail.panel_items:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Entrée catalogue non disponible")
    return detail


@router.get(
    "/suggested-patient-identifier",
    dependencies=[Depends(require_permission("patients", "create"))],
    response_model=SuggestedIdentifierPublic,
)
def suggested_patient_identifier(session: SessionDep) -> Any:
    return SuggestedIdentifierPublic(
        identifier=order_service.suggest_patient_identifier(session=session)
    )


@router.post(
    "/preview",
    dependencies=[Depends(require_permission("orders", "create"))],
    response_model=OrderPreviewPublic,
)
def preview_order(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request_in: OrderPreviewRequest,
) -> Any:
    return order_service.preview_order(
        session=session,
        request=request_in,
        can_override_prices=_can(session, current_user, "order_items", "edit"),
        can_discount=_can(session, current_user, "invoices", "edit"),
        can_collect_payment=_can(session, current_user, "payments", "collect"),
    )


@router.post(
    "/",
    dependencies=[Depends(require_permission("orders", "create"))],
    response_model=OrderDetailPublic,
)
def create_order(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    order_in: OrderCreate,
) -> Any:
    order = order_service.create_order(
        session=session,
        request=order_in,
        created_by_id=current_user.id,
        can_override_prices=_can(session, current_user, "order_items", "edit"),
        can_discount=_can(session, current_user, "invoices", "edit"),
        can_collect_payment=_can(session, current_user, "payments", "collect"),
    )
    return order_service.get_order_detail(session=session, order_id=order.id)


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("orders", "view"))],
    response_model=OrderDetailPublic,
)
def read_order(session: SessionDep, id: uuid.UUID) -> Any:
    return order_service.get_order_detail(session=session, order_id=id)


@router.post(
    "/{id}/preview",
    dependencies=[Depends(require_permission("orders", "edit"))],
    response_model=OrderPreviewPublic,
)
def preview_order_update(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    request_in: OrderPreviewRequest,
) -> Any:
    return order_service.preview_order_update(
        session=session,
        order_id=id,
        request=request_in,
        can_override_prices=_can(session, current_user, "order_items", "edit"),
        can_discount=_can(session, current_user, "invoices", "edit"),
    )


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("orders", "edit"))],
    response_model=OrderDetailPublic,
)
def update_order(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    order_in: OrderUpdate,
) -> Any:
    return order_service.update_order(
        session=session,
        order_id=id,
        request=order_in,
        performed_by_id=current_user.id,
        can_override_prices=_can(session, current_user, "order_items", "edit"),
        can_discount=_can(session, current_user, "invoices", "edit"),
    )


@router.get(
    "/{id}/revisions",
    dependencies=[Depends(require_permission("audit", "view"))],
    response_model=OrderRevisionsPublic,
)
def read_order_revisions(session: SessionDep, id: uuid.UUID) -> Any:
    return order_service.get_order_revisions(session=session, order_id=id)


@invoice_router.post(
    "/{id}/payments",
    dependencies=[Depends(require_permission("payments", "collect"))],
    response_model=PaymentTransactionPublic,
)
def collect_invoice_payment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    payment_in: PaymentCollect,
) -> Any:
    return order_service.collect_payment(
        session=session,
        invoice_id=id,
        payment_in=payment_in,
        collected_by_id=current_user.id,
    )
