"""Authentication workflows — login, password recovery, token management."""

from datetime import timedelta

from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import AccountInactiveError, AuthenticationError
from app.models.auth import NewPassword, Token
from app.models.rbac import PermissionPublic
from app.models.user import User
from app.repositories import user as user_repo
from app.services import permission as permission_service
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

# Dummy hash used for timing-attack prevention when the user is not found.
# This ensures the response time is similar whether or not the email exists.
_DUMMY_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$"
    "MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"
)


def authenticate(*, session: Session, email: str, password: str) -> User:
    """
    Authenticate a user by email and password.

    Raises AuthenticationError if credentials are invalid.
    Raises AccountInactiveError if the account is deactivated.
    """
    db_user = user_repo.get_by_email(session=session, email=email)
    if not db_user:
        # Run password verification against a dummy hash to prevent
        # timing attacks that reveal whether an email is registered.
        security.verify_password(password, _DUMMY_HASH)
        raise AuthenticationError("Email ou mot de passe incorrect")

    verified, updated_hash = security.verify_password(
        password, db_user.hashed_password
    )
    if not verified:
        raise AuthenticationError("Email ou mot de passe incorrect")

    if not db_user.is_active:
        raise AccountInactiveError("Compte utilisateur inactif")

    # Upgrade the password hash if the library re-hashed it
    if updated_hash:
        db_user.hashed_password = updated_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

    return db_user


def login(*, session: Session, email: str, password: str) -> Token:
    """
    Authenticate and return an access token.

    Raises AuthenticationError on bad credentials.
    Raises AccountInactiveError on deactivated account.
    """
    user = authenticate(session=session, email=email, password=password)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    permissions = permission_service.get_user_permissions(session=session, user=user)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        permissions=[PermissionPublic.model_validate(p) for p in permissions],
    )


def recover_password(*, session: Session, email: str) -> None:
    """
    Send a password recovery email if the user exists.

    Always returns silently — does not reveal whether the email is registered.
    """
    user = user_repo.get_by_email(session=session, email=email)
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )


def reset_password(*, session: Session, body: NewPassword) -> None:
    """
    Reset a password using a recovery token.

    Raises AuthenticationError if the token is invalid or the user is inactive.
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise AuthenticationError("Jeton invalide")

    user = user_repo.get_by_email(session=session, email=email)
    if not user:
        # Don't reveal that the user doesn't exist
        raise AuthenticationError("Jeton invalide")

    if not user.is_active:
        raise AccountInactiveError("Compte utilisateur inactif")

    hashed = security.get_password_hash(body.new_password)
    user_repo.update(
        session=session,
        db_user=user,
        update_data={},
        extra_data={"hashed_password": hashed},
    )
    session.commit()
    session.refresh(user)
