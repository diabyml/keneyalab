import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    CriticalNotificationAcknowledge,
    CriticalNotificationCountPublic,
    CriticalNotificationCreate,
    CriticalNotificationDetailPublic,
    CriticalNotificationListPublic,
    CriticalRecipientsPublic,
)
from app.services import result as result_service

router = APIRouter(
    prefix="/critical-notifications", tags=["critical-notifications"]
)


@router.get(
    "/",
    dependencies=[
        Depends(require_permission("critical_notifications", "view"))
    ],
    response_model=CriticalNotificationListPublic,
)
def read_critical_notifications(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    acknowledged: bool | None = None,
    search: str | None = None,
) -> Any:
    return result_service.get_critical_notifications(
        session=session,
        skip=skip,
        limit=limit,
        acknowledged=acknowledged,
        search=search,
    )


@router.get(
    "/unacknowledged-count",
    dependencies=[
        Depends(require_permission("critical_notifications", "view"))
    ],
    response_model=CriticalNotificationCountPublic,
)
def read_unacknowledged_count(session: SessionDep) -> Any:
    return result_service.get_unacknowledged_count(session=session)


@router.get(
    "/recipients",
    dependencies=[Depends(require_permission("results", "enter"))],
    response_model=CriticalRecipientsPublic,
)
def read_critical_recipients(
    session: SessionDep,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> Any:
    return result_service.get_recipients(
        session=session, search=search, skip=skip, limit=limit
    )


@router.post(
    "/results/{result_id}",
    dependencies=[Depends(require_permission("results", "enter"))],
    response_model=CriticalNotificationDetailPublic,
)
def create_critical_notification(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    result_id: uuid.UUID,
    request_in: CriticalNotificationCreate,
) -> Any:
    return result_service.create_critical_notification(
        session=session,
        result_id=result_id,
        request=request_in,
        user_id=current_user.id,
    )


@router.get(
    "/{notification_id}",
    dependencies=[
        Depends(require_permission("critical_notifications", "view"))
    ],
    response_model=CriticalNotificationDetailPublic,
)
def read_critical_notification(
    session: SessionDep, notification_id: uuid.UUID
) -> Any:
    return result_service.get_critical_notification(
        session=session, notification_id=notification_id
    )


@router.post(
    "/{notification_id}/acknowledge",
    dependencies=[
        Depends(require_permission("critical_notifications", "acknowledge"))
    ],
    response_model=CriticalNotificationDetailPublic,
)
def acknowledge_critical_notification(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    notification_id: uuid.UUID,
    request_in: CriticalNotificationAcknowledge,
) -> Any:
    return result_service.acknowledge_critical_notification(
        session=session,
        notification_id=notification_id,
        request=request_in,
        user_id=current_user.id,
    )
