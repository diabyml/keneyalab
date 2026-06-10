"""Item repository — pure database access only. Never commits, never creates sessions."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.item import Item


def get_by_id(*, session: Session, item_id: uuid.UUID) -> Item | None:
    return session.get(Item, item_id)


def get_all(*, session: Session, skip: int = 0, limit: int = 100) -> tuple[list[Item], int]:
    count_statement = select(func.count()).select_from(Item)
    count = session.exec(count_statement).one()

    statement = (
        select(Item)
        .order_by(col(Item.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return list(items), count


def get_by_owner(*, session: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100) -> tuple[list[Item], int]:
    count_statement = (
        select(func.count()).select_from(Item).where(Item.owner_id == owner_id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(Item)
        .where(Item.owner_id == owner_id)
        .order_by(col(Item.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return list(items), count


def create(*, session: Session, db_obj: Item) -> Item:
    """Add an item to the session. Flushes so DB-generated fields are populated."""
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_item: Item, update_data: dict) -> Item:
    """Update attributes on an item. Does NOT commit or refresh."""
    db_item.sqlmodel_update(update_data)
    session.add(db_item)
    return db_item


def delete(*, session: Session, db_item: Item) -> None:
    """Delete an item from the session. Does NOT commit."""
    session.delete(db_item)


def delete_by_owner(*, session: Session, owner_id: uuid.UUID) -> None:
    """Delete all items belonging to a user. Does NOT commit."""
    from sqlmodel import delete as sqldelete

    statement = sqldelete(Item).where(col(Item.owner_id) == owner_id)
    session.exec(statement)
