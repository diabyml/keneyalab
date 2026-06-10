import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_any_permission, require_permission
from app.models import (
    Message,
    PatientContextCreate,
    PatientContextPublic,
    PatientContextsPublic,
    PatientContextUpdate,
)
from app.services import patient_context as pc_service

router = APIRouter(prefix="/patient-contexts", tags=["patient-contexts"])


@router.get(
    "/",
    dependencies=[
        Depends(
            require_any_permission(
                ("reference_data", "manage"),
                ("orders", "create"),
            )
        )
    ],
    response_model=PatientContextsPublic,
)
def read_patient_contexts(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> Any:
    items, count = pc_service.get_patient_contexts(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search,
    )
    return PatientContextsPublic(
        data=[PatientContextPublic.model_validate(i) for i in items], count=count
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=PatientContextPublic,
)
def read_patient_context(session: SessionDep, id: uuid.UUID) -> Any:
    return pc_service.get_patient_context(session=session, pc_id=id)


@router.post(
    "/",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=PatientContextPublic,
)
def create_patient_context(*, session: SessionDep, pc_in: PatientContextCreate) -> Any:
    return pc_service.create_patient_context(session=session, pc_in=pc_in)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=PatientContextPublic,
)
def update_patient_context(
    *,
    session: SessionDep,
    id: uuid.UUID,
    pc_in: PatientContextUpdate,
) -> Any:
    return pc_service.update_patient_context(session=session, pc_id=id, pc_in=pc_in)


@router.delete(
    "/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))]
)
def delete_patient_context(session: SessionDep, id: uuid.UUID) -> Message:
    pc_service.delete_patient_context(session=session, pc_id=id)
    return Message(message="Contexte patient supprimé avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("reference_data", "manage"))],
    response_model=PatientContextPublic,
)
def restore_patient_context(session: SessionDep, id: uuid.UUID) -> Any:
    return pc_service.restore_patient_context(session=session, pc_id=id)
