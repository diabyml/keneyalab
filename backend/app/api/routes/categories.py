import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_any_permission, require_permission
from app.models import (
    CategoriesPublic,
    CategoryCreate,
    CategoryPublic,
    CategoryReorderRequest,
    CategoryUpdate,
    Message,
)
from app.services import category as category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "/",
    dependencies=[
        Depends(
            require_any_permission(
                ("catalog", "manage"),
                ("orders", "create"),
            )
        )
    ],
    response_model=CategoriesPublic,
)
def read_categories(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> Any:
    """Retrieve categories. Excludes soft-deleted records by default."""
    items, count = category_service.get_categories(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search,
    )
    return CategoriesPublic(
        data=[CategoryPublic.model_validate(item) for item in items],
        count=count,
    )


@router.put(
    "/reorder",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CategoriesPublic,
)
def reorder_categories(
    *,
    session: SessionDep,
    reorder_in: CategoryReorderRequest,
) -> Any:
    """Persist category sort order in bulk."""
    items, count = category_service.reorder_categories(
        session=session, reorder_in=reorder_in
    )
    return CategoriesPublic(
        data=[CategoryPublic.model_validate(item) for item in items],
        count=count,
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CategoryPublic,
)
def read_category(session: SessionDep, id: uuid.UUID) -> Any:
    """Get a category by ID."""
    return category_service.get_category(session=session, category_id=id)


@router.post(
    "/",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CategoryPublic,
)
def create_category(*, session: SessionDep, category_in: CategoryCreate) -> Any:
    """Create a new category."""
    return category_service.create_category(session=session, category_in=category_in)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CategoryPublic,
)
def update_category(
    *,
    session: SessionDep,
    id: uuid.UUID,
    category_in: CategoryUpdate,
) -> Any:
    """Update a category."""
    return category_service.update_category(
        session=session, category_id=id, category_in=category_in
    )


@router.delete(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
)
def delete_category(session: SessionDep, id: uuid.UUID) -> Message:
    """Soft-delete a category."""
    category_service.delete_category(session=session, category_id=id)
    return Message(message="Catégorie supprimée avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=CategoryPublic,
)
def restore_category(session: SessionDep, id: uuid.UUID) -> Any:
    """Restore a soft-deleted category."""
    return category_service.restore_category(session=session, category_id=id)
