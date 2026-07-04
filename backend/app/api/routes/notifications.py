import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.models.lis import (
    NotificationMarkAllReadPublic,
    NotificationPublic,
    NotificationsPublic,
    NotificationUnreadCountPublic,
)
from app.services import notification as notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/mine", response_model=NotificationsPublic)
def read_my_notifications(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 25,
    unread_only: bool = False,
) -> Any:
    return notification_service.get_my_notifications(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountPublic)
def read_my_unread_count(
    *, session: SessionDep, current_user: CurrentUser
) -> Any:
    return notification_service.get_unread_count(
        session=session, user_id=current_user.id
    )


@router.post("/mark-all-read", response_model=NotificationMarkAllReadPublic)
def mark_all_my_notifications_read(
    *, session: SessionDep, current_user: CurrentUser
) -> Any:
    return notification_service.mark_all_read(
        session=session, user_id=current_user.id
    )


@router.post("/{notification_id}/mark-read", response_model=NotificationPublic)
def mark_my_notification_read(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    notification_id: uuid.UUID,
) -> Any:
    return notification_service.mark_read(
        session=session,
        user_id=current_user.id,
        notification_id=notification_id,
    )
