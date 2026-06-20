"""Central audit capture, request attribution, and redaction."""

from __future__ import annotations

import ipaddress
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session as SASession

from app.models.lis import AuditAction, AuditCategory, AuditLog

_SENSITIVE_PARTS = (
    "password",
    "hashed_password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "access_key",
)
_EXCLUDED_TABLES = {"audit_logs", "daily_sequences"}
_SECURITY_TABLES = {
    "user",
    "users",
    "permissions",
    "roles",
    "role_permissions",
    "user_roles",
}
_FINANCE_TABLES = {
    "finance_settings",
    "insurance_pricing",
    "invoices",
    "invoice_lines",
    "payment_transactions",
    "payment_refunds",
    "invoice_balance_transfers",
    "customer_credits",
    "doctor_commission_configs",
    "doctor_commission_entries",
    "doctor_commission_adjustments",
    "doctor_commission_payments",
    "doctor_commission_payment_entries",
}
_CONFIG_TABLES = {
    "titles",
    "units",
    "patient_contexts",
    "payment_methods",
    "rejection_reasons",
    "specimen_types",
    "categories",
    "insurance_providers",
    "catalog",
    "catalog_specimen_requirements",
    "catalog_panel_items",
    "analytes",
    "catalog_item_analytes",
    "validation_rules",
    "consistency_rules",
    "consistency_rule_analytes",
    "reflex_rules",
    "instruments",
    "report_templates",
    "lab_settings",
}
_WORKFLOW_TABLES = {
    "orders",
    "order_revisions",
    "order_specimens",
    "order_items",
    "order_item_specimens",
    "order_catalog_item_analytes",
    "analyte_results",
    "analyte_result_comments",
    "critical_notifications",
    "reports",
    "notifications",
}


@dataclass(slots=True)
class AuditRequestContext:
    request_id: str | None = None
    correlation_id: str | None = None
    source: str = "system"
    ip_address: str | None = None
    user_agent: str | None = None
    http_method: str | None = None
    http_path: str | None = None
    actor_id: uuid.UUID | None = None
    actor_name: str | None = None
    actor_email: str | None = None


@dataclass(slots=True)
class AuditAnnotation:
    metadata: dict[str, Any] = field(default_factory=dict)
    record_label: str | None = None
    category: AuditCategory | None = None


_request_context: ContextVar[AuditRequestContext | None] = ContextVar(
    "audit_request_context",
    default=None,
)


def _context() -> AuditRequestContext:
    return _request_context.get() or AuditRequestContext()


def set_request_context(
    context: AuditRequestContext,
) -> Token[AuditRequestContext | None]:
    return _request_context.set(context)


def reset_request_context(token: Token[AuditRequestContext | None]) -> None:
    _request_context.reset(token)


def set_actor(*, actor_id: uuid.UUID, name: str | None, email: str | None) -> None:
    current = _context()
    _request_context.set(
        AuditRequestContext(
            request_id=current.request_id,
            correlation_id=current.correlation_id,
            source=current.source,
            ip_address=current.ip_address,
            user_agent=current.user_agent,
            http_method=current.http_method,
            http_path=current.http_path,
            actor_id=actor_id,
            actor_name=name,
            actor_email=email,
        )
    )


def set_session_actor(
    session: SASession,
    *,
    actor_id: uuid.UUID,
    name: str | None,
    email: str | None,
) -> None:
    session.info["audit_actor"] = {
        "id": actor_id,
        "name": name,
        "email": email,
    }


