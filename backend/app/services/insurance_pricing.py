"""InsurancePricing business logic."""

import uuid
from decimal import Decimal

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    Catalog,
    CatalogType,
    InsurancePricing,
    InsurancePricingCreate,
    InsurancePricingDetailPublic,
    InsurancePricingUpdate,
    InsuranceProvider,
    SortOrder,
)
from app.repositories import insurance_pricing as pricing_repo


def _pricing_detail(
    pricing: InsurancePricing, provider: InsuranceProvider, catalog: Catalog
) -> InsurancePricingDetailPublic:
    return InsurancePricingDetailPublic(
        **pricing.model_dump(),
        insurance_provider_name=provider.name,
        catalog_code=catalog.code,
        catalog_name=catalog.name,
        catalog_price=catalog.price,
    )


def _ensure_price_valid(value: Decimal | None) -> None:
    if value is not None and value < Decimal("0"):
        raise BusinessRuleError("Le prix assurance doit être positif")


def _ensure_provider_active(
    *, session: Session, provider_id: uuid.UUID
) -> InsuranceProvider:
    provider = session.get(InsuranceProvider, provider_id)
    if provider is None or provider.is_deleted:
        raise BusinessRuleError("Assureur non disponible")
    return provider


def _ensure_catalog_test_active(*, session: Session, catalog_id: uuid.UUID) -> Catalog:
    catalog = session.get(Catalog, catalog_id)
    if catalog is None or catalog.is_deleted or catalog.type != CatalogType.item:
        raise BusinessRuleError("Test catalogue non disponible")
    return catalog


def _get_pricing(*, session: Session, pricing_id: uuid.UUID) -> InsurancePricing:
    pricing = pricing_repo.get_by_id(session=session, pricing_id=pricing_id)
    if pricing is None:
        raise NotFoundError("Tarif assurance non trouvé")
    return pricing


def get_insurance_pricings(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    insurance_provider_id: uuid.UUID | None = None,
    catalog_id: uuid.UUID | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[InsurancePricingDetailPublic], int]:
    rows, count = pricing_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        search=search.strip() if search else None,
        insurance_provider_id=insurance_provider_id,
        catalog_id=catalog_id,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return [_pricing_detail(*row) for row in rows], count


def create_insurance_pricing(
    *, session: Session, pricing_in: InsurancePricingCreate
) -> InsurancePricingDetailPublic:
    _ensure_price_valid(pricing_in.insurance_price)
    provider = _ensure_provider_active(
        session=session, provider_id=pricing_in.insurance_provider_id
    )
    catalog = _ensure_catalog_test_active(
        session=session, catalog_id=pricing_in.catalog_id
    )
    existing = pricing_repo.get_by_provider_and_catalog(
        session=session,
        provider_id=pricing_in.insurance_provider_id,
        catalog_id=pricing_in.catalog_id,
    )
    if existing is not None:
        raise ConflictError("Un tarif existe déjà pour cet assureur et ce test")

    db_obj = InsurancePricing.model_validate(pricing_in)
    pricing_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return _pricing_detail(db_obj, provider, catalog)


def update_insurance_pricing(
    *,
    session: Session,
    pricing_id: uuid.UUID,
    pricing_in: InsurancePricingUpdate,
) -> InsurancePricingDetailPublic:
    db_obj = _get_pricing(session=session, pricing_id=pricing_id)
    update_data = pricing_in.model_dump(exclude_unset=True)
    _ensure_price_valid(update_data.get("insurance_price"))
    pricing_repo.update(session=session, db_obj=db_obj, update_data=update_data)
    session.commit()
    session.refresh(db_obj)
    provider = session.get(InsuranceProvider, db_obj.insurance_provider_id)
    catalog = session.get(Catalog, db_obj.catalog_id)
    if provider is None or catalog is None:
        raise NotFoundError("Tarif assurance non trouvé")
    return _pricing_detail(db_obj, provider, catalog)


def delete_insurance_pricing(*, session: Session, pricing_id: uuid.UUID) -> None:
    db_obj = _get_pricing(session=session, pricing_id=pricing_id)
    pricing_repo.delete(session=session, db_obj=db_obj)
    session.commit()
