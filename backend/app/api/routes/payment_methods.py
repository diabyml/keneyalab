import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    Message,
    PaymentMethodCreate,
    PaymentMethodPublic,
    PaymentMethodsPublic,
    PaymentMethodUpdate,
)
from app.services import payment_method as pm_service

router = APIRouter(prefix="/payment-methods", tags=["payment-methods"])


@router.get("/", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=PaymentMethodsPublic)
def read_payment_methods(session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> Any:
    items, count = pm_service.get_payment_methods(session=session, skip=skip, limit=limit, include_deleted=include_deleted)
    return PaymentMethodsPublic(data=[PaymentMethodPublic.model_validate(i) for i in items], count=count)


@router.get("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=PaymentMethodPublic)
def read_payment_method(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return pm_service.get_payment_method(session=session, pm_id=id)


@router.post("/", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=PaymentMethodPublic)
def create_payment_method(*, session: SessionDep, current_user: CurrentUser, pm_in: PaymentMethodCreate) -> Any:
    return pm_service.create_payment_method(session=session, pm_in=pm_in)


@router.put("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=PaymentMethodPublic)
def update_payment_method(*, session: SessionDep, current_user: CurrentUser, id: uuid.UUID, pm_in: PaymentMethodUpdate) -> Any:
    return pm_service.update_payment_method(session=session, pm_id=id, pm_in=pm_in)


@router.delete("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))])
def delete_payment_method(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Message:
    pm_service.delete_payment_method(session=session, pm_id=id)
    return Message(message="Méthode de paiement supprimée avec succès")


@router.post("/{id}/restore", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=PaymentMethodPublic)
def restore_payment_method(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return pm_service.restore_payment_method(session=session, pm_id=id)
