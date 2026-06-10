import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_any_permission, require_permission
from app.models import Message, TitleCreate, TitlePublic, TitlesPublic, TitleUpdate
from app.services import title as title_service

router = APIRouter(prefix="/titles", tags=["titles"])


@router.get(
    "/",
    dependencies=[
        Depends(
            require_any_permission(
                ("reference_data", "manage"),
                ("doctors", "create"),
                ("doctors", "edit"),
            )
        )
    ],
    response_model=TitlesPublic,
)
def read_titles(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> Any:
    """Retrieve all titles. Excludes soft-deleted by default."""
    items, count = title_service.get_titles(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search,
    )
    return TitlesPublic(
        data=[TitlePublic.model_validate(item) for item in items],
        count=count,
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=TitlePublic,
)
def read_title(session: SessionDep, id: uuid.UUID) -> Any:
    """Get a title by ID."""
    return title_service.get_title(session=session, title_id=id)


@router.post(
    "/",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=TitlePublic,
)
def create_title(*, session: SessionDep, title_in: TitleCreate) -> Any:
    """Create a new title."""
    return title_service.create_title(session=session, title_in=title_in)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=TitlePublic,
)
def update_title(
    *,
    session: SessionDep,
    id: uuid.UUID,
    title_in: TitleUpdate,
) -> Any:
    """Update a title."""
    return title_service.update_title(session=session, title_id=id, title_in=title_in)


@router.delete(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
)
def delete_title(session: SessionDep, id: uuid.UUID) -> Message:
    """Soft-delete a title."""
    title_service.delete_title(session=session, title_id=id)
    return Message(message="Titre supprimé avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=TitlePublic,
)
def restore_title(session: SessionDep, id: uuid.UUID) -> Any:
    """Restore a soft-deleted title."""
    return title_service.restore_title(session=session, title_id=id)
