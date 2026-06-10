import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message
from app.services import item as item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", dependencies=[Depends(require_permission("items", "view"))], response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """Retrieve items. Superusers see all; regular users see only their own."""
    items, count = item_service.get_items(
        session=session, current_user=current_user, skip=skip, limit=limit
    )
    return ItemsPublic(
        data=[ItemPublic.model_validate(item) for item in items],
        count=count,
    )


@router.get("/{id}", dependencies=[Depends(require_permission("items", "view"))], response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """Get item by ID."""
    return item_service.get_item(session=session, item_id=id, current_user=current_user)


@router.post("/", dependencies=[Depends(require_permission("items", "create"))], response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """Create new item."""
    return item_service.create_item(session=session, owner=current_user, item_in=item_in)


@router.put("/{id}", dependencies=[Depends(require_permission("items", "edit"))], response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """Update an item."""
    return item_service.update_item(
        session=session, item_id=id, current_user=current_user, item_in=item_in
    )


@router.delete("/{id}", dependencies=[Depends(require_permission("items", "delete"))])
def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """Delete an item."""
    item_service.delete_item(session=session, item_id=id, current_user=current_user)
    return Message(message="Tâche supprimée avec succès")
