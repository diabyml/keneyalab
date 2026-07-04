import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.models.lis import NotificationType
from app.services.notification import create_in_app_notification
from tests.utils.utils import random_lower_string

PREFIX = f"{settings.API_V1_STR}/notifications"


def _create_notification(
    *, db: Session, user_id: uuid.UUID, message: str
) -> str:
    notification = create_in_app_notification(
        session=db,
        user_id=user_id,
        type=NotificationType.general,
        message=message,
    )
    db.commit()
    db.refresh(notification)
    return str(notification.id)


def _user_id_by_email(*, db: Session, email: str) -> uuid.UUID:
    return db.exec(select(User.id).where(User.email == email)).one()


def test_current_user_only_sees_own_notifications(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    user_id = _user_id_by_email(db=db, email=settings.FIRST_SUPERUSER)
    other_user_id = _user_id_by_email(db=db, email=settings.EMAIL_TEST_USER)
    own_message = f"Notification personnelle {random_lower_string()}"
    other_message = f"Notification autre {random_lower_string()}"
    _create_notification(db=db, user_id=user_id, message=own_message)
    _create_notification(db=db, user_id=other_user_id, message=other_message)

    response = client.get(f"{PREFIX}/mine", headers=superuser_token_headers)

    assert response.status_code == 200
    messages = [item["message"] for item in response.json()["data"]]
    assert own_message in messages
    assert other_message not in messages
    client.post(f"{PREFIX}/mark-all-read", headers=normal_user_token_headers)


def test_unread_count_ignores_read_notifications(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user_id = _user_id_by_email(db=db, email=settings.EMAIL_TEST_USER)
    notification_id = _create_notification(
        db=db,
        user_id=user_id,
        message=f"À lire {random_lower_string()}",
    )

    unread_response = client.get(
        f"{PREFIX}/unread-count", headers=normal_user_token_headers
    )
    assert unread_response.status_code == 200
    assert unread_response.json()["count"] == 1

    mark_response = client.post(
        f"{PREFIX}/{notification_id}/mark-read", headers=normal_user_token_headers
    )
    assert mark_response.status_code == 200

    read_response = client.get(
        f"{PREFIX}/unread-count", headers=normal_user_token_headers
    )
    assert read_response.status_code == 200
    assert read_response.json()["count"] == 0


def test_mark_read_rejects_other_user_notification(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    other_user_id = _user_id_by_email(db=db, email=settings.EMAIL_TEST_USER)
    notification_id = _create_notification(
        db=db,
        user_id=other_user_id,
        message=f"Privée {random_lower_string()}",
    )

    response = client.post(
        f"{PREFIX}/{notification_id}/mark-read", headers=superuser_token_headers
    )

    assert response.status_code == 404


def test_mark_all_read_updates_only_current_user_notifications(
    client: TestClient,
    db: Session,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
) -> None:
    user_id = _user_id_by_email(db=db, email=settings.FIRST_SUPERUSER)
    other_user_id = _user_id_by_email(db=db, email=settings.EMAIL_TEST_USER)
    client.post(f"{PREFIX}/mark-all-read", headers=superuser_token_headers)
    client.post(f"{PREFIX}/mark-all-read", headers=normal_user_token_headers)
    _create_notification(db=db, user_id=user_id, message=random_lower_string())
    _create_notification(db=db, user_id=user_id, message=random_lower_string())
    _create_notification(db=db, user_id=other_user_id, message=random_lower_string())

    response = client.post(f"{PREFIX}/mark-all-read", headers=superuser_token_headers)

    assert response.status_code == 200
    assert response.json()["count"] == 2
    own_count = client.get(f"{PREFIX}/unread-count", headers=superuser_token_headers)
    other_count = client.get(
        f"{PREFIX}/unread-count", headers=normal_user_token_headers
    )
    assert own_count.json()["count"] == 0
    assert other_count.json()["count"] == 1
