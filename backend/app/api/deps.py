from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.core.exceptions import (
    AccountInactiveError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
)
from app.models import TokenPayload, User
from app.services import permission as permission_service

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise AuthenticationError("Impossible de valider les identifiants")
    user = session.get(User, token_data.sub)
    if not user:
        raise NotFoundError("Utilisateur non trouvé")
    if not user.is_active:
        raise AccountInactiveError("Compte utilisateur inactif")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise ForbiddenError("L'utilisateur ne dispose pas de privilèges suffisants")
    return current_user


def require_permission(resource: str, action: str):
    """
    Dependency factory — ensures the current user has a specific permission.

    Superusers bypass all permission checks (is_superuser is checked first,
    before any DB query for permissions).

    Usage:
        @router.get("/orders/", dependencies=[Depends(require_permission("orders", "view"))])
        def list_orders(...): ...
    """

    def _check_permission(
        current_user: CurrentUser, session: SessionDep
    ) -> bool:
        if not permission_service.check_permission(
            session=session, user=current_user, resource=resource, action=action
        ):
            raise ForbiddenError("L'utilisateur ne dispose pas de privilèges suffisants")
        return True

    return _check_permission


def require_any_permission(*permissions: tuple[str, str]):
    """Dependency factory — allows access if the user has any listed permission."""

    def _check_permission(
        current_user: CurrentUser, session: SessionDep
    ) -> bool:
        for resource, action in permissions:
            if permission_service.check_permission(
                session=session,
                user=current_user,
                resource=resource,
                action=action,
            ):
                return True
        raise ForbiddenError("L'utilisateur ne dispose pas de privilèges suffisants")

    return _check_permission
