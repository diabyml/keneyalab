"""RolePermission repository — pure database access only. Never commits."""
import uuid

from sqlmodel import Session, select

from app.models.rbac import RolePermission


def get_by_role(*, session: Session, role_id: uuid.UUID) -> list[RolePermission]:
    statement = select(RolePermission).where(RolePermission.role_id == role_id)
    return list(session.exec(statement).all())


def get_by_role_and_permission(
    *, session: Session, role_id: uuid.UUID, permission_id: uuid.UUID
) -> RolePermission | None:
    statement = select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    )
    return session.exec(statement).first()


def create(*, session: Session, db_obj: RolePermission) -> RolePermission:
    session.add(db_obj)
    session.flush()
    return db_obj


def delete(*, session: Session, db_obj: RolePermission) -> None:
    session.delete(db_obj)
