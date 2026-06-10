import random
import string

from sqlmodel import Session

from app.models.lis import Category, CategoryCreate
from app.services.category import create_category


def random_lower_string(length: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=length))


def create_random_category(db: Session, sort_order: int = 0) -> Category:
    category_in = CategoryCreate(name=random_lower_string(), sort_order=sort_order)
    return create_category(session=db, category_in=category_in)
