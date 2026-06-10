"""Catalog repository - pure database access only."""

import uuid

from sqlalchemy import case, exists
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, func, or_, select

from app.models.lis import (
    Analyte,
    Catalog,
    CatalogItemAnalyte,
    CatalogPanelItem,
    CatalogSpecimenRequirement,
    CatalogType,
    Category,
    SortOrder,
    SpecimenType,
    Unit,
)

SORT_COLUMNS = {
    "code": Catalog.code,
    "name": Catalog.name,
    "type": Catalog.type,
    "is_orderable": Catalog.is_orderable,
    "created_at": Catalog.created_at,
    "updated_at": Catalog.updated_at,
}


def effective_price_expression():
    panel_test = aliased(Catalog)
    panel_total = (
        select(func.coalesce(func.sum(panel_test.price), 0))
        .select_from(CatalogPanelItem)
        .join(panel_test, CatalogPanelItem.test_id == panel_test.id)
        .where(CatalogPanelItem.panel_id == Catalog.id)
        .correlate(Catalog)
        .scalar_subquery()
    )
    return case(
        (Catalog.type == CatalogType.panel, panel_total),
        else_=Catalog.price,
    )


def get_by_id(*, session: Session, catalog_id: uuid.UUID) -> Catalog | None:
    return session.get(Catalog, catalog_id)


