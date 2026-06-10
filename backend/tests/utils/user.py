from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import User, UserCreate, UserUpdate
from app.repositories import user as user_repo
from app.services.user import create_user, update_user
from tests.utils.utils import random_email, random_lower_string


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    return create_user(session=db, user_in=user_in)


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_lower_string()
    user = user_repo.get_by_email(session=db, email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=password)
        user = create_user(session=db, user_in=user_in_create)
    else:
        from app.core.security import get_password_hash

        user_repo.update(
            session=db,
            db_user=user,
            update_data={},
            extra_data={"hashed_password": get_password_hash(password)},
        )
        db.commit()
        db.refresh(user)

    return user_authentication_headers(client=client, email=email, password=password)
