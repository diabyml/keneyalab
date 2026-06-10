import random, string
from sqlmodel import Session
from app.models.lis import PaymentMethod, PaymentMethodCreate
from app.services.payment_method import create_payment_method

def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def create_random_payment_method(db: Session) -> PaymentMethod:
    return create_payment_method(session=db, pm_in=PaymentMethodCreate(name=random_lower_string()))
