import random
import string

from sqlmodel import Session

from app.models.lis import Unit, UnitCreate
from app.services.unit import create_unit


def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def create_random_unit(db: Session) -> Unit:
    name = random_lower_string()
    unit_in = UnitCreate(name=name)
    return create_unit(session=db, unit_in=unit_in)