def get_by_code(*, session: Session, code: str) -> Catalog | None:
    statement = select(Catalog).where(Catalog.code == code)
    return session.exec(statement).first()


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    type: CatalogType | None = None,
    category_id: uuid.UUID | None = None,
    is_orderable: bool | None = None,
    exclude_empty_panels: bool = False,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> tuple[list[Catalog], int]:
    conditions = []
    if is_deleted is not None:
        conditions.append(Catalog.is_deleted == is_deleted)
    elif not include_deleted:
        conditions.append(col(Catalog.is_deleted).is_(False))
    if search:
        q = f"%{search.strip()}%"
        conditions.append(or_(col(Catalog.code).ilike(q), col(Catalog.name).ilike(q)))
    if type is not None:
        conditions.append(Catalog.type == type)
    if category_id is not None:
        conditions.append(Catalog.category_id == category_id)
    if is_orderable is not None:
        conditions.append(Catalog.is_orderable == is_orderable)
    if exclude_empty_panels:
        conditions.append(
            (Catalog.type != CatalogType.panel)
            | exists(
                select(CatalogPanelItem.id).where(
                    CatalogPanelItem.panel_id == Catalog.id
                )
            )
        )

    base_query = select(Catalog)
    count_statement = select(func.count()).select_from(Catalog)
    if conditions:
        base_query = base_query.where(*conditions)
        count_statement = count_statement.where(*conditions)

    count = session.exec(count_statement).one()

    if sort_by == "price":
        sort_column = effective_price_expression()
        order_expr = (
            sort_column.desc() if sort_order == SortOrder.desc else sort_column.asc()
        )
    else:
        sort_column = SORT_COLUMNS.get(sort_by or "code", Catalog.code)
        order_expr = (
            col(sort_column).desc()
            if sort_order == SortOrder.desc
            else col(sort_column).asc()
        )
    statement = (
        base_query.order_by(order_expr, col(Catalog.name).asc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return list(items), count


def create(*, session: Session, db_obj: Catalog) -> Catalog:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_catalog: Catalog, update_data: dict) -> Catalog:
    db_catalog.sqlmodel_update(update_data)
    session.add(db_catalog)
    return db_catalog


def soft_delete(*, session: Session, db_catalog: Catalog) -> None:
    db_catalog.is_deleted = True
    session.add(db_catalog)


def count_analytes(*, session: Session, catalog_id: uuid.UUID) -> int:
    statement = (
        select(func.count())
        .select_from(CatalogItemAnalyte)
        .where(CatalogItemAnalyte.catalog_item_id == catalog_id)
    )
    return session.exec(statement).one()


def count_specimen_requirements(*, session: Session, catalog_id: uuid.UUID) -> int:
    statement = (
        select(func.count())
        .select_from(CatalogSpecimenRequirement)
        .where(CatalogSpecimenRequirement.catalog_id == catalog_id)
    )
    return session.exec(statement).one()


def count_panel_items(*, session: Session, catalog_id: uuid.UUID) -> int:
    statement = (
        select(func.count())
        .select_from(CatalogPanelItem)
        .where(CatalogPanelItem.panel_id == catalog_id)
    )
    return session.exec(statement).one()


def sum_panel_item_prices(*, session: Session, panel_id: uuid.UUID):
    test = aliased(Catalog)
    statement = (
        select(func.coalesce(func.sum(test.price), 0))
        .select_from(CatalogPanelItem)
        .join(test, CatalogPanelItem.test_id == test.id)
        .where(CatalogPanelItem.panel_id == panel_id)
    )
    return session.exec(statement).one()


def get_category_name(*, session: Session, category_id: uuid.UUID | None) -> str | None:
    if category_id is None:
        return None
    category = session.get(Category, category_id)
    return category.name if category else None


def get_item_analytes(
    *, session: Session, catalog_item_id: uuid.UUID
) -> list[tuple[CatalogItemAnalyte, Analyte, Unit | None]]:
    statement = (
        select(CatalogItemAnalyte, Analyte, Unit)
        .join(Analyte, CatalogItemAnalyte.analyte_id == Analyte.id)
        .join(Unit, Analyte.unit_id == Unit.id, isouter=True)
        .where(CatalogItemAnalyte.catalog_item_id == catalog_item_id)
        .order_by(col(CatalogItemAnalyte.sort_order).asc(), col(Analyte.code).asc())
    )
    return list(session.exec(statement).all())


def get_specimen_requirements(
    *, session: Session, catalog_id: uuid.UUID
) -> list[tuple[CatalogSpecimenRequirement, SpecimenType]]:
    statement = (
        select(CatalogSpecimenRequirement, SpecimenType)
        .join(
            SpecimenType, CatalogSpecimenRequirement.specimen_type_id == SpecimenType.id
        )
        .where(CatalogSpecimenRequirement.catalog_id == catalog_id)
        .order_by(col(SpecimenType.name).asc())
    )
    return list(session.exec(statement).all())


def get_panel_items(
    *, session: Session, panel_id: uuid.UUID
) -> list[tuple[CatalogPanelItem, Catalog]]:
    statement = (
        select(CatalogPanelItem, Catalog)
        .join(Catalog, CatalogPanelItem.test_id == Catalog.id)
        .where(CatalogPanelItem.panel_id == panel_id)
        .order_by(col(CatalogPanelItem.sort_order).asc(), col(Catalog.code).asc())
    )
    return list(session.exec(statement).all())


def get_item_analyte_by_id(
    *, session: Session, attachment_id: uuid.UUID
) -> CatalogItemAnalyte | None:
    return session.get(CatalogItemAnalyte, attachment_id)


def get_item_analyte(
    *, session: Session, catalog_item_id: uuid.UUID, analyte_id: uuid.UUID
) -> CatalogItemAnalyte | None:
    statement = select(CatalogItemAnalyte).where(
        CatalogItemAnalyte.catalog_item_id == catalog_item_id,
        CatalogItemAnalyte.analyte_id == analyte_id,
    )
    return session.exec(statement).first()


def create_item_analyte(
    *, session: Session, db_obj: CatalogItemAnalyte
) -> CatalogItemAnalyte:
    session.add(db_obj)
    session.flush()
    return db_obj


def get_specimen_requirement(
    *, session: Session, catalog_id: uuid.UUID, specimen_type_id: uuid.UUID
) -> CatalogSpecimenRequirement | None:
    return session.get(CatalogSpecimenRequirement, (catalog_id, specimen_type_id))


def upsert_specimen_requirement(
    *, session: Session, db_obj: CatalogSpecimenRequirement
) -> CatalogSpecimenRequirement:
    session.add(db_obj)
    session.flush()
    return db_obj


def get_panel_item_by_id(
    *, session: Session, panel_item_id: uuid.UUID
) -> CatalogPanelItem | None:
    return session.get(CatalogPanelItem, panel_item_id)


def get_panel_item(
    *, session: Session, panel_id: uuid.UUID, test_id: uuid.UUID
) -> CatalogPanelItem | None:
    statement = select(CatalogPanelItem).where(
        CatalogPanelItem.panel_id == panel_id,
        CatalogPanelItem.test_id == test_id,
    )
    return session.exec(statement).first()


def create_panel_item(
    *, session: Session, db_obj: CatalogPanelItem
) -> CatalogPanelItem:
    session.add(db_obj)
    session.flush()
    return db_obj


def delete_obj(*, session: Session, db_obj: object) -> None:
    session.delete(db_obj)
