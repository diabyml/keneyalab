from datetime import datetime, timezone

from sqlmodel import SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Generic message
class Message(SQLModel):
    message: str
