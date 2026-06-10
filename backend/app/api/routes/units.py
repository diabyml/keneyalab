import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import Message, UnitCreate, UnitPublic, UnitsPublic, UnitUpdate
from app.services import unit as unit_service

router = APIRouter(prefix="/units", tags=["units"])


@router.get(
    "/",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=UnitsPublic,
)
def read_units(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> Any:
    """Retrieve all units. Excludes soft-deleted by default."""
    items, count = unit_service.get_units(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search,
    )
    return UnitsPublic(
        data=[UnitPublic.model_validate(item) for item in items],
        count=count,
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=UnitPublic,
)
def read_unit(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """Get a unit by ID."""
    return unit_service.get_unit(session=session, unit_id=id)


@router.post(
    "/",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=UnitPublic,
)
def create_unit(
    *, session: SessionDep, current_user: CurrentUser, unit_in: UnitCreate
) -> Any:
    """Create a new unit."""
    return unit_service.create_unit(session=session, unit_in=unit_in)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=UnitPublic,
)
def update_unit(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    unit_in: UnitUpdate,
) -> Any:
    """Update a unit."""
    return unit_service.update_unit(session=session, unit_id=id, unit_in=unit_in)


@router.delete(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
)
def delete_unit(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """Soft-delete a unit."""
    unit_service.delete_unit(session=session, unit_id=id)
    return Message(message="Unité supprimée avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=UnitPublic,
)
def restore_unit(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """Restore a soft-deleted unit."""
    return unit_service.restore_unit(session=session, unit_id=id)
