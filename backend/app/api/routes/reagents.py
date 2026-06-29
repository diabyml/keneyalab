import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    Message,
    ReagentAlertSummaryPublic,
    ReagentCreate,
    ReagentExpiryStatus,
    ReagentLotCreate,
    ReagentLotPublic,
    ReagentLotsPublic,
    ReagentLotStatus,
    ReagentLotUpdate,
    ReagentMovementCreate,
    ReagentPublic,
    ReagentSettingsPublic,
    ReagentSettingsUpdate,
    ReagentsPublic,
    ReagentStockMovementPublic,
    ReagentStockMovementsPublic,
    ReagentUpdate,
)
from app.services import reagent as reagent_service

router = APIRouter(prefix="/reagents", tags=["reagents"])


@router.get(
    "/",
    dependencies=[Depends(require_permission("reagents", "view"))],
    response_model=ReagentsPublic,
)
def read_reagents(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    stock_status: str | None = None,
    expiry_status: ReagentExpiryStatus | None = None,
) -> Any:
    return reagent_service.list_reagents(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        stock_status=stock_status,
        expiry_status=expiry_status,
    )


@router.post(
    "/",
    dependencies=[Depends(require_permission("reagents", "manage"))],
    response_model=ReagentPublic,
)
def create_reagent(*, session: SessionDep, reagent_in: ReagentCreate) -> Any:
    return reagent_service.create_reagent(session=session, reagent_in=reagent_in)


@router.get(
    "/alerts/summary",
    dependencies=[Depends(require_permission("reagents", "view"))],
    response_model=ReagentAlertSummaryPublic,
)
def read_reagent_alert_summary(session: SessionDep) -> Any:
    return reagent_service.get_alert_summary(session=session)


@router.get(
    "/settings",
    dependencies=[Depends(require_permission("reagents", "view"))],
    response_model=ReagentSettingsPublic,
)
def read_reagent_settings(session: SessionDep) -> Any:
    return reagent_service.get_settings_public(session=session)


@router.put(
    "/settings",
    dependencies=[Depends(require_permission("reagents", "manage_settings"))],
    response_model=ReagentSettingsPublic,
)
def update_reagent_settings(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    settings_in: ReagentSettingsUpdate,
) -> Any:
    return reagent_service.update_settings(
        session=session, settings_in=settings_in, user_id=current_user.id
    )


@router.get(
    "/lots",
    dependencies=[Depends(require_permission("reagents", "view"))],
    response_model=ReagentLotsPublic,
)
def read_reagent_lots(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    reagent_id: uuid.UUID | None = None,
    status: ReagentLotStatus | None = None,
    search: str | None = None,
    expiry_status: ReagentExpiryStatus | None = None,
) -> Any:
    return reagent_service.list_lots(
        session=session,
        skip=skip,
        limit=limit,
        reagent_id=reagent_id,
        status=status,
        search=search,
        expiry_status=expiry_status,
    )


@router.post(
    "/lots",
    dependencies=[Depends(require_permission("reagents", "record_movement"))],
    response_model=ReagentLotPublic,
)
def create_reagent_lot(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    lot_in: ReagentLotCreate,
) -> Any:
    return reagent_service.create_lot(
        session=session, lot_in=lot_in, user_id=current_user.id
    )


@router.put(
    "/lots/{lot_id}",
    dependencies=[Depends(require_permission("reagents", "manage"))],
    response_model=ReagentLotPublic,
)
def update_reagent_lot(
    *,
    session: SessionDep,
    lot_id: uuid.UUID,
    lot_in: ReagentLotUpdate,
) -> Any:
    return reagent_service.update_lot(session=session, lot_id=lot_id, lot_in=lot_in)


@router.get(
    "/movements",
    dependencies=[Depends(require_permission("reagents", "view"))],
    response_model=ReagentStockMovementsPublic,
)
def read_reagent_movements(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    reagent_id: uuid.UUID | None = None,
    lot_id: uuid.UUID | None = None,
) -> Any:
    return reagent_service.list_movements(
        session=session,
        skip=skip,
        limit=limit,
        reagent_id=reagent_id,
        lot_id=lot_id,
    )


@router.post(
    "/movements",
    dependencies=[Depends(require_permission("reagents", "record_movement"))],
    response_model=ReagentStockMovementPublic,
)
def create_reagent_movement(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    movement_in: ReagentMovementCreate,
) -> Any:
    return reagent_service.create_movement(
        session=session, movement_in=movement_in, user_id=current_user.id
    )


@router.get(
    "/{reagent_id}",
    dependencies=[Depends(require_permission("reagents", "view"))],
    response_model=ReagentPublic,
)
def read_reagent(session: SessionDep, reagent_id: uuid.UUID) -> Any:
    return reagent_service.get_reagent(session=session, reagent_id=reagent_id)


@router.put(
    "/{reagent_id}",
    dependencies=[Depends(require_permission("reagents", "manage"))],
    response_model=ReagentPublic,
)
def update_reagent(
    *,
    session: SessionDep,
    reagent_id: uuid.UUID,
    reagent_in: ReagentUpdate,
) -> Any:
    return reagent_service.update_reagent(
        session=session, reagent_id=reagent_id, reagent_in=reagent_in
    )


@router.delete(
    "/{reagent_id}",
    dependencies=[Depends(require_permission("reagents", "manage"))],
)
def delete_reagent(session: SessionDep, reagent_id: uuid.UUID) -> Message:
    reagent_service.delete_reagent(session=session, reagent_id=reagent_id)
    return Message(message="Réactif supprimé avec succès")


@router.post(
    "/{reagent_id}/restore",
    dependencies=[Depends(require_permission("reagents", "manage"))],
    response_model=ReagentPublic,
)
def restore_reagent(session: SessionDep, reagent_id: uuid.UUID) -> Any:
    return reagent_service.restore_reagent(session=session, reagent_id=reagent_id)
