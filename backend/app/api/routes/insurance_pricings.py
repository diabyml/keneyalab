import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_permission
from app.models import (
    InsurancePricingCreate,
    InsurancePricingDetailPublic,
    InsurancePricingsPublic,
    InsurancePricingUpdate,
    Message,
    SortOrder,
)
from app.services import insurance_pricing as pricing_service

router = APIRouter(prefix="/insurance-pricings", tags=["insurance-pricings"])


@router.get(
    "/",
    dependencies=[Depends(require_permission("finance", "manage"))],
    response_model=InsurancePricingsPublic,
)
def read_insurance_pricings(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    insurance_provider_id: uuid.UUID | None = None,
    catalog_id: uuid.UUID | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> Any:
    items, count = pricing_service.get_insurance_pricings(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        insurance_provider_id=insurance_provider_id,
        catalog_id=catalog_id,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return InsurancePricingsPublic(data=items, count=count)


@router.post(
    "/",
    dependencies=[Depends(require_permission("finance", "manage"))],
    response_model=InsurancePricingDetailPublic,
)
def create_insurance_pricing(
    *, session: SessionDep, pricing_in: InsurancePricingCreate
) -> Any:
    return pricing_service.create_insurance_pricing(
        session=session, pricing_in=pricing_in
    )


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("finance", "manage"))],
    response_model=InsurancePricingDetailPublic,
)
def update_insurance_pricing(
    *, session: SessionDep, id: uuid.UUID, pricing_in: InsurancePricingUpdate
) -> Any:
    return pricing_service.update_insurance_pricing(
        session=session, pricing_id=id, pricing_in=pricing_in
    )


@router.delete(
    "/{id}", dependencies=[Depends(require_permission("finance", "manage"))]
)
def delete_insurance_pricing(session: SessionDep, id: uuid.UUID) -> Message:
    pricing_service.delete_insurance_pricing(session=session, pricing_id=id)
    return Message(message="Tarif assurance supprimé avec succès")
