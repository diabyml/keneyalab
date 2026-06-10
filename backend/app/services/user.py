"""User business logic — creation, updates, password management."""

import uuid

from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import (
    BusinessRuleError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.user import User, UserCreate, UserUpdate, UserUpdateMe
from app.repositories import user as user_repo
from app.services.permission import assign_default_roles, check_permission
from app.utils import generate_new_account_email, send_email


def create_user(*, session: Session, user_in: UserCreate, assigned_by: User | None = None) -> User:
    """Create a new user. If assigned_by is provided, default roles are assigned.
    Raises ConflictError if email is already taken."""
    if user_in.is_superuser and assigned_by is not None and not assigned_by.is_superuser:
        raise ForbiddenError("L'utilisateur ne dispose pas de privilèges suffisants")

    existing = user_repo.get_by_email(session=session, email=user_in.email)
    if existing:
        raise ConflictError("Un utilisateur avec cet email existe déjà dans le système.")

    hashed = security.get_password_hash(user_in.password)
    db_user = User.model_validate(user_in, update={"hashed_password": hashed})
    user_repo.create(session=session, db_obj=db_user)
    session.commit()
    session.refresh(db_user)

    # Assign default roles (e.g., receptionist) to the new user
    if assigned_by is not None:
        assign_default_roles(session=session, user=db_user, assigned_by=assigned_by)

    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email,
            username=user_in.email,
            password=user_in.password,
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )

    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Look up a user by email. Returns None if not found."""
    return user_repo.get_by_email(session=session, email=email)


def get_users(*, session: Session, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
    """Return all users (admin only — authorization enforced in route decorator)."""
    return user_repo.get_all(session=session, skip=skip, limit=limit)


def get_user(*, session: Session, user_id: uuid.UUID, current_user: User) -> User:
    """
    Get a user by ID. The current user can read themselves;
    otherwise users:manage permission is required.

    Non-superusers always get a permission error first — the existence
    of other users is not revealed.
    """
    db_user = user_repo.get_by_id(session=session, user_id=user_id)

    if db_user == current_user:
        return db_user

    if not check_permission(
        session=session, user=current_user, resource="users", action="manage"
    ):
        raise ForbiddenError("L'utilisateur ne dispose pas de privilèges suffisants")

    if db_user is None:
        raise NotFoundError("Utilisateur non trouvé")
    return db_user


def update_me(*, session: Session, current_user: User, user_in: UserUpdateMe) -> User:
    """Update the current user's own profile."""
    if user_in.email:
        existing = user_repo.get_by_email(session=session, email=user_in.email)
        if existing and existing.id != current_user.id:
            raise ConflictError("Un utilisateur avec cet email existe déjà")

    user_data = user_in.model_dump(exclude_unset=True)
    user_repo.update(session=session, db_user=current_user, update_data=user_data)
    session.commit()
    session.refresh(current_user)
    return current_user


def update_password_me(
    *, session: Session, current_user: User, current_password: str, new_password: str
) -> None:
    """Update the current user's password."""
    verified, _ = security.verify_password(current_password, current_user.hashed_password)
    if not verified:
        raise BusinessRuleError("Mot de passe incorrect")

    if current_password == new_password:
        raise BusinessRuleError("Le nouveau mot de passe ne peut pas être identique à l'actuel")

    hashed = security.get_password_hash(new_password)
    user_repo.update(
        session=session,
        db_user=current_user,
        update_data={},
        extra_data={"hashed_password": hashed},
    )
    session.commit()


def update_user(
    *, session: Session, current_user: User, user_id: uuid.UUID, user_in: UserUpdate
) -> User:
    """Admin update of any user."""
    db_user = user_repo.get_by_id(session=session, user_id=user_id)
    if db_user is None:
        raise NotFoundError("L'utilisateur avec cet identifiant n'existe pas dans le système")

    if user_in.email:
        existing = user_repo.get_by_email(session=session, email=user_in.email)
        if existing and existing.id != user_id:
            raise ConflictError("Un utilisateur avec cet email existe déjà")

    user_data = user_in.model_dump(exclude_unset=True)
    if "is_superuser" in user_data and not current_user.is_superuser:
        raise ForbiddenError("L'utilisateur ne dispose pas de privilèges suffisants")

    extra_data = {}
    if "password" in user_data:
        hashed = security.get_password_hash(user_data.pop("password"))
        extra_data["hashed_password"] = hashed

    user_repo.update(
        session=session, db_user=db_user, update_data=user_data, extra_data=extra_data
    )
    session.commit()
    session.refresh(db_user)
    return db_user
