import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_any_permission, require_permission
from app.models import (
    InsuranceProviderCreate,
    InsuranceProviderPublic,
    InsuranceProvidersPublic,
    InsuranceProviderUpdate,
    Message,
    SortOrder,
)
from app.services import insurance_provider as ip_service

router = APIRouter(prefix="/insurance-providers", tags=["insurance-providers"])


@router.get(
    "/",
    dependencies=[
        Depends(
            require_any_permission(
                ("reference_data", "manage"),
                ("finance", "manage"),
                ("patient_insurance", "create"),
                ("patient_insurance", "view"),
            )
        )
    ],
    response_model=InsuranceProvidersPublic,
)
def read_insurance_providers(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> Any:
    items, count = ip_service.get_insurance_providers(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return InsuranceProvidersPublic(
        data=[InsuranceProviderPublic.model_validate(i) for i in items], count=count
    )


@router.get(
    "/{id}",
    dependencies=[
        Depends(
            require_any_permission(
                ("reference_data", "manage"),
                ("finance", "manage"),
            )
        )
    ],
    response_model=InsuranceProviderPublic,
)
def read_insurance_provider(session: SessionDep, id: uuid.UUID) -> Any:
    return ip_service.get_insurance_provider(session=session, ip_id=id)


@router.post(
    "/",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=InsuranceProviderPublic,
)
def create_insurance_provider(
    *, session: SessionDep, ip_in: InsuranceProviderCreate
) -> Any:
    return ip_service.create_insurance_provider(session=session, ip_in=ip_in)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=InsuranceProviderPublic,
)
def update_insurance_provider(
    *, session: SessionDep, id: uuid.UUID, ip_in: InsuranceProviderUpdate
) -> Any:
    return ip_service.update_insurance_provider(session=session, ip_id=id, ip_in=ip_in)


@router.delete(
    "/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))]
)
def delete_insurance_provider(session: SessionDep, id: uuid.UUID) -> Message:
    ip_service.delete_insurance_provider(session=session, ip_id=id)
    return Message(message="Assureur supprimé avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=InsuranceProviderPublic,
)
def restore_insurance_provider(session: SessionDep, id: uuid.UUID) -> Any:
    return ip_service.restore_insurance_provider(session=session, ip_id=id)
