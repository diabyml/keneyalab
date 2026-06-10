"""UserRole repository — pure database access only. Never commits."""
import uuid
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.rbac import Role, UserRole


def get_by_user(*, session: Session, user_id: uuid.UUID) -> list[UserRole]:
    statement = select(UserRole).where(UserRole.user_id == user_id)
    return list(session.exec(statement).all())


def get_active_by_user(*, session: Session, user_id: uuid.UUID) -> list[UserRole]:
    """Return non-expired UserRole records whose Role is not soft-deleted."""
    now = datetime.now(timezone.utc)
    statement = (
        select(UserRole)
        .join(Role, UserRole.role_id == Role.id)
        .where(
            UserRole.user_id == user_id,
            Role.is_deleted == False,  # noqa: E712
        )
        .where(
            (UserRole.expires_at == None) | (UserRole.expires_at > now)  # noqa: E711
        )
    )
    return list(session.exec(statement).all())


def get_by_user_and_role(
    *, session: Session, user_id: uuid.UUID, role_id: uuid.UUID
) -> UserRole | None:
    statement = select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    )
    return session.exec(statement).first()


def create(*, session: Session, db_obj: UserRole) -> UserRole:
    session.add(db_obj)
    session.flush()
    return db_obj


def delete(*, session: Session, db_obj: UserRole) -> None:
    session.delete(db_obj)
