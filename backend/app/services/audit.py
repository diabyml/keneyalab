"""Audit explorer business logic and export."""

import csv
import io
import json
import uuid
from collections.abc import Iterator
from datetime import datetime
from typing import Any

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.lis import (
    AuditAction,
    AuditActorPublic,
    AuditActorsPublic,
    AuditCategory,
    AuditLog,
    AuditLogPublic,
    AuditLogsPublic,
    AuditSummaryPublic,
    SortOrder,
)
from app.repositories import audit as audit_repo

EXPORT_LIMIT = 100_000
EXPORT_BATCH_SIZE = 1_000


def _public(row: AuditLog) -> AuditLogPublic:
    return AuditLogPublic(
        id=row.id,
        table_name=row.table_name,
        record_id=row.record_id,
        action=row.action,
        category=row.category,
        record_label=row.record_label,
        old_values=row.old_values,
        new_values=row.new_values,
        audit_metadata=row.metadata_json,
        performed_by_id=row.performed_by_id,
        actor_name=row.actor_name,
        actor_email=row.actor_email,
        request_id=row.request_id,
        correlation_id=row.correlation_id,
        source=row.source,
        ip_address=row.ip_address,
        user_agent=row.user_agent,
        http_method=row.http_method,
        http_path=row.http_path,
        performed_at=row.performed_at,
        created_at=row.created_at,
    )


def get_logs(
    *,
    session: Session,
    skip: int,
    limit: int,
    sort_by: str | None,
    sort_order: SortOrder,
    **filters: Any,
) -> AuditLogsPublic:
    rows, count = audit_repo.get_all(
        session=session,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
        **filters,
    )
    return AuditLogsPublic(data=[_public(row) for row in rows], count=count)


def get_log(*, session: Session, audit_id: uuid.UUID) -> AuditLogPublic:
    row = audit_repo.get_by_id(session=session, audit_id=audit_id)
    if row is None:
        raise NotFoundError("Événement d'audit introuvable")
    return _public(row)


def get_summary(*, session: Session, **filters: Any) -> AuditSummaryPublic:
    row = audit_repo.get_summary(session=session, **filters)
    return AuditSummaryPublic(
        total=row.total,
        inserts=row.inserts,
        updates=row.updates,
        deletes=row.deletes,
        security_events=row.security_events,
    )


def get_actors(
    *, session: Session, search: str | None, limit: int
) -> AuditActorsPublic:
    return AuditActorsPublic(
        data=[
            AuditActorPublic(id=actor_id, name=name, email=email)
            for actor_id, name, email in audit_repo.get_actors(
                session=session, search=search, limit=limit
            )
        ]
    )


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True) if value else ""


def validate_export(*, session: Session, **filters: Any) -> int:
    summary = audit_repo.get_summary(session=session, **filters)
    if summary.total > EXPORT_LIMIT:
        raise BusinessRuleError(
            "L'export dépasse 100 000 événements. Veuillez affiner les filtres."
        )
    return int(summary.total)


def export_csv(
    *, session: Session, total: int, **filters: Any
) -> Iterator[str]:

    headers = [
        "Date",
        "Catégorie",
        "Action",
        "Entité",
        "Libellé",
        "Identifiant",
        "Acteur",
        "Email acteur",
        "Source",
        "Adresse IP",
        "Méthode",
        "Chemin",
        "ID requête",
        "ID corrélation",
        "Anciennes valeurs",
        "Nouvelles valeurs",
        "Métadonnées",
    ]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    yield "\ufeff" + buffer.getvalue()

    offset = 0
    while offset < total:
        rows, _ = audit_repo.get_all(
            session=session,
            skip=offset,
            limit=EXPORT_BATCH_SIZE,
            sort_by="performed_at",
            sort_order=SortOrder.desc,
            **filters,
        )
        if not rows:
            break
        for row in rows:
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(
                [
                    row.performed_at.isoformat(),
                    row.category.value,
                    row.action.value,
                    row.table_name,
                    row.record_label or "",
                    str(row.record_id or ""),
                    row.actor_name or "",
                    row.actor_email or "",
                    row.source,
                    row.ip_address or "",
                    row.http_method or "",
                    row.http_path or "",
                    row.request_id or "",
                    row.correlation_id or "",
                    _json(row.old_values),
                    _json(row.new_values),
                    _json(row.metadata_json),
                ]
            )
            yield buffer.getvalue()
        offset += len(rows)


def filters(
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
    return {
        "search": search,
        "category": category,
        "action": action,
        "table_name": table_name,
        "record_id": record_id,
        "performed_by_id": performed_by_id,
        "source": source,
        "request_id": request_id,
        "correlation_id": correlation_id,
        "performed_from": performed_from,
        "performed_to": performed_to,
    }
