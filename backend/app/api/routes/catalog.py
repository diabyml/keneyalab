import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_any_permission, require_permission
from app.models import (
    CatalogCreate,
    CatalogDetailPublic,
    CatalogItemAnalyteCreate,
    CatalogPanelItemCreate,
    CatalogRelationshipReorderRequest,
    CatalogSpecimenRequirementUpsert,
    CatalogSummariesPublic,
    CatalogSummaryPublic,
    CatalogType,
    CatalogUpdate,
    Message,
    SortOrder,
)
from app.services import catalog as catalog_service

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get(
    "/",
    dependencies=[
        Depends(
            require_any_permission(
                ("catalog", "manage"),
                ("finance", "manage"),
            )
        )
    ],
    response_model=CatalogSummariesPublic,
)
def read_catalog(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    type: CatalogType | None = None,
    category_id: uuid.UUID | None = None,
    is_orderable: bool | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> Any:
    """Retrieve catalog entries with server-side search, filters, and sorting."""
    items, count = catalog_service.get_catalogs(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        type=type,
        category_id=category_id,
        is_orderable=is_orderable,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return CatalogSummariesPublic(data=items, count=count)


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def read_catalog_entry(session: SessionDep, id: uuid.UUID) -> Any:
    """Get a catalog entry with analytes, specimen requirements, and panel items."""
    return catalog_service.get_catalog(session=session, catalog_id=id)


@router.post(
    "/",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogSummaryPublic,
)
def create_catalog(*, session: SessionDep, catalog_in: CatalogCreate) -> Any:
    """Create a test or panel catalog entry."""
    item = catalog_service.create_catalog(session=session, catalog_in=catalog_in)
    return catalog_service.get_catalog(session=session, catalog_id=item.id)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogSummaryPublic,
)
def update_catalog(
    *, session: SessionDep, id: uuid.UUID, catalog_in: CatalogUpdate
) -> Any:
    """Update catalog metadata."""
    item = catalog_service.update_catalog(
        session=session, catalog_id=id, catalog_in=catalog_in
    )
    return catalog_service.get_catalog(session=session, catalog_id=item.id)


@router.delete(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
)
def delete_catalog(session: SessionDep, id: uuid.UUID) -> Message:
    """Soft-delete a catalog entry."""
    catalog_service.delete_catalog(session=session, catalog_id=id)
    return Message(message="Entrée catalogue supprimée avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogSummaryPublic,
)
def restore_catalog(session: SessionDep, id: uuid.UUID) -> Any:
    """Restore a soft-deleted catalog entry."""
    item = catalog_service.restore_catalog(session=session, catalog_id=id)
    return catalog_service.get_catalog(session=session, catalog_id=item.id)


@router.post(
    "/{id}/analytes",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def add_catalog_analyte(
    *, session: SessionDep, id: uuid.UUID, attachment_in: CatalogItemAnalyteCreate
) -> Any:
    """Attach an analyte to a catalog test."""
    return catalog_service.add_item_analyte(
        session=session, catalog_id=id, attachment_in=attachment_in
    )


@router.put(
    "/{id}/analytes/reorder",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def reorder_catalog_analytes(
    *, session: SessionDep, id: uuid.UUID, reorder_in: CatalogRelationshipReorderRequest
) -> Any:
    """Persist analyte attachment order for a catalog test."""
    return catalog_service.reorder_item_analytes(
        session=session, catalog_id=id, reorder_in=reorder_in
    )


@router.delete(
    "/{id}/analytes/{attachment_id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def remove_catalog_analyte(
    *, session: SessionDep, id: uuid.UUID, attachment_id: uuid.UUID
) -> Any:
    """Remove an analyte attachment from a catalog test."""
    return catalog_service.remove_item_analyte(
        session=session, catalog_id=id, attachment_id=attachment_id
    )


@router.put(
    "/{id}/specimen-requirements/{specimen_type_id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def upsert_catalog_specimen_requirement(
    *,
    session: SessionDep,
    id: uuid.UUID,
    specimen_type_id: uuid.UUID,
    requirement_in: CatalogSpecimenRequirementUpsert,
) -> Any:
    """Create or update a specimen requirement for a catalog test."""
    return catalog_service.upsert_specimen_requirement(
        session=session,
        catalog_id=id,
        specimen_type_id=specimen_type_id,
        requirement_in=requirement_in,
    )


@router.delete(
    "/{id}/specimen-requirements/{specimen_type_id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def remove_catalog_specimen_requirement(
    *, session: SessionDep, id: uuid.UUID, specimen_type_id: uuid.UUID
) -> Any:
    """Remove a specimen requirement from a catalog test."""
    return catalog_service.remove_specimen_requirement(
        session=session, catalog_id=id, specimen_type_id=specimen_type_id
    )


@router.post(
    "/{id}/panel-items",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def add_catalog_panel_item(
    *, session: SessionDep, id: uuid.UUID, panel_item_in: CatalogPanelItemCreate
) -> Any:
    """Attach a test to a catalog panel."""
    return catalog_service.add_panel_item(
        session=session, catalog_id=id, panel_item_in=panel_item_in
    )


@router.put(
    "/{id}/panel-items/reorder",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def reorder_catalog_panel_items(
    *, session: SessionDep, id: uuid.UUID, reorder_in: CatalogRelationshipReorderRequest
) -> Any:
    """Persist test order for a catalog panel."""
    return catalog_service.reorder_panel_items(
        session=session, catalog_id=id, reorder_in=reorder_in
    )


@router.delete(
    "/{id}/panel-items/{panel_item_id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CatalogDetailPublic,
)
def remove_catalog_panel_item(
    *, session: SessionDep, id: uuid.UUID, panel_item_id: uuid.UUID
) -> Any:
    """Remove a test from a catalog panel."""
    return catalog_service.remove_panel_item(
        session=session, catalog_id=id, panel_item_id=panel_item_id
    )
