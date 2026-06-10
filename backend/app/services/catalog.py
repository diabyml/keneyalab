"""Catalog business logic - tests, panels, analytes, and specimens."""

import uuid
from decimal import Decimal

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.lis import (
    Analyte,
    Catalog,
    CatalogCreate,
    CatalogDetailPublic,
    CatalogItemAnalyte,
    CatalogItemAnalyteCreate,
    CatalogItemAnalyteDetailPublic,
    CatalogPanelItem,
    CatalogPanelItemCreate,
    CatalogPanelItemDetailPublic,
    CatalogRelationshipReorderRequest,
    CatalogSpecimenRequirement,
    CatalogSpecimenRequirementDetailPublic,
    CatalogSpecimenRequirementUpsert,
    CatalogSummaryPublic,
    CatalogType,
    CatalogUpdate,
    Category,
    SortOrder,
    SpecimenType,
)
from app.repositories import catalog as catalog_repo


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_payload(data: dict) -> dict:
    if "code" in data and data["code"] is not None:
        data["code"] = data["code"].strip().upper()
        if not data["code"]:
            raise BusinessRuleError("Le code catalogue est requis")

    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
        if not data["name"]:
            raise BusinessRuleError("Le nom catalogue est requis")

    if "price" in data and data["price"] is not None and data["price"] < Decimal("0"):
        raise BusinessRuleError("Le prix doit être positif")

    return data


def _ensure_panel_price_is_computed(data: dict) -> None:
    price = data.get("price")
    if price is not None and price != Decimal("0"):
        raise BusinessRuleError("Le prix d'un panel est calculé à partir de ses tests")


def _ensure_unique_code(
    *, session: Session, code: str, exclude_id: uuid.UUID | None = None
) -> None:
    existing = catalog_repo.get_by_code(session=session, code=code)
    if existing is not None and existing.id != exclude_id:
        raise ConflictError("Code catalogue déjà utilisé")


def _ensure_category_active(*, session: Session, category_id: uuid.UUID | None) -> None:
    if category_id is None:
        return
    category = session.get(Category, category_id)
    if category is None or category.is_deleted:
        raise BusinessRuleError("Catégorie non disponible")


def _get_catalog(*, session: Session, catalog_id: uuid.UUID) -> Catalog:
    db_catalog = catalog_repo.get_by_id(session=session, catalog_id=catalog_id)
    if db_catalog is None:
        raise NotFoundError("Entrée catalogue non trouvée")
    return db_catalog


def _ensure_catalog_type(db_catalog: Catalog, expected_type: CatalogType) -> None:
    if db_catalog.type != expected_type:
        if expected_type == CatalogType.item:
            raise BusinessRuleError("Cette action est réservée aux tests catalogue")
        raise BusinessRuleError("Cette action est réservée aux panels catalogue")


def _ensure_analyte_active(*, session: Session, analyte_id: uuid.UUID) -> Analyte:
    analyte = session.get(Analyte, analyte_id)
    if analyte is None or analyte.is_deleted:
        raise BusinessRuleError("Analyte non disponible")
    return analyte


def _ensure_specimen_type_active(
    *, session: Session, specimen_type_id: uuid.UUID
) -> SpecimenType:
    specimen_type = session.get(SpecimenType, specimen_type_id)
    if specimen_type is None or specimen_type.is_deleted:
        raise BusinessRuleError("Type de prélèvement non disponible")
    return specimen_type


def _ensure_panel_test_active(*, session: Session, test_id: uuid.UUID) -> Catalog:
    test = _get_catalog(session=session, catalog_id=test_id)
    if test.is_deleted or test.type != CatalogType.item:
        raise BusinessRuleError("Seuls les tests actifs peuvent être ajoutés au panel")
    return test


def _effective_catalog_price(*, session: Session, db_catalog: Catalog) -> Decimal:
    if db_catalog.type == CatalogType.panel:
        return Decimal(
            catalog_repo.sum_panel_item_prices(session=session, panel_id=db_catalog.id)
        ).quantize(Decimal("0.01"))
    return db_catalog.price


def _summary_for_catalog(
    *, session: Session, db_catalog: Catalog
) -> CatalogSummaryPublic:
    return CatalogSummaryPublic(
        id=db_catalog.id,
        is_deleted=db_catalog.is_deleted,
        created_at=db_catalog.created_at,
        updated_at=db_catalog.updated_at,
        type=db_catalog.type,
        name=db_catalog.name,
        code=db_catalog.code,
        price=_effective_catalog_price(session=session, db_catalog=db_catalog),
        is_orderable=db_catalog.is_orderable,
        category_id=db_catalog.category_id,
        category_name=catalog_repo.get_category_name(
            session=session, category_id=db_catalog.category_id
        ),
        analytes_count=catalog_repo.count_analytes(
            session=session, catalog_id=db_catalog.id
        ),
        specimen_requirements_count=catalog_repo.count_specimen_requirements(
            session=session, catalog_id=db_catalog.id
        ),
        panel_items_count=catalog_repo.count_panel_items(
            session=session, catalog_id=db_catalog.id
        ),
    )


