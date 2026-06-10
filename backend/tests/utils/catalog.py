import random
import string
from decimal import Decimal

from sqlmodel import Session

from app.models.lis import Catalog, CatalogCreate, CatalogType
from app.services.catalog import create_catalog


def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def create_random_catalog(
    db: Session,
    type: CatalogType = CatalogType.item,
    price: Decimal | None = None,
) -> Catalog:
    code = random_lower_string(8).upper()
    catalog_price = price
    if catalog_price is None:
        catalog_price = Decimal("0.00") if type == CatalogType.panel else Decimal("1000.00")
    catalog_in = CatalogCreate(
        type=type,
        code=code,
        name=f"Catalogue {code}",
        price=catalog_price,
        is_orderable=True,
    )
    return create_catalog(session=db, catalog_in=catalog_in)
