import random, string
from sqlmodel import Session
from app.models.lis import RejectionReason, RejectionReasonCreate
from app.services.rejection_reason import create_rejection_reason

def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def create_random_rejection_reason(db: Session) -> RejectionReason:
    return create_rejection_reason(session=db, rr_in=RejectionReasonCreate(name=random_lower_string()))
