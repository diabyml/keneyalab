import random, string
from sqlmodel import Session
from app.models.lis import PatientContext, PatientContextCreate
from app.services.patient_context import create_patient_context

def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def create_random_patient_context(db: Session) -> PatientContext:
    return create_patient_context(session=db, pc_in=PatientContextCreate(name=random_lower_string()))
