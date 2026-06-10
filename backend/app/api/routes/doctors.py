import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_permission
from app.models import (
    DoctorCommissionConfigCreate,
    DoctorCommissionConfigPublic,
    DoctorCommissionConfigsPublic,
    DoctorCommissionConfigUpdate,
    DoctorCreate,
    DoctorsPublic,
    DoctorUpdate,
    DoctorWithTitlePublic,
    Message,
    SortOrder,
)
from app.services import doctor as doctor_service

router = APIRouter(prefix="/doctors", tags=["doctors"])
commission_router = APIRouter(
    prefix="/doctor-commission-configs",
    tags=["doctor-commission-configs"],
)


def _doctor_public(row: tuple[Any, Any]) -> DoctorWithTitlePublic:
    doctor, title = row
    return DoctorWithTitlePublic(
        **doctor.model_dump(),
        title_name=title.name if title else None,
    )


@router.get(
    "/",
    dependencies=[Depends(require_permission("doctors", "view"))],
    response_model=DoctorsPublic,
)
def read_doctors(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    title_id: uuid.UUID | None = None,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.asc,
) -> Any:
    rows, count = doctor_service.get_doctors(
        session=session,
        skip=skip,
        limit=limit,
        search=search,
        title_id=title_id,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return DoctorsPublic(data=[_doctor_public(row) for row in rows], count=count)


@router.post(
    "/",
    dependencies=[Depends(require_permission("doctors", "create"))],
    response_model=DoctorWithTitlePublic,
)
def create_doctor(*, session: SessionDep, doctor_in: DoctorCreate) -> Any:
    doctor = doctor_service.create_doctor(session=session, doctor_in=doctor_in)
    return _doctor_public(
        doctor_service.get_doctor_with_title(session=session, doctor_id=doctor.id)
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("doctors", "view"))],
    response_model=DoctorWithTitlePublic,
)
def read_doctor(session: SessionDep, id: uuid.UUID) -> Any:
    return _doctor_public(
        doctor_service.get_doctor_with_title(session=session, doctor_id=id)
    )


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("doctors", "edit"))],
    response_model=DoctorWithTitlePublic,
)
def update_doctor(
    *, session: SessionDep, id: uuid.UUID, doctor_in: DoctorUpdate
) -> Any:
    doctor = doctor_service.update_doctor(
        session=session, doctor_id=id, doctor_in=doctor_in
    )
    return _doctor_public(
        doctor_service.get_doctor_with_title(session=session, doctor_id=doctor.id)
    )


@router.delete(
    "/{id}",
    dependencies=[Depends(require_permission("doctors", "delete"))],
)
def delete_doctor(session: SessionDep, id: uuid.UUID) -> Message:
    doctor_service.delete_doctor(session=session, doctor_id=id)
    return Message(message="Médecin supprimé avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("doctors", "delete"))],
    response_model=DoctorWithTitlePublic,
)
def restore_doctor(session: SessionDep, id: uuid.UUID) -> Any:
    doctor = doctor_service.restore_doctor(session=session, doctor_id=id)
    return _doctor_public(
        doctor_service.get_doctor_with_title(session=session, doctor_id=doctor.id)
    )


@router.get(
    "/{id}/commission-configs",
    dependencies=[Depends(require_permission("commissions", "manage_config"))],
    response_model=DoctorCommissionConfigsPublic,
)
def read_doctor_commission_configs(
    session: SessionDep,
    id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    items, count = doctor_service.get_commission_configs(
        session=session,
        doctor_id=id,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return DoctorCommissionConfigsPublic(
        data=[DoctorCommissionConfigPublic.model_validate(item) for item in items],
        count=count,
    )


@router.post(
    "/{id}/commission-configs",
    dependencies=[Depends(require_permission("commissions", "manage_config"))],
    response_model=DoctorCommissionConfigPublic,
)
def create_doctor_commission_config(
    *,
    session: SessionDep,
    id: uuid.UUID,
    config_in: DoctorCommissionConfigCreate,
) -> Any:
    return doctor_service.create_commission_config(
        session=session,
        doctor_id=id,
        config_in=config_in,
    )


@commission_router.put(
    "/{id}",
    dependencies=[Depends(require_permission("commissions", "manage_config"))],
    response_model=DoctorCommissionConfigPublic,
)
def update_doctor_commission_config(
    *,
    session: SessionDep,
    id: uuid.UUID,
    config_in: DoctorCommissionConfigUpdate,
) -> Any:
    return doctor_service.update_commission_config(
        session=session,
        config_id=id,
        config_in=config_in,
    )