def client_ip(*, direct_host: str | None, forwarded_for: str | None, trusted: bool) -> str | None:
    candidate = forwarded_for.split(",", 1)[0].strip() if trusted and forwarded_for else direct_host
    if not candidate:
        return None
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def serialize_value(value: Any, *, field_name: str | None = None) -> Any:
    if field_name and any(part in field_name.lower() for part in _SENSITIVE_PARTS):
        return "[MASQUÉ]"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (uuid.UUID, Decimal, date, datetime, Enum)):
        return value.value if isinstance(value, Enum) else str(value)
    if isinstance(value, bytes):
        return f"[{len(value)} octets]"
    if isinstance(value, dict):
        return {
            str(key): serialize_value(item, field_name=str(key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set)):
        return [serialize_value(item) for item in value]
    return str(value)


def audit_record_id(value: Any) -> uuid.UUID | None:
    """Normalize model primary keys to the UUID audit-log identifier."""
    if value is None or isinstance(value, uuid.UUID):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return uuid.UUID(int=value)
        except ValueError:
            return None
    return None


def category_for_table(table_name: str) -> AuditCategory:
    if table_name in _SECURITY_TABLES:
        return AuditCategory.security
    if table_name in _FINANCE_TABLES:
        return AuditCategory.finance
    if table_name in _CONFIG_TABLES:
        return AuditCategory.configuration
    if table_name in _WORKFLOW_TABLES:
        return AuditCategory.workflow
    if table_name in {"patients", "patient_insurance", "doctors"}:
        return AuditCategory.clinical
    return AuditCategory.system


def record_label_for(instance: Any) -> str | None:
    for fields in (
        ("accession_number",),
        ("invoice_number",),
        ("identifier",),
        ("code", "name"),
        ("first_name", "last_name"),
        ("full_name",),
        ("name",),
        ("email",),
    ):
        values = [getattr(instance, name, None) for name in fields]
        if all(value not in (None, "") for value in values):
            return " ".join(str(value) for value in values)[:255]
    return None


def annotate(
    session: SASession,
    instance: Any,
    *,
    metadata: dict[str, Any] | None = None,
    record_label: str | None = None,
    category: AuditCategory | None = None,
) -> None:
    annotations = session.info.setdefault("audit_annotations", {})
    annotations[id(instance)] = AuditAnnotation(
        metadata=metadata or {},
        record_label=record_label,
        category=category,
    )


def add_event(
    session: SASession,
    *,
    table_name: str,
    action: AuditAction,
    category: AuditCategory,
    record_id: uuid.UUID | None = None,
    record_label: str | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    actor_id: uuid.UUID | None = None,
    actor_name: str | None = None,
    actor_email: str | None = None,
) -> AuditLog:
    context = _context()
    session_actor = session.info.get("audit_actor", {})
    event_row = AuditLog(
        table_name=table_name,
        record_id=record_id,
        action=action,
        category=category,
        record_label=record_label,
        old_values=serialize_value(old_values),
        new_values=serialize_value(new_values),
        metadata_json=serialize_value(metadata),
        performed_by_id=(
            actor_id
            if actor_id is not None
            else session_actor.get("id", context.actor_id)
        ),
        actor_name=(
            actor_name
            if actor_name is not None
            else session_actor.get("name", context.actor_name)
        ),
        actor_email=(
            actor_email
            if actor_email is not None
            else session_actor.get("email", context.actor_email)
        ),
        request_id=context.request_id,
        correlation_id=context.correlation_id,
        source=context.source,
        ip_address=context.ip_address,
        user_agent=context.user_agent,
        http_method=context.http_method,
        http_path=context.http_path,
    )
    session.add(event_row)
    return event_row


def _column_values(instance: Any) -> dict[str, Any]:
    state = inspect(instance)
    return {
        attribute.key: serialize_value(getattr(instance, attribute.key, None), field_name=attribute.key)
        for attribute in state.mapper.column_attrs
    }


def _changed_values(instance: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    state = inspect(instance)
    old_values: dict[str, Any] = {}
    new_values: dict[str, Any] = {}
    for attribute in state.mapper.column_attrs:
        history = state.attrs[attribute.key].history
        if not history.has_changes():
            continue
        old = history.deleted[0] if history.deleted else None
        new = history.added[0] if history.added else getattr(instance, attribute.key, None)
        old_serialized = serialize_value(old, field_name=attribute.key)
        new_serialized = serialize_value(new, field_name=attribute.key)
        if old_serialized == new_serialized:
            continue
        old_values[attribute.key] = old_serialized
        new_values[attribute.key] = new_serialized
    return old_values, new_values


def _manual_keys(session: SASession) -> set[tuple[str, uuid.UUID | None, AuditAction]]:
    return {
        (row.table_name, row.record_id, row.action)
        for row in session.new
        if isinstance(row, AuditLog)
    }


@event.listens_for(SASession, "before_flush")
def capture_changes(session: SASession, _flush_context: Any, _instances: Any) -> None:
    manual_keys = _manual_keys(session)
    annotations: dict[int, AuditAnnotation] = session.info.pop("audit_annotations", {})
    candidates = (
        [(instance, AuditAction.insert) for instance in list(session.new)]
        + [(instance, AuditAction.update) for instance in list(session.dirty)]
        + [(instance, AuditAction.delete) for instance in list(session.deleted)]
    )
    for instance, action in candidates:
        if isinstance(instance, AuditLog):
            context = _context()
            session_actor = session.info.get("audit_actor", {})
            instance.performed_by_id = (
                instance.performed_by_id
                or session_actor.get("id")
                or context.actor_id
            )
            instance.actor_name = (
                instance.actor_name
                or session_actor.get("name")
                or context.actor_name
            )
            instance.actor_email = (
                instance.actor_email
                or session_actor.get("email")
                or context.actor_email
            )
            instance.request_id = instance.request_id or context.request_id
            instance.correlation_id = instance.correlation_id or context.correlation_id
            if instance.source == "system" and context.source != "system":
                instance.source = context.source
            instance.ip_address = instance.ip_address or context.ip_address
            instance.user_agent = instance.user_agent or context.user_agent
            instance.http_method = instance.http_method or context.http_method
            instance.http_path = instance.http_path or context.http_path
            if instance.category == AuditCategory.system:
                instance.category = category_for_table(instance.table_name)
            instance.old_values = serialize_value(instance.old_values)
            instance.new_values = serialize_value(instance.new_values)
            instance.metadata_json = serialize_value(instance.metadata_json)
            continue

        state = inspect(instance)
        table_name = state.mapper.local_table.name
        if table_name in _EXCLUDED_TABLES:
            continue
        record_id = audit_record_id(getattr(instance, "id", None))
        key = (table_name, record_id, action)
        if key in manual_keys:
            continue

        annotation = annotations.get(id(instance), AuditAnnotation())
        if action == AuditAction.insert:
            old_values, new_values = None, _column_values(instance)
        elif action == AuditAction.delete:
            old_values, new_values = _column_values(instance), None
        else:
            old_values, new_values = _changed_values(instance)
            if not old_values:
                continue

        add_event(
            session,
            table_name=table_name,
            record_id=record_id,
            action=action,
            category=annotation.category or category_for_table(table_name),
            record_label=annotation.record_label or record_label_for(instance),
            old_values=old_values,
            new_values=new_values,
            metadata=annotation.metadata,
        )
