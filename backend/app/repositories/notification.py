import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.models.lis import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)


def get_by_id(
    *, session: Session, notification_id: uuid.UUID
) -> Notification | None:
    return session.get(Notification, notification_id)


def list_for_user(
    *,
    session: Session,
    user_id: uuid.UUID,
    skip: int,
    limit: int,
    unread_only: bool,
) -> tuple[list[Notification], int]:
    conditions = [
        Notification.user_id == user_id,
        Notification.channel == NotificationChannel.in_app,
    ]
    if unread_only:
        conditions.append(Notification.status == NotificationStatus.pending)

    statement = (
        select(Notification)
        .where(*conditions)
        .order_by(col(Notification.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    count_statement = select(func.count()).select_from(Notification).where(*conditions)
    return list(session.exec(statement).all()), session.exec(count_statement).one()


def count_unread(*, session: Session, user_id: uuid.UUID) -> int:
    statement = (
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.channel == NotificationChannel.in_app,
            Notification.status == NotificationStatus.pending,
        )
    )
    return session.exec(statement).one()


def create(*, session: Session, db_obj: Notification) -> Notification:
    session.add(db_obj)
    session.flush()
    return db_obj


def mark_read(*, notification: Notification) -> Notification:
    notification.status = NotificationStatus.sent
    notification.sent_at = datetime.now(timezone.utc)
    return notification


def list_pending_for_user(
    *, session: Session, user_id: uuid.UUID
) -> list[Notification]:
    statement = select(Notification).where(
        Notification.user_id == user_id,
        Notification.channel == NotificationChannel.in_app,
        Notification.status == NotificationStatus.pending,
    )
    return list(session.exec(statement).all())
