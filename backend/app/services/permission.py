"""RBAC business logic — permission resolution, role/perm CRUD."""
import uuid

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.rbac import (
    Permission,
    PermissionCreate,
    Role,
    RoleCreate,
    RolePermission,
    RoleUpdate,
    UserRole,
    UserRoleCreate,
)
from app.models.user import User
from app.repositories import permission as perm_repo
from app.repositories import role as role_repo
from app.repositories import role_permission as rp_repo
from app.repositories import user_role as ur_repo


# ---------------------------------------------------------------------------
# Permission resolution
# ---------------------------------------------------------------------------

def get_user_permissions(*, session: Session, user: User) -> list[Permission]:
    """
    Return all effective permissions for a user.
    Superusers get ALL permissions in the system.
    Regular users get the union across all non-expired, non-deleted roles.
    """
    if user.is_superuser:
        perms, _ = perm_repo.get_all(session=session, skip=0, limit=10_000)
        return perms

    active_roles = ur_repo.get_active_by_user(session=session, user_id=user.id)
    if not active_roles:
        return []

    permission_ids: set[uuid.UUID] = set()
    for ur in active_roles:
        rps = rp_repo.get_by_role(session=session, role_id=ur.role_id)
        permission_ids.update(rp.permission_id for rp in rps)

    if not permission_ids:
        return []

    # Fetch Permission objects by IDs
    permissions: list[Permission] = []
    for pid in permission_ids:
        perm = perm_repo.get_by_id(session=session, permission_id=pid)
        if perm is not None:
            permissions.append(perm)
    return permissions


def check_permission(
    *, session: Session, user: User, resource: str, action: str
) -> bool:
    """
    Check whether a user has a specific permission.
    Superusers always return True (short-circuit, no DB query for permissions).
    """
    if user.is_superuser:
        return True

    permissions = get_user_permissions(session=session, user=user)
    return any(
        p.resource == resource and p.action == action for p in permissions
    )


# ---------------------------------------------------------------------------
# Permission CRUD
# ---------------------------------------------------------------------------

def create_permission(
    *, session: Session, permission_in: PermissionCreate
) -> Permission:
    """Create a new permission. Raises ConflictError on duplicate resource+action."""
    existing = perm_repo.get_by_resource_action(
        session=session, resource=permission_in.resource, action=permission_in.action
    )
    if existing:
        raise ConflictError("Cette permission existe déjà")

    db_obj = Permission.model_validate(permission_in)
    perm_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_permission(*, session: Session, permission_id: uuid.UUID) -> None:
    """Delete a permission. Raises NotFoundError if not found."""
    db_obj = perm_repo.get_by_id(session=session, permission_id=permission_id)
    if db_obj is None:
        raise NotFoundError("Permission non trouvée")
    perm_repo.delete(session=session, db_obj=db_obj)
    session.commit()


# ---------------------------------------------------------------------------
# Role CRUD
# ---------------------------------------------------------------------------

def create_role(*, session: Session, role_in: RoleCreate) -> Role:
    """Create a new role. Raises ConflictError on duplicate name."""
    existing = role_repo.get_by_name(session=session, name=role_in.name)
    if existing:
        raise ConflictError("Un rôle avec ce nom existe déjà")

    db_obj = Role.model_validate(role_in)
    role_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_role(
    *, session: Session, role_id: uuid.UUID, role_in: RoleUpdate
) -> Role:
    """Update a role. Raises NotFoundError or ConflictError (duplicate name)."""
    db_obj = role_repo.get_by_id(session=session, role_id=role_id)
    if db_obj is None:
        raise NotFoundError("Rôle non trouvé")

    update_data = role_in.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = role_repo.get_by_name(session=session, name=update_data["name"])
        if existing and existing.id != role_id:
            raise ConflictError("Un rôle avec ce nom existe déjà")

    role_repo.update(session=session, db_role=db_obj, update_data=update_data)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_role(*, session: Session, role_id: uuid.UUID) -> None:
    """Soft-delete a role. Raises NotFoundError if not found."""
    db_obj = role_repo.get_by_id(session=session, role_id=role_id)
    if db_obj is None:
        raise NotFoundError("Rôle non trouvé")
    role_repo.soft_delete(session=session, db_role=db_obj)
    session.commit()


