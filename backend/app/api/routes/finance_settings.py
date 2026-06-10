from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models.lis import FinanceSettingsPublic, FinanceSettingsUpdate
from app.services import finance_settings as settings_service

router = APIRouter(prefix="/finance-settings", tags=["finance-settings"])


@router.get(
    "/",
    dependencies=[Depends(require_permission("finance", "manage"))],
    response_model=FinanceSettingsPublic,
)
def read_finance_settings(session: SessionDep) -> Any:
    return settings_service.get_settings_public(session=session)


@router.put(
    "/",
    dependencies=[Depends(require_permission("finance", "manage"))],
    response_model=FinanceSettingsPublic,
)
def update_finance_settings(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    settings_in: FinanceSettingsUpdate,
) -> Any:
    return settings_service.update_settings(
        session=session,
        settings_in=settings_in,
        updated_by_id=current_user.id,
    )
