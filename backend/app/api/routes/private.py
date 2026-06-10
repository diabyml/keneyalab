from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.security import get_password_hash
from app.models import (
    User,
    UserPublic,
)
from app.services.permission import assign_default_roles

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    # Assign default roles so the user has baseline permissions
    superuser = session.exec(
        select(User).where(User.is_superuser == True)
    ).first()
    if superuser:
        assign_default_roles(session=session, user=user, assigned_by=superuser)

    return user
