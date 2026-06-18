import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import SessionDep, require_permission
from app.models.lis import (
    AuditAction,
    AuditActorsPublic,
    AuditCategory,
    AuditLogPublic,
    AuditLogsPublic,
    AuditSummaryPublic,
    SortOrder,
)
from app.services import audit as audit_service

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _filters(
    *,
    search: str | None,
    category: AuditCategory | None,
    action: AuditAction | None,
    table_name: str | None,
    record_id: uuid.UUID | None,
    performed_by_id: uuid.UUID | None,
    source: str | None,
    request_id: str | None,
    correlation_id: str | None,
    performed_from: datetime | None,
    performed_to: datetime | None,
) -> dict[str, Any]:
    return audit_service.filters(
        search=search,
        category=category,
        action=action,
        table_name=table_name,
        record_id=record_id,
        performed_by_id=performed_by_id,
        source=source,
        request_id=request_id,
        correlation_id=correlation_id,
        performed_from=performed_from,
        performed_to=performed_to,
    )


@router.get(
    "/",
    dependencies=[Depends(require_permission("audit", "view"))],
    response_model=AuditLogsPublic,
)
def read_audit_logs(
    session: SessionDep,
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    category: AuditCategory | None = None,
    action: AuditAction | None = None,
    table_name: str | None = None,
    record_id: uuid.UUID | None = None,
    performed_by_id: uuid.UUID | None = None,
    source: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    performed_from: datetime | None = None,
    performed_to: datetime | None = None,
    sort_by: str | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    return audit_service.get_logs(
        session=session,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **_filters(
            search=search,
            category=category,
            action=action,
            table_name=table_name,
            record_id=record_id,
            performed_by_id=performed_by_id,
            source=source,
            request_id=request_id,
            correlation_id=correlation_id,
            performed_from=performed_from,
            performed_to=performed_to,
        ),
    )


@router.get(
    "/summary",
    dependencies=[Depends(require_permission("audit", "view"))],
    response_model=AuditSummaryPublic,
)
def read_audit_summary(
    session: SessionDep,
    search: str | None = None,
    category: AuditCategory | None = None,
    action: AuditAction | None = None,
    table_name: str | None = None,
    record_id: uuid.UUID | None = None,
    performed_by_id: uuid.UUID | None = None,
    source: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    performed_from: datetime | None = None,
    performed_to: datetime | None = None,
) -> Any:
    return audit_service.get_summary(
        session=session,
        **_filters(
            search=search,
            category=category,
            action=action,
            table_name=table_name,
            record_id=record_id,
            performed_by_id=performed_by_id,
            source=source,
            request_id=request_id,
            correlation_id=correlation_id,
            performed_from=performed_from,
            performed_to=performed_to,
        ),
    )


@router.get(
    "/actors",
    dependencies=[Depends(require_permission("audit", "view"))],
    response_model=AuditActorsPublic,
)
def read_audit_actors(
    session: SessionDep, search: str | None = None, limit: int = 20
) -> Any:
    return audit_service.get_actors(
        session=session, search=search, limit=min(max(limit, 1), 100)
    )


@router.get(
    "/export",
    dependencies=[Depends(require_permission("audit", "export"))],
)
def export_audit_logs(
    session: SessionDep,
    search: str | None = None,
    category: AuditCategory | None = None,
    action: AuditAction | None = None,
    table_name: str | None = None,
    record_id: uuid.UUID | None = None,
    performed_by_id: uuid.UUID | None = None,
    source: str | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    performed_from: datetime | None = None,
    performed_to: datetime | None = None,
) -> StreamingResponse:
    filters = _filters(
        search=search,
        category=category,
        action=action,
        table_name=table_name,
        record_id=record_id,
        performed_by_id=performed_by_id,
        source=source,
        request_id=request_id,
        correlation_id=correlation_id,
        performed_from=performed_from,
        performed_to=performed_to,
    )
    total = audit_service.validate_export(session=session, **filters)
    rows = audit_service.export_csv(
        session=session,
        total=total,
        **filters,
    )
    return StreamingResponse(
        rows,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="journal-audit.csv"'
        },
    )


@router.get(
    "/{audit_id}",
    dependencies=[Depends(require_permission("audit", "view"))],
    response_model=AuditLogPublic,
)
def read_audit_log(session: SessionDep, audit_id: uuid.UUID) -> Any:
    return audit_service.get_log(session=session, audit_id=audit_id)
