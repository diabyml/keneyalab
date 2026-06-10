"""Title repository — pure database access only. Never commits, never creates sessions."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import Title


def get_by_id(*, session: Session, title_id: uuid.UUID) -> Title | None:
    return session.get(Title, title_id)


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[Title], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(Title.is_deleted).is_(False))
    if search:
        conditions.append(col(Title.name).ilike(f"%{search.strip()}%"))

    base_query = select(Title)
    if conditions:
        base_query = base_query.where(*conditions)

    count_statement = select(func.count()).select_from(Title)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()

    statement = (
        base_query
        .order_by(col(Title.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return list(items), count


def create(*, session: Session, db_obj: Title) -> Title:
    """Add a title to the session. Flushes so DB-generated fields are populated."""
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_title: Title, update_data: dict) -> Title:
    """Update attributes on a title. Does NOT commit or refresh."""
    db_title.sqlmodel_update(update_data)
    session.add(db_title)
    return db_title


def soft_delete(*, session: Session, db_title: Title) -> None:
    """Soft-delete a title by setting is_deleted=True. Does NOT commit."""
    db_title.is_deleted = True
    session.add(db_title)
