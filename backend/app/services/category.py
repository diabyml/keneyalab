"""Category business logic - CRUD and ordering for catalog setup."""

import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import (
    Category,
    CategoryCreate,
    CategoryReorderRequest,
    CategoryUpdate,
)
from app.repositories import category as category_repo


def create_category(*, session: Session, category_in: CategoryCreate) -> Category:
    db_category = Category.model_validate(category_in)
    category_repo.create(session=session, db_obj=db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


def get_categories(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[Category], int]:
    search = search.strip() if search else None
    return category_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search or None,
    )


def get_category(*, session: Session, category_id: uuid.UUID) -> Category:
    db_category = category_repo.get_by_id(
        session=session, category_id=category_id
    )
    if db_category is None:
        raise NotFoundError("Catégorie non trouvée")
    return db_category


def update_category(
    *, session: Session, category_id: uuid.UUID, category_in: CategoryUpdate
) -> Category:
    db_category = category_repo.get_by_id(
        session=session, category_id=category_id
    )
    if db_category is None:
        raise NotFoundError("Catégorie non trouvée")

    update_data = category_in.model_dump(exclude_unset=True)
    category_repo.update(
        session=session, db_category=db_category, update_data=update_data
    )
    session.commit()
    session.refresh(db_category)
    return db_category


def delete_category(*, session: Session, category_id: uuid.UUID) -> None:
    db_category = category_repo.get_by_id(
        session=session, category_id=category_id
    )
    if db_category is None:
        raise NotFoundError("Catégorie non trouvée")

    category_repo.soft_delete(session=session, db_category=db_category)
    session.commit()


def restore_category(*, session: Session, category_id: uuid.UUID) -> Category:
    db_category = category_repo.get_by_id(
        session=session, category_id=category_id
    )
    if db_category is None:
        raise NotFoundError("Catégorie non trouvée")

    category_repo.update(
        session=session,
        db_category=db_category,
        update_data={"is_deleted": False},
    )
    session.commit()
    session.refresh(db_category)
    return db_category


def reorder_categories(
    *, session: Session, reorder_in: CategoryReorderRequest
) -> tuple[list[Category], int]:
    categories_by_id: dict[uuid.UUID, Category] = {}
    for item in reorder_in.items:
        db_category = category_repo.get_by_id(
            session=session, category_id=item.id
        )
        if db_category is None:
            raise NotFoundError("Catégorie non trouvée")
        categories_by_id[item.id] = db_category

    ordered_items = sorted(reorder_in.items, key=lambda item: item.sort_order)
    for index, item in enumerate(ordered_items, start=1):
        category_repo.update(
            session=session,
            db_category=categories_by_id[item.id],
            update_data={"sort_order": index},
        )

    session.commit()
    return category_repo.get_all(session=session, limit=500)
