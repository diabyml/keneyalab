"""InsurancePricing repository - pure database access only."""

import uuid
from decimal import Decimal

from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    Catalog,
    CatalogType,
    InsurancePricing,
    InsuranceProvider,
    SortOrder,
)

SORT_COLUMNS = {
    "provider_name": InsuranceProvider.name,
    "catalog_code": Catalog.code,
    "catalog_name": Catalog.name,
    "catalog_price": Catalog.price,
    "insurance_price": InsurancePricing.insurance_price,
    "created_at": InsurancePricing.created_at,
    "updated_at": InsurancePricing.updated_at,
}


def get_by_id(
    *, session: Session, pricing_id: uuid.UUID
) -> InsurancePricing | None:
    return session.get(InsurancePricing, pricing_id)


def get_by_provider_and_catalog(
    *, session: Session, provider_id: uuid.UUID, catalog_id: uuid.UUID
) -> InsurancePricing | None:
    statement = select(InsurancePricing).where(
        InsurancePricing.insurance_provider_id == provider_id,
        InsurancePricing.catalog_id == catalog_id,
    )
    return session.exec(statement).first()


def get_all(
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
) -> tuple[list[tuple[InsurancePricing, InsuranceProvider, Catalog]], int]:
    conditions = [Catalog.type == CatalogType.item]
    if insurance_provider_id is not None:
        conditions.append(
            InsurancePricing.insurance_provider_id == insurance_provider_id
        )
    if catalog_id is not None:
        conditions.append(InsurancePricing.catalog_id == catalog_id)
    if min_price is not None:
        conditions.append(InsurancePricing.insurance_price >= min_price)
    if max_price is not None:
        conditions.append(InsurancePricing.insurance_price <= max_price)
    if search:
        q = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(InsuranceProvider.name).ilike(q),
                col(Catalog.code).ilike(q),
                col(Catalog.name).ilike(q),
            )
        )

    base_query = (
        select(InsurancePricing, InsuranceProvider, Catalog)
        .join(
            InsuranceProvider,
            InsurancePricing.insurance_provider_id == InsuranceProvider.id,
        )
        .join(Catalog, InsurancePricing.catalog_id == Catalog.id)
    )
    count_statement = (
        select(func.count())
        .select_from(InsurancePricing)
        .join(
            InsuranceProvider,
            InsurancePricing.insurance_provider_id == InsuranceProvider.id,
        )
        .join(Catalog, InsurancePricing.catalog_id == Catalog.id)
    )
    if conditions:
        base_query = base_query.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()
    sort_column = SORT_COLUMNS.get(sort_by or "provider_name", InsuranceProvider.name)
    order_expr = (
        col(sort_column).desc()
        if sort_order == SortOrder.desc
        else col(sort_column).asc()
    )
    statement = (
        base_query.order_by(order_expr, col(Catalog.code).asc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all()), count


def create(
    *, session: Session, db_obj: InsurancePricing
) -> InsurancePricing:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(
    *, session: Session, db_obj: InsurancePricing, update_data: dict
) -> InsurancePricing:
    db_obj.sqlmodel_update(update_data)
    session.add(db_obj)
    return db_obj


def delete(*, session: Session, db_obj: InsurancePricing) -> None:
    session.delete(db_obj)
