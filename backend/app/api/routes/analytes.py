import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_permission
from app.models import (
    AnalyteCreate,
    AnalyteDataType,
    AnalytePublic,
    AnalytesPublic,
    AnalyteUpdate,
    Message,
)
from app.services import analyte as analyte_service

router = APIRouter(prefix="/analytes", tags=["analytes"])


@router.get(
    "/",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=AnalytesPublic,
)
def read_analytes(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
    is_deleted: bool | None = None,
    search: str | None = None,
    data_type: AnalyteDataType | None = None,
    is_calculated: bool | None = None,
) -> Any:
    """Retrieve analytes. Excludes soft-deleted records by default."""
    items, count = analyte_service.get_analytes(
        session=session,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
        is_deleted=is_deleted,
        search=search,
        data_type=data_type,
        is_calculated=is_calculated,
    )
    return AnalytesPublic(
        data=[AnalytePublic.model_validate(item) for item in items],
        count=count,
    )


@router.get(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=AnalytePublic,
)
def read_analyte(session: SessionDep, id: uuid.UUID) -> Any:
    """Get an analyte by ID."""
    return analyte_service.get_analyte(session=session, analyte_id=id)


@router.post(
    "/",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=AnalytePublic,
)
def create_analyte(
    *, session: SessionDep, analyte_in: AnalyteCreate
) -> Any:
    """Create a new analyte."""
    return analyte_service.create_analyte(session=session, analyte_in=analyte_in)


@router.put(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=AnalytePublic,
)
def update_analyte(
    *,
    session: SessionDep,
    id: uuid.UUID,
    analyte_in: AnalyteUpdate,
) -> Any:
    """Update an analyte."""
    return analyte_service.update_analyte(
        session=session, analyte_id=id, analyte_in=analyte_in
    )


@router.delete(
    "/{id}",
    dependencies=[Depends(require_permission("catalog", "manage"))],
)
def delete_analyte(session: SessionDep, id: uuid.UUID) -> Message:
    """Soft-delete an analyte."""
    analyte_service.delete_analyte(session=session, analyte_id=id)
    return Message(message="Analyte supprimé avec succès")


@router.post(
    "/{id}/restore",
    dependencies=[Depends(require_permission("catalog", "manage"))],
    response_model=AnalytePublic,
)
def restore_analyte(session: SessionDep, id: uuid.UUID) -> Any:
    """Restore a soft-deleted analyte."""
    return analyte_service.restore_analyte(session=session, analyte_id=id)
