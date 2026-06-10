"""Title business logic — CRUD for reference data (no ownership checks)."""

import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import Title, TitleCreate, TitleUpdate
from app.repositories import title as title_repo


def create_title(*, session: Session, title_in: TitleCreate) -> Title:
    """Create a new title."""
    db_title = Title.model_validate(title_in)
    title_repo.create(session=session, db_obj=db_title)
    session.commit()
    session.refresh(db_title)
    return db_title


def get_titles(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> tuple[list[Title], int]:
    """Get all titles. Excludes soft-deleted by default."""
    return title_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search,
    )


def get_title(*, session: Session, title_id: uuid.UUID) -> Title:
    """Get a single title by ID."""
    db_title = title_repo.get_by_id(session=session, title_id=title_id)
    if db_title is None:
        raise NotFoundError("Titre non trouvé")
    return db_title


def update_title(
    *, session: Session, title_id: uuid.UUID, title_in: TitleUpdate
) -> Title:
    """Update a title's name."""
    db_title = title_repo.get_by_id(session=session, title_id=title_id)
    if db_title is None:
        raise NotFoundError("Titre non trouvé")

    update_data = title_in.model_dump(exclude_unset=True)
    title_repo.update(session=session, db_title=db_title, update_data=update_data)
    session.commit()
    session.refresh(db_title)
    return db_title


def delete_title(*, session: Session, title_id: uuid.UUID) -> None:
    """Soft-delete a title."""
    db_title = title_repo.get_by_id(session=session, title_id=title_id)
    if db_title is None:
        raise NotFoundError("Titre non trouvé")

    title_repo.soft_delete(session=session, db_title=db_title)
    session.commit()


def restore_title(*, session: Session, title_id: uuid.UUID) -> Title:
    """Restore a soft-deleted title."""
    db_title = title_repo.get_by_id(session=session, title_id=title_id)
    if db_title is None:
        raise NotFoundError("Titre non trouvé")

    title_repo.update(
        session=session, db_title=db_title, update_data={"is_deleted": False}
    )
    session.commit()
    session.refresh(db_title)
    return db_title
