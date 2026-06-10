"""RBAC test utilities — helpers for creating test permissions, roles, assignments."""
import uuid

from sqlmodel import Session

from app.models.rbac import (
    Permission,
    PermissionCreate,
    Role,
    RoleCreate,
    UserRole,
)
from app.models.user import User
from app.services import permission as permission_service


def create_test_permission(
    *, session: Session, resource: str = "test_resource", action: str = "test_action"
) -> Permission:
    """Create a permission for testing. Uses unique resource/action to avoid conflicts."""
    unique_resource = f"{resource}_{uuid.uuid4().hex[:8]}"
    unique_action = f"{action}_{uuid.uuid4().hex[:8]}"
    perm_in = PermissionCreate(resource=unique_resource, action=unique_action)
    return permission_service.create_permission(session=session, permission_in=perm_in)


def create_test_role(
    *, session: Session, name: str | None = None
) -> Role:
    """Create a role for testing."""
    role_name = name or f"test_role_{uuid.uuid4().hex[:8]}"
    role_in = RoleCreate(name=role_name, description="Test role")
    return permission_service.create_role(session=session, role_in=role_in)


def assign_role_to_test_user(
    *,
    session: Session,
    user: User,
    role: Role,
    assigned_by: User,
) -> UserRole:
    """Assign a role to a user for testing."""
    return permission_service.assign_role_to_user(
        session=session,
        user_id=user.id,
        role_id=role.id,
        assigned_by=assigned_by,
    )


def add_permission_to_test_role(
    *,
    session: Session,
    role: Role,
    permission: Permission,
) -> None:
    """Add a permission to a role."""
    permission_service.add_permission_to_role(
        session=session,
        role_id=role.id,
        permission_id=permission.id,
    )
