"""Category repository - pure database access only."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import Category


def get_by_id(*, session: Session, category_id: uuid.UUID) -> Category | None:
    return session.get(Category, category_id)


def get_all(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[Category], int]:
    conditions = []
    if not include_deleted:
        conditions.append(col(Category.is_deleted).is_(False))
    if search:
        conditions.append(col(Category.name).ilike(f"%{search.strip()}%"))

    base_query = select(Category)
    if conditions:
        base_query = base_query.where(*conditions)

    count_statement = select(func.count()).select_from(Category)
    if conditions:
        count_statement = count_statement.where(*conditions)
    count = session.exec(count_statement).one()

    statement = (
        base_query.order_by(col(Category.sort_order).asc(), col(Category.name).asc())
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return list(items), count


def create(*, session: Session, db_obj: Category) -> Category:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(
    *, session: Session, db_category: Category, update_data: dict
) -> Category:
    db_category.sqlmodel_update(update_data)
    session.add(db_category)
    return db_category


def soft_delete(*, session: Session, db_category: Category) -> None:
    db_category.is_deleted = True
    session.add(db_category)
