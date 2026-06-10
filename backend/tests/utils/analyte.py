import random
import string

from sqlmodel import Session

from app.models.lis import Analyte, AnalyteCreate, AnalyteDataType
from app.services.analyte import create_analyte


def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def create_random_analyte(
    db: Session, data_type: AnalyteDataType = AnalyteDataType.numeric
) -> Analyte:
    code = random_lower_string(8).upper()
    analyte_in = AnalyteCreate(
        code=code,
        name=f"Analyte {code}",
        data_type=data_type,
        options_data=["Positif", "Négatif"] if data_type == AnalyteDataType.options else None,
    )
    return create_analyte(session=db, analyte_in=analyte_in)
