import random, string
from sqlmodel import Session
from app.models.lis import SpecimenType, SpecimenTypeCreate
from app.services.specimen_type import create_specimen_type

def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def create_random_specimen_type(db: Session) -> SpecimenType:
    return create_specimen_type(session=db, st_in=SpecimenTypeCreate(name=random_lower_string(), color="#ff0000"))
