import random, string
from sqlmodel import Session
from app.models.lis import InsuranceProvider, InsuranceProviderCreate
from app.services.insurance_provider import create_insurance_provider

def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))

def create_random_insurance_provider(db: Session) -> InsuranceProvider:
    return create_insurance_provider(session=db, ip_in=InsuranceProviderCreate(name=random_lower_string()))
