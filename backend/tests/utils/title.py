import random
import string

from sqlmodel import Session

from app.models.lis import Title, TitleCreate
from app.services.title import create_title


def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def create_random_title(db: Session) -> Title:
    name = random_lower_string()
    title_in = TitleCreate(name=name)
    return create_title(session=db, title_in=title_in)
