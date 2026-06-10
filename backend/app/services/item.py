"""Item business logic — CRUD with ownership enforcement."""

import uuid

from sqlmodel import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.item import Item, ItemCreate, ItemUpdate
from app.models.user import User
from app.repositories import item as item_repo


def create_item(*, session: Session, owner: User, item_in: ItemCreate) -> Item:
    """Create a new item owned by the given user."""
    db_item = Item.model_validate(item_in, update={"owner_id": owner.id})
    item_repo.create(session=session, db_obj=db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def get_items(
    *, session: Session, current_user: User, skip: int = 0, limit: int = 100
) -> tuple[list[Item], int]:
    """
    Get items. Superusers see all items; regular users see only their own.
    """
    if current_user.is_superuser:
        return item_repo.get_all(session=session, skip=skip, limit=limit)
    return item_repo.get_by_owner(
        session=session, owner_id=current_user.id, skip=skip, limit=limit
    )


def _check_ownership(item: Item, current_user: User) -> None:
    """Raise ForbiddenError if the user is not a superuser and not the owner."""
    if not current_user.is_superuser and item.owner_id != current_user.id:
        raise ForbiddenError("Permissions insuffisantes")


def get_item(*, session: Session, item_id: uuid.UUID, current_user: User) -> Item:
    """Get a single item, enforcing ownership."""
    db_item = item_repo.get_by_id(session=session, item_id=item_id)
    if db_item is None:
        raise NotFoundError("Tâche non trouvée")
    _check_ownership(db_item, current_user)
    return db_item


def update_item(
    *, session: Session, item_id: uuid.UUID, current_user: User, item_in: ItemUpdate
) -> Item:
    """Update an item, enforcing ownership."""
    db_item = item_repo.get_by_id(session=session, item_id=item_id)
    if db_item is None:
        raise NotFoundError("Tâche non trouvée")
    _check_ownership(db_item, current_user)

    user_data = item_in.model_dump(exclude_unset=True)
    item_repo.update(session=session, db_item=db_item, update_data=user_data)
    session.commit()
    session.refresh(db_item)
    return db_item


def delete_item(
    *, session: Session, item_id: uuid.UUID, current_user: User
) -> None:
    """Delete an item, enforcing ownership."""
    db_item = item_repo.get_by_id(session=session, item_id=item_id)
    if db_item is None:
        raise NotFoundError("Tâche non trouvée")
    _check_ownership(db_item, current_user)

    item_repo.delete(session=session, db_item=db_item)
    session.commit()