def detail_for_catalog(*, session: Session, db_catalog: Catalog) -> CatalogDetailPublic:
    summary = _summary_for_catalog(session=session, db_catalog=db_catalog)
    analytes = [
        CatalogItemAnalyteDetailPublic(
            **attachment.model_dump(),
            analyte_code=analyte.code,
            analyte_name=analyte.name,
            analyte_data_type=analyte.data_type,
            unit_name=unit.name if unit else None,
        )
        for attachment, analyte, unit in catalog_repo.get_item_analytes(
            session=session, catalog_item_id=db_catalog.id
        )
    ]
    specimen_requirements = [
        CatalogSpecimenRequirementDetailPublic(
            **requirement.model_dump(),
            specimen_type_name=specimen_type.name,
            specimen_type_color=specimen_type.color,
        )
        for requirement, specimen_type in catalog_repo.get_specimen_requirements(
            session=session, catalog_id=db_catalog.id
        )
    ]
    panel_items = [
        CatalogPanelItemDetailPublic(
            **panel_item.model_dump(),
            test_code=test.code,
            test_name=test.name,
            test_price=test.price,
        )
        for panel_item, test in catalog_repo.get_panel_items(
            session=session, panel_id=db_catalog.id
        )
    ]
    return CatalogDetailPublic(
        **summary.model_dump(),
        analytes=analytes,
        specimen_requirements=specimen_requirements,
        panel_items=panel_items,
    )


def create_catalog(*, session: Session, catalog_in: CatalogCreate) -> Catalog:
    data = _validate_payload(catalog_in.model_dump())
    if data["type"] == CatalogType.panel:
        _ensure_panel_price_is_computed(data)
        data["price"] = Decimal("0.00")
    _ensure_unique_code(session=session, code=data["code"])
    _ensure_category_active(session=session, category_id=data.get("category_id"))
    db_catalog = Catalog.model_validate(data)
    catalog_repo.create(session=session, db_obj=db_catalog)
    session.commit()
    session.refresh(db_catalog)
    return db_catalog


def get_catalogs(
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
) -> tuple[list[CatalogSummaryPublic], int]:
    items, count = catalog_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=_clean_text(search),
        type=type,
        category_id=category_id,
        is_orderable=is_orderable,
        exclude_empty_panels=exclude_empty_panels,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return [
        _summary_for_catalog(session=session, db_catalog=item) for item in items
    ], count


def get_catalog(*, session: Session, catalog_id: uuid.UUID) -> CatalogDetailPublic:
    return detail_for_catalog(
        session=session, db_catalog=_get_catalog(session=session, catalog_id=catalog_id)
    )


def update_catalog(
    *, session: Session, catalog_id: uuid.UUID, catalog_in: CatalogUpdate
) -> Catalog:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    update_data = _validate_payload(catalog_in.model_dump(exclude_unset=True))

    if "type" in update_data and update_data["type"] != db_catalog.type:
        raise BusinessRuleError("Le type catalogue ne peut pas être modifié")
    update_data.pop("type", None)

    if db_catalog.type == CatalogType.panel:
        _ensure_panel_price_is_computed(update_data)
        update_data.pop("price", None)

    if "code" in update_data:
        _ensure_unique_code(
            session=session, code=update_data["code"], exclude_id=db_catalog.id
        )
    if "category_id" in update_data:
        _ensure_category_active(session=session, category_id=update_data["category_id"])

    catalog_repo.update(session=session, db_catalog=db_catalog, update_data=update_data)
    session.commit()
    session.refresh(db_catalog)
    return db_catalog


def delete_catalog(*, session: Session, catalog_id: uuid.UUID) -> None:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    catalog_repo.soft_delete(session=session, db_catalog=db_catalog)
    session.commit()


def restore_catalog(*, session: Session, catalog_id: uuid.UUID) -> Catalog:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    catalog_repo.update(
        session=session, db_catalog=db_catalog, update_data={"is_deleted": False}
    )
    session.commit()
    session.refresh(db_catalog)
    return db_catalog


def add_item_analyte(
    *, session: Session, catalog_id: uuid.UUID, attachment_in: CatalogItemAnalyteCreate
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.item)
    _ensure_analyte_active(session=session, analyte_id=attachment_in.analyte_id)
    if catalog_repo.get_item_analyte(
        session=session, catalog_item_id=catalog_id, analyte_id=attachment_in.analyte_id
    ):
        raise ConflictError("Analyte déjà attaché à ce test")

    catalog_repo.create_item_analyte(
        session=session,
        db_obj=CatalogItemAnalyte(
            catalog_item_id=catalog_id,
            analyte_id=attachment_in.analyte_id,
            sort_order=attachment_in.sort_order,
        ),
    )
    session.commit()
    session.refresh(db_catalog)
    return detail_for_catalog(session=session, db_catalog=db_catalog)


