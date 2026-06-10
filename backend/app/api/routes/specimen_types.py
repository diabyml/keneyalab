import uuid
from typing import Any
from fastapi import APIRouter, Depends
from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import Message, SpecimenTypeCreate, SpecimenTypePublic, SpecimenTypesPublic, SpecimenTypeUpdate
from app.services import specimen_type as st_service

router = APIRouter(prefix="/specimen-types", tags=["specimen-types"])


@router.get("/", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=SpecimenTypesPublic)
def read_specimen_types(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    search: str | None = None,
) -> Any:
    items, count = st_service.get_specimen_types(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        search=search,
    )
    return SpecimenTypesPublic(data=[SpecimenTypePublic.model_validate(i) for i in items], count=count)


@router.get("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=SpecimenTypePublic)
def read_specimen_type(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return st_service.get_specimen_type(session=session, st_id=id)


@router.post("/", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=SpecimenTypePublic)
def create_specimen_type(*, session: SessionDep, current_user: CurrentUser, st_in: SpecimenTypeCreate) -> Any:
    return st_service.create_specimen_type(session=session, st_in=st_in)


@router.put("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=SpecimenTypePublic)
def update_specimen_type(*, session: SessionDep, current_user: CurrentUser, id: uuid.UUID, st_in: SpecimenTypeUpdate) -> Any:
    return st_service.update_specimen_type(session=session, st_id=id, st_in=st_in)


@router.delete("/{id}", dependencies=[Depends(require_permission("reference_data", "manage"))])
def delete_specimen_type(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Message:
    st_service.delete_specimen_type(session=session, st_id=id)
    return Message(message="Type de prélèvement supprimé avec succès")


@router.post("/{id}/restore", dependencies=[Depends(require_permission("reference_data", "manage"))], response_model=SpecimenTypePublic)
def restore_specimen_type(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    return st_service.restore_specimen_type(session=session, st_id=id)
