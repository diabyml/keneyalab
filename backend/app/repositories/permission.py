"""Permission repository — pure database access only. Never commits."""
import uuid

from sqlmodel import Session, func, select

from app.models.rbac import Permission


def get_all(*, session: Session, skip: int = 0, limit: int = 100) -> tuple[list[Permission], int]:
    count_statement = select(func.count()).select_from(Permission)
    count = session.exec(count_statement).one()

    statement = select(Permission).offset(skip).limit(limit)
    permissions = session.exec(statement).all()
    return list(permissions), count


def get_by_id(*, session: Session, permission_id: uuid.UUID) -> Permission | None:
    return session.get(Permission, permission_id)


def get_by_resource_action(*, session: Session, resource: str, action: str) -> Permission | None:
    statement = select(Permission).where(
        Permission.resource == resource,
        Permission.action == action,
    )
    return session.exec(statement).first()


def create(*, session: Session, db_obj: Permission) -> Permission:
    session.add(db_obj)
    session.flush()
    return db_obj


def delete(*, session: Session, db_obj: Permission) -> None:
    session.delete(db_obj)