def reorder_item_analytes(
    *,
    session: Session,
    catalog_id: uuid.UUID,
    reorder_in: CatalogRelationshipReorderRequest,
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.item)
    for item in sorted(reorder_in.items, key=lambda value: value.sort_order):
        attachment = catalog_repo.get_item_analyte_by_id(
            session=session, attachment_id=item.id
        )
        if attachment is None or attachment.catalog_item_id != catalog_id:
            raise NotFoundError("Attachement analyte non trouvé")
        attachment.sort_order = item.sort_order
        session.add(attachment)
    session.commit()
    return detail_for_catalog(session=session, db_catalog=db_catalog)


def remove_item_analyte(
    *, session: Session, catalog_id: uuid.UUID, attachment_id: uuid.UUID
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.item)
    attachment = catalog_repo.get_item_analyte_by_id(
        session=session, attachment_id=attachment_id
    )
    if attachment is None or attachment.catalog_item_id != catalog_id:
        raise NotFoundError("Attachement analyte non trouvé")
    catalog_repo.delete_obj(session=session, db_obj=attachment)
    session.commit()
    return detail_for_catalog(session=session, db_catalog=db_catalog)


def upsert_specimen_requirement(
    *,
    session: Session,
    catalog_id: uuid.UUID,
    specimen_type_id: uuid.UUID,
    requirement_in: CatalogSpecimenRequirementUpsert,
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.item)
    _ensure_specimen_type_active(session=session, specimen_type_id=specimen_type_id)
    data = requirement_in.model_dump()
    if data.get("volume_ml") is not None and data["volume_ml"] < Decimal("0"):
        raise BusinessRuleError("Le volume doit être positif")
    existing = catalog_repo.get_specimen_requirement(
        session=session, catalog_id=catalog_id, specimen_type_id=specimen_type_id
    )
    if existing is None:
        existing = CatalogSpecimenRequirement(
            catalog_id=catalog_id,
            specimen_type_id=specimen_type_id,
            volume_ml=data.get("volume_ml"),
            instructions=_clean_text(data.get("instructions")),
        )
    else:
        existing.volume_ml = data.get("volume_ml")
        existing.instructions = _clean_text(data.get("instructions"))
    catalog_repo.upsert_specimen_requirement(session=session, db_obj=existing)
    session.commit()
    return detail_for_catalog(session=session, db_catalog=db_catalog)


def remove_specimen_requirement(
    *, session: Session, catalog_id: uuid.UUID, specimen_type_id: uuid.UUID
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.item)
    requirement = catalog_repo.get_specimen_requirement(
        session=session, catalog_id=catalog_id, specimen_type_id=specimen_type_id
    )
    if requirement is None:
        raise NotFoundError("Exigence de prélèvement non trouvée")
    catalog_repo.delete_obj(session=session, db_obj=requirement)
    session.commit()
    return detail_for_catalog(session=session, db_catalog=db_catalog)


def add_panel_item(
    *, session: Session, catalog_id: uuid.UUID, panel_item_in: CatalogPanelItemCreate
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.panel)
    _ensure_panel_test_active(session=session, test_id=panel_item_in.test_id)
    if catalog_repo.get_panel_item(
        session=session, panel_id=catalog_id, test_id=panel_item_in.test_id
    ):
        raise ConflictError("Test déjà ajouté à ce panel")
    catalog_repo.create_panel_item(
        session=session,
        db_obj=CatalogPanelItem(
            panel_id=catalog_id,
            test_id=panel_item_in.test_id,
            sort_order=panel_item_in.sort_order,
        ),
    )
    session.commit()
    return detail_for_catalog(session=session, db_catalog=db_catalog)


def reorder_panel_items(
    *,
    session: Session,
    catalog_id: uuid.UUID,
    reorder_in: CatalogRelationshipReorderRequest,
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.panel)
    for item in sorted(reorder_in.items, key=lambda value: value.sort_order):
        panel_item = catalog_repo.get_panel_item_by_id(
            session=session, panel_item_id=item.id
        )
        if panel_item is None or panel_item.panel_id != catalog_id:
            raise NotFoundError("Test du panel non trouvé")
        panel_item.sort_order = item.sort_order
        session.add(panel_item)
    session.commit()
    return detail_for_catalog(session=session, db_catalog=db_catalog)


def remove_panel_item(
    *, session: Session, catalog_id: uuid.UUID, panel_item_id: uuid.UUID
) -> CatalogDetailPublic:
    db_catalog = _get_catalog(session=session, catalog_id=catalog_id)
    _ensure_catalog_type(db_catalog, CatalogType.panel)
    panel_item = catalog_repo.get_panel_item_by_id(
        session=session, panel_item_id=panel_item_id
    )
    if panel_item is None or panel_item.panel_id != catalog_id:
        raise NotFoundError("Test du panel non trouvé")
    catalog_repo.delete_obj(session=session, db_obj=panel_item)
    session.commit()
    return detail_for_catalog(session=session, db_catalog=db_catalog)
