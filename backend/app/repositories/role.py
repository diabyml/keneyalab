"""Role repository — pure database access only. Never commits."""
import uuid

from sqlmodel import Session, col, func, select

from app.models.rbac import Role


def get_all(
    *, session: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False
) -> tuple[list[Role], int]:
    base = select(Role)
    if not include_deleted:
        base = base.where(Role.is_deleted == False)  # noqa: E712

    count_statement = select(func.count()).select_from(base.subquery())
    count = session.exec(count_statement).one()

    statement = (
        base.order_by(col(Role.created_at).desc()).offset(skip).limit(limit)
    )
    roles = session.exec(statement).all()
    return list(roles), count


def get_by_id(*, session: Session, role_id: uuid.UUID) -> Role | None:
    return session.get(Role, role_id)


def get_by_name(*, session: Session, name: str) -> Role | None:
    statement = select(Role).where(Role.name == name)
    return session.exec(statement).first()


def get_defaults(*, session: Session) -> list[Role]:
    """Return roles with is_default=True that are not soft-deleted."""
    statement = select(Role).where(
        Role.is_default == True,  # noqa: E712
        Role.is_deleted == False,  # noqa: E712
    )
    return list(session.exec(statement).all())


def create(*, session: Session, db_obj: Role) -> Role:
    session.add(db_obj)
    session.flush()
    return db_obj


def update(*, session: Session, db_role: Role, update_data: dict) -> Role:
    db_role.sqlmodel_update(update_data)
    session.add(db_role)
    return db_role


def soft_delete(*, session: Session, db_role: Role) -> None:
    db_role.is_deleted = True
    session.add(db_role)
