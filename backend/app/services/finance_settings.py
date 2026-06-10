"""Global finance configuration."""

import uuid
from datetime import datetime, timezone

from sqlmodel import Session

from app.models.lis import (
    AuditAction,
    AuditLog,
    FinanceSettings,
    FinanceSettingsPublic,
    FinanceSettingsUpdate,
)

SETTINGS_ID = 1


def get_settings(*, session: Session) -> FinanceSettings:
    settings = session.get(FinanceSettings, SETTINGS_ID)
    if settings is None:
        settings = FinanceSettings(id=SETTINGS_ID)
        session.add(settings)
        session.flush()
    return settings


def get_settings_public(*, session: Session) -> FinanceSettingsPublic:
    return FinanceSettingsPublic.model_validate(get_settings(session=session))


def update_settings(
    *,
    session: Session,
    settings_in: FinanceSettingsUpdate,
    updated_by_id: uuid.UUID,
) -> FinanceSettingsPublic:
    settings = get_settings(session=session)
    old_values: dict[str, object] = {}
    new_values: dict[str, object] = {}

    if settings_in.discount_allocation_policy is not None:
        old_values["discount_allocation_policy"] = (
            settings.discount_allocation_policy.value
        )
        settings.discount_allocation_policy = settings_in.discount_allocation_policy
        new_values["discount_allocation_policy"] = (
            settings_in.discount_allocation_policy.value
        )

    if settings_in.default_commission_rate is not None:
        old_values["default_commission_rate"] = str(
            settings.default_commission_rate
        )
        settings.default_commission_rate = settings_in.default_commission_rate
        new_values["default_commission_rate"] = str(
            settings_in.default_commission_rate
        )

    if settings_in.default_insurance_commission_rate is not None:
        old_values["default_insurance_commission_rate"] = str(
            settings.default_insurance_commission_rate
        )
        settings.default_insurance_commission_rate = (
            settings_in.default_insurance_commission_rate
        )
        new_values["default_insurance_commission_rate"] = str(
            settings_in.default_insurance_commission_rate
        )

    if not old_values:
        return FinanceSettingsPublic.model_validate(settings)

    settings.updated_by_id = updated_by_id
    settings.updated_at = datetime.now(timezone.utc)
    session.add(settings)
    session.add(
        AuditLog(
            table_name="finance_settings",
            record_id=uuid.UUID(int=SETTINGS_ID),
            action=AuditAction.update,
            old_values=old_values,
            new_values=new_values,
            performed_by_id=updated_by_id,
        )
    )
    session.commit()
    session.refresh(settings)
    return FinanceSettingsPublic.model_validate(settings)
