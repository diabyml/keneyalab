"""Global laboratory identity configuration."""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlmodel import Session

from app.core.exceptions import BusinessRuleError
from app.models.lis import (
    AuditAction,
    AuditLog,
    LabSettings,
    LabSettingsPublic,
    LabSettingsUpdate,
)
from app.services import object_storage

SETTINGS_ID = 1


def get_settings(*, session: Session) -> LabSettings:
    settings = session.get(LabSettings, SETTINGS_ID)
    if settings is None:
        settings = LabSettings(id=SETTINGS_ID)
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


def to_public(settings: LabSettings) -> LabSettingsPublic:
    data = settings.model_dump()
    data["logo_url"] = object_storage.presigned_url(settings.logo_object_key)
    return LabSettingsPublic.model_validate(data)


def get_settings_public(*, session: Session) -> LabSettingsPublic:
    return to_public(get_settings(session=session))


def _audit_value(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def update_settings(
    *,
    session: Session,
    settings_in: LabSettingsUpdate,
    updated_by_id: uuid.UUID,
) -> LabSettingsPublic:
    settings = get_settings(session=session)
    updates = settings_in.model_dump(exclude_unset=True)
    for field_name, value in updates.items():
        if isinstance(value, str):
            normalized = value.strip()
            updates[field_name] = normalized or None
    if updates.get("display_name") is None and "display_name" in updates:
        raise BusinessRuleError("Le nom du laboratoire est obligatoire")

    old_values: dict[str, Any] = {}
    new_values: dict[str, Any] = {}
    for field_name, value in updates.items():
        current = getattr(settings, field_name)
        if current == value:
            continue
        old_values[field_name] = _audit_value(current)
        new_values[field_name] = _audit_value(value)
        setattr(settings, field_name, value)

    if not old_values:
        return to_public(settings)

    _save_audited_change(
        session=session,
        settings=settings,
        updated_by_id=updated_by_id,
        old_values=old_values,
        new_values=new_values,
    )
    return to_public(settings)


def update_logo(
    *,
    session: Session,
    content_type: str | None,
    data: bytes,
    updated_by_id: uuid.UUID,
) -> LabSettingsPublic:
    settings = get_settings(session=session)
    old_key = settings.logo_object_key
    new_key = object_storage.upload_lab_logo(content_type=content_type, data=data)
    settings.logo_object_key = new_key
    _save_audited_change(
        session=session,
        settings=settings,
        updated_by_id=updated_by_id,
        old_values={"logo_object_key": old_key},
        new_values={"logo_object_key": new_key},
    )
    if old_key:
        object_storage.delete_object(old_key)
    return to_public(settings)


def delete_logo(
    *, session: Session, updated_by_id: uuid.UUID
) -> LabSettingsPublic:
    settings = get_settings(session=session)
    old_key = settings.logo_object_key
    if not old_key:
        return to_public(settings)
    settings.logo_object_key = None
    _save_audited_change(
        session=session,
        settings=settings,
        updated_by_id=updated_by_id,
        old_values={"logo_object_key": old_key},
        new_values={"logo_object_key": None},
    )
    object_storage.delete_object(old_key)
    return to_public(settings)


def _save_audited_change(
    *,
    session: Session,
    settings: LabSettings,
    updated_by_id: uuid.UUID,
    old_values: dict[str, Any],
    new_values: dict[str, Any],
) -> None:
    settings.updated_by_id = updated_by_id
    settings.updated_at = datetime.now(timezone.utc)
    session.add(settings)
    session.add(
        AuditLog(
            table_name="lab_settings",
            record_id=uuid.UUID(int=SETTINGS_ID),
            action=AuditAction.update,
            old_values=old_values,
            new_values=new_values,
            performed_by_id=updated_by_id,
        )
    )
    session.commit()
    session.refresh(settings)
