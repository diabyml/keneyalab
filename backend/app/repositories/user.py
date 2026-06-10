"""User repository — pure database access only. Never commits, never creates sessions."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.user import User


def get_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def get_all(*, session: Session, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = (
        select(User)
        .order_by(col(User.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    users = session.exec(statement).all()
    return list(users), count


def create(*, session: Session, db_obj: User) -> User:
    """Add a user to the session. Flushes so DB-generated fields are populated."""
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_user: User, update_data: dict, extra_data: dict | None = None) -> User:
    """Update attributes on a user. Does NOT commit or refresh."""
    db_user.sqlmodel_update(update_data, update=extra_data or {})
    session.add(db_user)
    return db_user
