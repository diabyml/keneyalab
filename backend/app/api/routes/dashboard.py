from datetime import datetime
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.models.lis import DashboardPublic
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardPublic)
def read_dashboard(
    session: SessionDep,
    current_user: CurrentUser,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> Any:
    return dashboard_service.get_dashboard(
        session=session,
        user=current_user,
        created_from=created_from,
        created_to=created_to,
    )
