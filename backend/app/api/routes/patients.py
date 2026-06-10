import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_permission
from app.models import (
    GenderType,
    Message,
    PatientCreate,
    PatientInsuranceCreate,
    PatientInsurancesPublic,
    PatientInsuranceUpdate,
    PatientInsuranceWithProviderPublic,
    PatientPublic,
    PatientsPublic,
    PatientUpdate,
    SortOrder,
)
from app.services import patient as patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


def _insurance_public(row: tuple[Any, Any]) -> PatientInsuranceWithProviderPublic:
    insurance, provider = row
    return PatientInsuranceWithProviderPublic(
        **insurance.model_dump(),
        insurance_provider_name=provider.name,
    )


@router.get(
    "/",
    dependencies=[Depends(require_permission("patients", "view"))],
    response_model=PatientsPublic,
)
def read_patients(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    gender: GenderType | None = None,
    doctor_id: uuid.UUID | None = None,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> Any:
    items, count = patient_service.get_patients(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        gender=gender,
        doctor_id=doctor_id,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PatientsPublic(
        data=[PatientPublic.model_validate(item) for item in items], count=count
    )


@router.post(
    "/",
    dependencies=[Depends(require_permission("patients", "create"))],
    response_model=PatientPublic,
)
def create_patient(*, session: SessionDep, patient_in: PatientCreate) -> Any:
    return patient_service.create_patient(session=session, patient_in=patient_in)


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("patients", "view"))],
    response_model=PatientPublic,
)
def read_patient(session: SessionDep, id: uuid.UUID) -> Any:
    return patient_service.get_patient(session=session, patient_id=id)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("patients", "edit"))],
    response_model=PatientPublic,
)
def update_patient(
    *, session: SessionDep, id: uuid.UUID, patient_in: PatientUpdate
) -> Any:
    return patient_service.update_patient(
        session=session, patient_id=id, patient_in=patient_in
    )


@router.delete(
    "/{id}",
    dependencies=[Depends(require_permission("patients", "delete"))],
)
def delete_patient(session: SessionDep, id: uuid.UUID) -> Message:
    patient_service.delete_patient(session=session, patient_id=id)
    return Message(message="Patient supprimé avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("patients", "delete"))],
    response_model=PatientPublic,
)
def restore_patient(session: SessionDep, id: uuid.UUID) -> Any:
    return patient_service.restore_patient(session=session, patient_id=id)


@router.get(
    "/{id}/insurance",
    dependencies=[Depends(require_permission("patient_insurance", "view"))],
    response_model=PatientInsurancesPublic,
)
def read_patient_insurances(
    session: SessionDep,
    id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> Any:
    items, count = patient_service.get_patient_insurances(
        session=session,
        patient_id=id,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PatientInsurancesPublic(
        data=[_insurance_public(item) for item in items], count=count
    )


@router.post(
    "/{id}/insurance",
    dependencies=[Depends(require_permission("patient_insurance", "create"))],
    response_model=PatientInsuranceWithProviderPublic,
)
def create_patient_insurance(
    *,
    session: SessionDep,
    id: uuid.UUID,
    insurance_in: PatientInsuranceCreate,
) -> Any:
    insurance = patient_service.create_patient_insurance(
        session=session, patient_id=id, insurance_in=insurance_in
    )
    return _insurance_public(
        patient_service.get_patient_insurance_with_provider(
            session=session, patient_id=id, insurance_id=insurance.id
        )
    )


@router.put(
    "/{id}/insurance/{insurance_id}",
    dependencies=[Depends(require_permission("patient_insurance", "edit"))],
    response_model=PatientInsuranceWithProviderPublic,
)
def update_patient_insurance(
    *,
    session: SessionDep,
    id: uuid.UUID,
    insurance_id: uuid.UUID,
    insurance_in: PatientInsuranceUpdate,
) -> Any:
    insurance = patient_service.update_patient_insurance(
        session=session,
        patient_id=id,
        insurance_id=insurance_id,
        insurance_in=insurance_in,
    )
    return _insurance_public(
        patient_service.get_patient_insurance_with_provider(
            session=session, patient_id=id, insurance_id=insurance.id
        )
    )


@router.delete(
    "/{id}/insurance/{insurance_id}",
    dependencies=[Depends(require_permission("patient_insurance", "edit"))],
)
def delete_patient_insurance(
    session: SessionDep,
    id: uuid.UUID,
    insurance_id: uuid.UUID,
) -> Message:
    patient_service.delete_patient_insurance(
        session=session, patient_id=id, insurance_id=insurance_id
    )
    return Message(message="Assurance patient supprimée avec succès")


@router.post(
    "/{id}/insurance/{insurance_id}/restore",
    dependencies=[Depends(require_permission("patient_insurance", "edit"))],
    response_model=PatientInsuranceWithProviderPublic,
)
def restore_patient_insurance(
    session: SessionDep,
    id: uuid.UUID,
    insurance_id: uuid.UUID,
) -> Any:
    insurance = patient_service.restore_patient_insurance(
        session=session, patient_id=id, insurance_id=insurance_id
    )
    return _insurance_public(
        patient_service.get_patient_insurance_with_provider(
            session=session, patient_id=id, insurance_id=insurance.id
        )
    )
