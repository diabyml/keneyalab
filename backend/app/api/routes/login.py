from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import Message, NewPassword, Token, UserPublic
from app.repositories import user as user_repo
from app.services import auth as auth_service
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
)

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """OAuth2 compatible token login, get an access token for future requests."""
    return auth_service.login(
        session=session, email=form_data.username, password=form_data.password
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """Test access token."""
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """Password Recovery — always returns success to prevent email enumeration."""
    auth_service.recover_password(session=session, email=email)
    return Message(
        message="Si cet email est enregistré, un lien de récupération a été envoyé"
    )


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """Reset password."""
    auth_service.reset_password(session=session, body=body)
    return Message(message="Mot de passe mis à jour avec succès")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """HTML Content for Password Recovery (admin only)."""
    user = user_repo.get_by_email(session=session, email=email)
    if not user:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Aucun utilisateur trouvé avec cet email",
        )

    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )
