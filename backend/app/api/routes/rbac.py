"""RBAC admin endpoints — manage permissions, roles, and user-role assignments."""
import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentUser,
    SessionDep,
    require_permission,
)
from app.core.exceptions import NotFoundError
from app.models.rbac import (
    PermissionCreate,
    PermissionPublic,
    PermissionsPublic,
    RoleCreate,
    RoleDetail,
    RolePermissionCreate,
    RolePublic,
    RolesPublic,
    RoleUpdate,
    UserRoleCreate,
    UserRolePublic,
)
from app.repositories import permission as perm_repo
from app.repositories import role as role_repo
from app.repositories import role_permission as rp_repo
from app.repositories import user_role as ur_repo
from app.services import permission as permission_service

router = APIRouter(prefix="/rbac", tags=["rbac"])


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

@router.get(
    "/permissions/",
    dependencies=[Depends(require_permission("roles", "manage"))],
    response_model=PermissionsPublic,
)
def list_permissions(
    session: SessionDep, skip: int = 0, limit: int = 200
) -> Any:
    """List all permissions."""
    perms, count = perm_repo.get_all(session=session, skip=skip, limit=limit)
    return PermissionsPublic(
        data=[PermissionPublic.model_validate(p) for p in perms],
        count=count,
    )


@router.post(
    "/permissions/",
    dependencies=[Depends(require_permission("roles", "manage"))],
    response_model=PermissionPublic,
    status_code=201,
)
def create_permission(
    *, session: SessionDep, permission_in: PermissionCreate
) -> Any:
    """Create a new permission."""
    return permission_service.create_permission(
        session=session, permission_in=permission_in
    )


@router.delete(
    "/permissions/{permission_id}",
    dependencies=[Depends(require_permission("roles", "manage"))],
    status_code=204,
)
def delete_permission(
    session: SessionDep, permission_id: uuid.UUID
) -> None:
    """Delete a permission."""
    permission_service.delete_permission(
        session=session, permission_id=permission_id
    )


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

@router.get(
    "/roles/",
    dependencies=[Depends(require_permission("roles", "manage"))],
    response_model=RolesPublic,
)
def list_roles(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """List all roles (soft-deleted excluded)."""
    roles, count = role_repo.get_all(
        session=session, skip=skip, limit=limit, include_deleted=False
    )
    return RolesPublic(
        data=[RolePublic.model_validate(r) for r in roles],
        count=count,
    )


@router.get(
    "/roles/{role_id}",
    dependencies=[Depends(require_permission("roles", "manage"))],
    response_model=RoleDetail,
)
def get_role(session: SessionDep, role_id: uuid.UUID) -> Any:
    """Get a role with its permissions."""
    role = role_repo.get_by_id(session=session, role_id=role_id)
    if role is None:
        raise NotFoundError("Rôle non trouvé")

    rps = rp_repo.get_by_role(session=session, role_id=role.id)
    perms = []
    for rp in rps:
        p = perm_repo.get_by_id(session=session, permission_id=rp.permission_id)
        if p:
            perms.append(PermissionPublic.model_validate(p))

    return RoleDetail(
        id=role.id,
        name=role.name,
        description=role.description,
        is_default=role.is_default,
        is_deleted=role.is_deleted,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permissions=perms,
    )


@router.post(
    "/roles/",
    dependencies=[Depends(require_permission("roles", "manage"))],
    response_model=RolePublic,
    status_code=201,
)
def create_role(*, session: SessionDep, role_in: RoleCreate) -> Any:
    """Create a new role."""
    return permission_service.create_role(session=session, role_in=role_in)


@router.patch(
    "/roles/{role_id}",
    dependencies=[Depends(require_permission("roles", "manage"))],
    response_model=RolePublic,
)
def update_role(
    *, session: SessionDep, role_id: uuid.UUID, role_in: RoleUpdate
) -> Any:
    """Update a role."""
    return permission_service.update_role(
        session=session, role_id=role_id, role_in=role_in
    )


@router.delete(
    "/roles/{role_id}",
    dependencies=[Depends(require_permission("roles", "manage"))],
    status_code=204,
)
def delete_role(session: SessionDep, role_id: uuid.UUID) -> None:
    """Soft-delete a role."""
    permission_service.delete_role(session=session, role_id=role_id)


# ---------------------------------------------------------------------------
# Role-Permission assignments
# ---------------------------------------------------------------------------

@router.post(
    "/roles/{role_id}/permissions",
    dependencies=[Depends(require_permission("roles", "manage"))],
    status_code=201,
)
def add_permission_to_role(
    session: SessionDep, role_id: uuid.UUID, body: RolePermissionCreate
) -> Any:
    """Assign a permission to a role."""
    permission_service.add_permission_to_role(
        session=session,
        role_id=role_id,
        permission_id=body.permission_id,
    )
    return {"detail": "Permission assignée au rôle"}


@router.delete(
    "/roles/{role_id}/permissions/{permission_id}",
    dependencies=[Depends(require_permission("roles", "manage"))],
    status_code=204,
)
def remove_permission_from_role(
    session: SessionDep, role_id: uuid.UUID, permission_id: uuid.UUID
) -> None:
    """Remove a permission from a role."""
    permission_service.remove_permission_from_role(
        session=session,
        role_id=role_id,
        permission_id=permission_id,
    )


# ---------------------------------------------------------------------------
# User-Role assignments
# ---------------------------------------------------------------------------

@router.get(
    "/users/{user_id}/roles",
    dependencies=[Depends(require_permission("roles", "manage"))],
    response_model=list[UserRolePublic],
)
def list_user_roles(
    session: SessionDep, user_id: uuid.UUID
) -> Any:
    """List all role assignments for a user."""
    assignments = ur_repo.get_by_user(session=session, user_id=user_id)
    result: list[UserRolePublic] = []
    for ur in assignments:
        role = role_repo.get_by_id(session=session, role_id=ur.role_id)
        result.append(
            UserRolePublic(
                id=ur.id,
                user_id=ur.user_id,
                role_id=ur.role_id,
                assigned_by_id=ur.assigned_by_id,
                expires_at=ur.expires_at,
                assigned_at=ur.assigned_at,
                role=RolePublic.model_validate(role) if role else None,
            )
        )
    return result


@router.post(
    "/users/{user_id}/roles",
    dependencies=[Depends(require_permission("roles", "manage"))],
    status_code=201,
)
def assign_role_to_user(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_id: uuid.UUID,
    body: UserRoleCreate,
) -> Any:
    """Assign a role to a user."""
    permission_service.assign_role_to_user(
        session=session,
        user_id=user_id,
        role_id=body.role_id,
        assigned_by=current_user,
    )
    return {"detail": "Rôle assigné à l'utilisateur"}


@router.delete(
    "/users/{user_id}/roles/{role_id}",
    dependencies=[Depends(require_permission("roles", "manage"))],
    status_code=204,
)
def remove_role_from_user(
    session: SessionDep, user_id: uuid.UUID, role_id: uuid.UUID
) -> None:
    """Remove a role from a user."""
    permission_service.remove_role_from_user(
        session=session,
        user_id=user_id,
        role_id=role_id,
    )
