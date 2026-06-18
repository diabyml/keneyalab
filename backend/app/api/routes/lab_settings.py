from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models.lis import LabSettingsPublic, LabSettingsUpdate
from app.services import lab_settings as settings_service

router = APIRouter(prefix="/lab-settings", tags=["lab-settings"])


@router.get("/", response_model=LabSettingsPublic)
def read_lab_settings(
    session: SessionDep, _current_user: CurrentUser
) -> Any:
    return settings_service.get_settings_public(session=session)


@router.put(
    "/",
    dependencies=[Depends(require_permission("lab_settings", "manage"))],
    response_model=LabSettingsPublic,
)
def update_lab_settings(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    settings_in: LabSettingsUpdate,
) -> Any:
    return settings_service.update_settings(
        session=session,
        settings_in=settings_in,
        updated_by_id=current_user.id,
    )


@router.post(
    "/logo",
    dependencies=[Depends(require_permission("lab_settings", "manage"))],
    response_model=LabSettingsPublic,
)
async def upload_lab_logo(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(),
) -> Any:
    return settings_service.update_logo(
        session=session,
        content_type=file.content_type,
        data=await file.read(),
        updated_by_id=current_user.id,
    )


@router.delete(
    "/logo",
    dependencies=[Depends(require_permission("lab_settings", "manage"))],
    response_model=LabSettingsPublic,
)
def delete_lab_logo(
    *, session: SessionDep, current_user: CurrentUser
) -> Any:
    return settings_service.delete_logo(
        session=session, updated_by_id=current_user.id
    )
