import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import (
    Notification,
    NotificationChannel,
    NotificationMarkAllReadPublic,
    NotificationPublic,
    NotificationsPublic,
    NotificationStatus,
    NotificationType,
    NotificationUnreadCountPublic,
)
from app.repositories import notification as notification_repo


def get_my_notifications(
    *,
    session: Session,
    user_id: uuid.UUID,
    skip: int,
    limit: int,
    unread_only: bool,
) -> NotificationsPublic:
    notifications, count = notification_repo.list_for_user(
        session=session,
        user_id=user_id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )
    return NotificationsPublic(
        data=[
            NotificationPublic.model_validate(notification)
            for notification in notifications
        ],
        count=count,
    )


def get_unread_count(
    *, session: Session, user_id: uuid.UUID
) -> NotificationUnreadCountPublic:
    return NotificationUnreadCountPublic(
        count=notification_repo.count_unread(session=session, user_id=user_id)
    )


def mark_read(
    *, session: Session, user_id: uuid.UUID, notification_id: uuid.UUID
) -> NotificationPublic:
    notification = _get_owned_in_app_notification(
        session=session, user_id=user_id, notification_id=notification_id
    )
    if notification.status == NotificationStatus.pending:
        notification_repo.mark_read(notification=notification)
        session.add(notification)
        session.commit()
        session.refresh(notification)
    return NotificationPublic.model_validate(notification)


def mark_all_read(
    *, session: Session, user_id: uuid.UUID
) -> NotificationMarkAllReadPublic:
    notifications = notification_repo.list_pending_for_user(
        session=session, user_id=user_id
    )
    for notification in notifications:
        notification_repo.mark_read(notification=notification)
        session.add(notification)
    session.commit()
    return NotificationMarkAllReadPublic(count=len(notifications))


def create_in_app_notification(
    *,
    session: Session,
    user_id: uuid.UUID,
    type: NotificationType,
    message: str,
    order_id: uuid.UUID | None = None,
    patient_id: uuid.UUID | None = None,
) -> Notification:
    return notification_repo.create(
        session=session,
        db_obj=Notification(
            user_id=user_id,
            type=type,
            channel=NotificationChannel.in_app,
            status=NotificationStatus.pending,
            message=message,
            order_id=order_id,
            patient_id=patient_id,
        ),
    )


def _get_owned_in_app_notification(
    *, session: Session, user_id: uuid.UUID, notification_id: uuid.UUID
) -> Notification:
    notification = notification_repo.get_by_id(
        session=session, notification_id=notification_id
    )
    if (
        notification is None
        or notification.user_id != user_id
        or notification.channel != NotificationChannel.in_app
    ):
        raise NotFoundError("Notification non trouvée")
    return notification
