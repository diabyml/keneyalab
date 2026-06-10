# Re-export everything for backward compatibility.
# Existing code doing `from app.models import User` continues to work,
# while new code can do `from app.models.user import User` if preferred.

from sqlmodel import SQLModel

from . import lis as _lis
from .auth import NewPassword, Token, TokenPayload
from .common import Message, get_datetime_utc
from .item import Item, ItemBase, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from .lis import *  # noqa: F403
from .rbac import (
    Permission,
    PermissionBase,
    PermissionCreate,
    PermissionPublic,
    PermissionsPublic,
    Role,
    RoleBase,
    RoleCreate,
    RoleDetail,
    RolePermission,
    RolePermissionCreate,
    RolePublic,
    RolesPublic,
    RoleUpdate,
    UserRole,
    UserRoleBase,
    UserRoleCreate,
    UserRolePublic,
)
from .user import (
    UpdatePassword,
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

__all__ = [
    # Common
    "get_datetime_utc",
    "Message",
    "SQLModel",
    # Auth
    "NewPassword",
    "Token",
    "TokenPayload",
    # Item
    "Item",
    "ItemBase",
    "ItemCreate",
    "ItemPublic",
    "ItemUpdate",
    "ItemsPublic",
    # RBAC — Permission
    "Permission",
    "PermissionBase",
    "PermissionCreate",
    "PermissionPublic",
    "PermissionsPublic",
    # RBAC — Role
    "Role",
    "RoleBase",
    "RoleCreate",
    "RoleDetail",
    "RolePublic",
    "RolesPublic",
    "RoleUpdate",
    # RBAC — RolePermission
    "RolePermission",
    "RolePermissionCreate",
    # RBAC — UserRole
    "UserRole",
    "UserRoleBase",
    "UserRoleCreate",
    "UserRolePublic",
    # User
    "UpdatePassword",
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
]

__all__ += [
    name
    for name in _lis.__all__
    if not name.startswith("_") and name not in __all__
]
