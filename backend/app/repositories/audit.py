"""Audit log database access."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, case, cast
from sqlalchemy import select as sa_select
from sqlmodel import Session, col, func, or_, select

from app.models.lis import AuditAction, AuditCategory, AuditLog, SortOrder


def _conditions(
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
) -> list[Any]:
    conditions: list[Any] = []
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(AuditLog.table_name).ilike(query),
                col(AuditLog.record_label).ilike(query),
                col(AuditLog.actor_name).ilike(query),
                col(AuditLog.actor_email).ilike(query),
                col(AuditLog.request_id).ilike(query),
                col(AuditLog.correlation_id).ilike(query),
                cast(AuditLog.old_values, String).ilike(query),
                cast(AuditLog.new_values, String).ilike(query),
                cast(AuditLog.metadata_json, String).ilike(query),
            )
        )
    if category is not None:
        conditions.append(col(AuditLog.category) == category)
    if action is not None:
        conditions.append(col(AuditLog.action) == action)
    if table_name:
        conditions.append(col(AuditLog.table_name) == table_name)
    if record_id is not None:
        conditions.append(col(AuditLog.record_id) == record_id)
    if performed_by_id is not None:
        conditions.append(col(AuditLog.performed_by_id) == performed_by_id)
    if source:
        conditions.append(col(AuditLog.source) == source)
    if request_id:
        conditions.append(col(AuditLog.request_id) == request_id)
    if correlation_id:
        conditions.append(col(AuditLog.correlation_id) == correlation_id)
    if performed_from is not None:
        conditions.append(col(AuditLog.performed_at) >= performed_from)
    if performed_to is not None:
        conditions.append(col(AuditLog.performed_at) <= performed_to)
    return conditions


def filtered_statement(**filters: Any) -> Any:
    return select(AuditLog).where(*_conditions(**filters))


def get_all(
    *,
    session: Session,
    skip: int,
    limit: int,
    sort_by: str | None,
    sort_order: SortOrder,
    **filters: Any,
) -> tuple[list[AuditLog], int]:
    base = filtered_statement(**filters)
    count = session.exec(select(func.count()).select_from(base.subquery())).one()
    sort_columns = {
        "performed_at": AuditLog.performed_at,
        "action": AuditLog.action,
        "category": AuditLog.category,
        "table_name": AuditLog.table_name,
        "actor_name": AuditLog.actor_name,
        "source": AuditLog.source,
    }
    sort_column = sort_columns.get(sort_by or "performed_at", AuditLog.performed_at)
    order_expression = (
        col(sort_column).desc()
        if sort_order == SortOrder.desc
        else col(sort_column).asc()
    )
    rows = session.exec(
        base.order_by(order_expression, col(AuditLog.id).desc())
        .offset(skip)
        .limit(limit)
    ).all()
    return list(rows), count


def get_by_id(*, session: Session, audit_id: uuid.UUID) -> AuditLog | None:
    return session.get(AuditLog, audit_id)


def get_summary(*, session: Session, **filters: Any) -> Any:
    filtered = filtered_statement(**filters).subquery()
    return session.exec(  # type: ignore[call-overload]
        sa_select(
            func.count().label("total"),
            func.coalesce(
                func.sum(case((filtered.c.action == AuditAction.insert, 1), else_=0)),
                0,
            ).label("inserts"),
            func.coalesce(
                func.sum(case((filtered.c.action == AuditAction.update, 1), else_=0)),
                0,
            ).label("updates"),
            func.coalesce(
                func.sum(case((filtered.c.action == AuditAction.delete, 1), else_=0)),
                0,
            ).label("deletes"),
            func.coalesce(
                func.sum(
                    case(
                        (filtered.c.category == AuditCategory.security, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("security_events"),
        )
    ).one()


def get_actors(
    *, session: Session, search: str | None, limit: int
) -> list[tuple[uuid.UUID, str | None, str | None]]:
    conditions: list[Any] = [col(AuditLog.performed_by_id).is_not(None)]
    if search:
        query = f"%{search.strip()}%"
        conditions.append(
            or_(
                col(AuditLog.actor_name).ilike(query),
                col(AuditLog.actor_email).ilike(query),
            )
        )
    rows = session.exec(
        select(
            AuditLog.performed_by_id,
            func.max(AuditLog.actor_name),
            func.max(AuditLog.actor_email),
        )
        .where(*conditions)
        .group_by(col(AuditLog.performed_by_id))
        .order_by(func.max(AuditLog.actor_name), func.max(AuditLog.actor_email))
        .limit(limit)
    ).all()
    return [(row[0], row[1], row[2]) for row in rows if row[0] is not None]
