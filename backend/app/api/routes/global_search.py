from typing import Any

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.models import GlobalSearchResultsPublic
from app.services import global_search as global_search_service

router = APIRouter(prefix="/global-search", tags=["global-search"])


@router.get("/", response_model=GlobalSearchResultsPublic)
def read_global_search(
    session: SessionDep,
    current_user: CurrentUser,
    query: str = Query(min_length=0, max_length=100),
    limit: int = Query(default=5, ge=1, le=10),
) -> Any:
    return global_search_service.search(
        session=session,
        user=current_user,
        query=query,
        limit=limit,
    )
