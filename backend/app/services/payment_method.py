"""PaymentMethod business logic — CRUD for reference data."""

import uuid

from sqlmodel import Session

from app.core.exceptions import NotFoundError
from app.models.lis import PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate
from app.repositories import payment_method as pm_repo


def create_payment_method(*, session: Session, pm_in: PaymentMethodCreate) -> PaymentMethod:
    db_obj = PaymentMethod.model_validate(pm_in)
    pm_repo.create(session=session, db_obj=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_payment_methods(*, session: Session, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> tuple[list[PaymentMethod], int]:
    return pm_repo.get_all(session=session, skip=skip, limit=limit, include_deleted=include_deleted)


def get_payment_method(*, session: Session, pm_id: uuid.UUID) -> PaymentMethod:
    db_obj = pm_repo.get_by_id(session=session, pm_id=pm_id)
    if db_obj is None:
        raise NotFoundError("Méthode de paiement non trouvée")
    return db_obj


def update_payment_method(*, session: Session, pm_id: uuid.UUID, pm_in: PaymentMethodUpdate) -> PaymentMethod:
    db_obj = pm_repo.get_by_id(session=session, pm_id=pm_id)
    if db_obj is None:
        raise NotFoundError("Méthode de paiement non trouvée")
    pm_repo.update(session=session, db_obj=db_obj, update_data=pm_in.model_dump(exclude_unset=True))
    session.commit()
    session.refresh(db_obj)
    return db_obj


def delete_payment_method(*, session: Session, pm_id: uuid.UUID) -> None:
    db_obj = pm_repo.get_by_id(session=session, pm_id=pm_id)
    if db_obj is None:
        raise NotFoundError("Méthode de paiement non trouvée")
    pm_repo.soft_delete(session=session, db_obj=db_obj)
    session.commit()


def restore_payment_method(*, session: Session, pm_id: uuid.UUID) -> PaymentMethod:
    db_obj = pm_repo.get_by_id(session=session, pm_id=pm_id)
    if db_obj is None:
        raise NotFoundError("Méthode de paiement non trouvée")
    pm_repo.update(session=session, db_obj=db_obj, update_data={"is_deleted": False})
    session.commit()
    session.refresh(db_obj)
    return db_obj