# ---------------------------------------------------------------------------
# Role-Permission management
# ---------------------------------------------------------------------------

def add_permission_to_role(
    *, session: Session, role_id: uuid.UUID, permission_id: uuid.UUID
) -> RolePermission:
    """Assign a permission to a role. Raises ConflictError if already assigned."""
    # Ensure role and permission exist
    role = role_repo.get_by_id(session=session, role_id=role_id)
    if role is None:
        raise NotFoundError("Rôle non trouvé")
    perm = perm_repo.get_by_id(session=session, permission_id=permission_id)
    if perm is None:
        raise NotFoundError("Permission non trouvée")

    existing = rp_repo.get_by_role_and_permission(
        session=session, role_id=role_id, permission_id=permission_id
    )
    if existing:
        raise ConflictError("Cette permission est déjà assignée au rôle")

    db_obj = RolePermission(role_id=role_id, permission_id=permission_id)
    rp_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def remove_permission_from_role(
    *, session: Session, role_id: uuid.UUID, permission_id: uuid.UUID
) -> None:
    """Remove a permission from a role."""
    db_obj = rp_repo.get_by_role_and_permission(
        session=session, role_id=role_id, permission_id=permission_id
    )
    if db_obj is None:
        raise NotFoundError("Cette permission n'est pas assignée au rôle")
    rp_repo.delete(session=session, db_obj=db_obj)
    session.commit()


# ---------------------------------------------------------------------------
# User-Role management
# ---------------------------------------------------------------------------

def assign_role_to_user(
    *,
    session: Session,
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    assigned_by: User,
) -> UserRole:
    """Assign a role to a user. Raises ConflictError if already assigned."""
    # Ensure role exists and is not deleted
    role = role_repo.get_by_id(session=session, role_id=role_id)
    if role is None or role.is_deleted:
        raise NotFoundError("Rôle non trouvé")

    existing = ur_repo.get_by_user_and_role(
        session=session, user_id=user_id, role_id=role_id
    )
    if existing:
        raise ConflictError("Ce rôle est déjà assigné à l'utilisateur")

    db_obj = UserRole(
        user_id=user_id,
        role_id=role_id,
        assigned_by_id=assigned_by.id,
    )
    try:
        ur_repo.create(session=session, db_obj=db_obj)
        session.commit()
        session.refresh(db_obj)
    except IntegrityError:
        session.rollback()
        raise ConflictError("Ce rôle est déjà assigné à l'utilisateur")
    return db_obj


def remove_role_from_user(
    *, session: Session, user_id: uuid.UUID, role_id: uuid.UUID
) -> None:
    """Remove a role from a user. Raises NotFoundError if not assigned."""
    db_obj = ur_repo.get_by_user_and_role(
        session=session, user_id=user_id, role_id=role_id
    )
    if db_obj is None:
        raise NotFoundError("Ce rôle n'est pas assigné à l'utilisateur")
    ur_repo.delete(session=session, db_obj=db_obj)
    session.commit()


def assign_default_roles(
    *, session: Session, user: User, assigned_by: User
) -> list[UserRole]:
    """Assign all default roles (is_default=True) to a user."""
    defaults = role_repo.get_defaults(session=session)
    assigned: list[UserRole] = []
    for role in defaults:
        existing = ur_repo.get_by_user_and_role(
            session=session, user_id=user.id, role_id=role.id
        )
        if existing:
            continue
        try:
            db_obj = UserRole(
                user_id=user.id,
                role_id=role.id,
                assigned_by_id=assigned_by.id,
            )
            ur_repo.create(session=session, db_obj=db_obj)
            session.flush()
            assigned.append(db_obj)
        except IntegrityError:
            session.rollback()
            continue
    if assigned:
        session.commit()
    return assigned
