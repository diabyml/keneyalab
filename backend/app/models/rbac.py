# ruff: noqa

"""
RBAC — Role-Based Access Control
SQLModel definitions

Tables:
  permissions       — granular resource + action pairs
  roles             — named role with optional soft-delete
  role_permissions  — many-to-many join (role ↔ permission)
  user_roles        — many-to-many join (user ↔ role) with expiry

Conventions follow the existing project pattern:
  <Entity>Base      — shared fields
  <Entity>Create    — API request body for POST
  <Entity>Update    — API request body for PUT/PATCH
  <Entity>Public    — API response
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from .common import get_datetime_utc

# ---------------------------------------------------------------------------
# Permission
# ---------------------------------------------------------------------------

class PermissionBase(SQLModel):
    resource:    str       = Field(max_length=100)
    action:      str       = Field(max_length=100)
    description: str | None = Field(default=None)


class PermissionCreate(PermissionBase):
    pass


class Permission(PermissionBase, table=True):
    __tablename__  = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )

    id:         uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    role_permissions: list["RolePermission"] = Relationship(back_populates="permission", cascade_delete=True)


class PermissionPublic(PermissionBase):
    id:         uuid.UUID
    created_at: datetime


class PermissionsPublic(SQLModel):
    data:  list[PermissionPublic]
    count: int


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------

class RoleBase(SQLModel):
    name:        str       = Field(max_length=100)
    description: str | None = Field(default=None)
    is_default:  bool      = Field(default=False)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    name:        str | None  = Field(default=None, max_length=100)
    description: str | None  = Field(default=None)
    is_default:  bool | None = Field(default=None)


class Role(RoleBase, table=True):
    __tablename__  = "roles"
    __table_args__ = (UniqueConstraint("name", name="uq_roles_name"),)

    id:         uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    is_deleted: bool      = Field(default=False)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    role_permissions: list["RolePermission"] = Relationship(back_populates="role", cascade_delete=True)
    user_roles:       list["UserRole"]       = Relationship(back_populates="role", cascade_delete=True)


class RolePublic(RoleBase):
    id:         uuid.UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class RolesPublic(SQLModel):
    data:  list[RolePublic]
    count: int


class RoleDetail(RolePublic):
    permissions: list[PermissionPublic] = []


# ---------------------------------------------------------------------------
# RolePermission (join table)
# ---------------------------------------------------------------------------

class RolePermission(SQLModel, table=True):
    __tablename__  = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
    )

    id:            uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    role_id:       uuid.UUID = Field(foreign_key="roles.id", ondelete="CASCADE")
    permission_id: uuid.UUID = Field(foreign_key="permissions.id", ondelete="CASCADE")
    created_at:    datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    role:       "Role"       = Relationship(back_populates="role_permissions")
    permission: "Permission" = Relationship(back_populates="role_permissions")


class RolePermissionCreate(SQLModel):
    permission_id: uuid.UUID


# ---------------------------------------------------------------------------
# UserRole (join table with metadata)
# ---------------------------------------------------------------------------

class UserRoleBase(SQLModel):
    user_id:        uuid.UUID         = Field(foreign_key="user.id", ondelete="CASCADE")
    role_id:        uuid.UUID         = Field(foreign_key="roles.id", ondelete="CASCADE")
    assigned_by_id: uuid.UUID | None  = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    expires_at:     datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class UserRoleCreate(SQLModel):
    role_id:    uuid.UUID
    expires_at: datetime | None = None


class UserRole(UserRoleBase, table=True):
    __tablename__ = "user_roles"

    id:          uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    assigned_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    created_at:  datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    updated_at:  datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    user:        "User" = Relationship(   # type: ignore
        back_populates="user_roles",
        sa_relationship_kwargs={"foreign_keys": "[UserRole.user_id]"},
    )
    role:        "Role" = Relationship(back_populates="user_roles")
    assigned_by: "User" = Relationship(  # type: ignore  # noqa: F821
        back_populates="assigned_roles",
        sa_relationship_kwargs={"foreign_keys": "[UserRole.assigned_by_id]"},
    )


class UserRolePublic(UserRoleBase):
    id:          uuid.UUID
    assigned_at: datetime
    role:        RolePublic | None = None
