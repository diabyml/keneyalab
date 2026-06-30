import uuid
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.deps import (
    CurrentUser,
    SessionDep,
    require_any_permission,
    require_permission,
)
from app.models import (
    ResultBulkEntryRequest,
    ResultBulkVerificationPublic,
    ResultCommentDetailPublic,
    ResultCommentRequest,
    ResultCorrectionRequest,
    ResultInterpretationUpdate,
    ResultQueuePublic,
    ResultSubmissionPublic,
    ResultWorkspacePublic,
    SortOrder,
)
from app.services import permission as permission_service
from app.services import result as result_service

router = APIRouter(prefix="/results", tags=["results"])


@router.get(
    "/queue",
    dependencies=[Depends(require_permission("results", "view"))],
    response_model=ResultQueuePublic,
)
def read_result_queue(
    session: SessionDep,
    mode: Literal["entry", "verification"] = "entry",
    skip: int = 0,
    limit: int = 25,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    flagged: bool | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    sort_order: SortOrder = SortOrder.desc,
) -> Any:
    return result_service.get_queue(
        session=session,
        mode=mode,
        skip=skip,
        limit=limit,
        search=search,
        category_id=category_id,
        flagged=flagged,
        created_from=created_from,
        created_to=created_to,
        sort_order=sort_order,
    )


@router.get(
    "/orders/{order_id}",
    dependencies=[Depends(require_permission("results", "view"))],
    response_model=ResultWorkspacePublic,
)
def read_result_workspace(
    session: SessionDep, current_user: CurrentUser, order_id: uuid.UUID
) -> Any:
    return result_service.get_workspace(
        session=session,
        order_id=order_id,
        include_audit=permission_service.check_permission(
            session=session,
            user=current_user,
            resource="audit",
            action="view",
        ),
    )


@router.put(
    "/orders/{order_id}/interpretation",
    dependencies=[Depends(require_permission("results", "edit"))],
    response_model=ResultWorkspacePublic,
)
def update_result_interpretation(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
    request_in: ResultInterpretationUpdate,
) -> Any:
    return result_service.update_interpretation(
        session=session,
        order_id=order_id,
        request=request_in,
        user_id=current_user.id,
    )


@router.post(
    "/orders/{order_id}/entries",
    dependencies=[
        Depends(
            require_any_permission(
                ("results", "enter"),
                ("results", "edit"),
            )
        )
    ],
    response_model=ResultSubmissionPublic,
)
def enter_results(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
    request_in: ResultBulkEntryRequest,
) -> Any:
    return result_service.enter_results(
        session=session,
        order_id=order_id,
        request=request_in,
        user_id=current_user.id,
    )


@router.post(
    "/orders/{order_id}/images",
    dependencies=[
        Depends(
            require_any_permission(
                ("results", "enter"),
                ("results", "edit"),
            )
        )
    ],
    response_model=ResultSubmissionPublic,
)
async def upload_result_image(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
    order_item_id: uuid.UUID = Form(),
    analyte_id: uuid.UUID = Form(),
    specimen_id: uuid.UUID = Form(),
    file: UploadFile = File(),
) -> Any:
    return result_service.upload_image_result(
        session=session,
        order_id=order_id,
        order_item_id=order_item_id,
        analyte_id=analyte_id,
        specimen_id=specimen_id,
        content_type=file.content_type,
        data=await file.read(),
        user_id=current_user.id,
    )


@router.post(
    "/{result_id}/comments",
    dependencies=[Depends(require_permission("results", "view"))],
    response_model=ResultCommentDetailPublic,
)
def add_result_comment(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    result_id: uuid.UUID,
    request_in: ResultCommentRequest,
) -> Any:
    return result_service.add_comment(
        session=session,
        result_id=result_id,
        request=request_in,
        user_id=current_user.id,
    )


@router.post(
    "/{result_id}/corrections",
    dependencies=[Depends(require_permission("results", "edit"))],
    response_model=ResultWorkspacePublic,
)
def correct_verified_result(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    result_id: uuid.UUID,
    request_in: ResultCorrectionRequest,
) -> Any:
    return result_service.correct_verified_result(
        session=session,
        result_id=result_id,
        request=request_in,
        user_id=current_user.id,
    )


@router.post(
    "/{result_id}/correction-image",
    dependencies=[Depends(require_permission("results", "edit"))],
    response_model=ResultWorkspacePublic,
)
async def correct_verified_image_result(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    result_id: uuid.UUID,
    reason: str = Form(),
    file: UploadFile = File(),
) -> Any:
    return result_service.correct_verified_image_result(
        session=session,
        result_id=result_id,
        reason=reason,
        content_type=file.content_type,
        data=await file.read(),
        user_id=current_user.id,
    )


@router.post(
    "/{result_id}/verify",
    dependencies=[Depends(require_permission("results", "verify"))],
    response_model=ResultWorkspacePublic,
)
def verify_result(
    session: SessionDep, current_user: CurrentUser, result_id: uuid.UUID
) -> Any:
    return result_service.verify_result(
        session=session, result_id=result_id, user_id=current_user.id
    )


@router.post(
    "/orders/{order_id}/verify",
    dependencies=[Depends(require_permission("results", "verify"))],
    response_model=ResultBulkVerificationPublic,
)
def verify_order(
    session: SessionDep, current_user: CurrentUser, order_id: uuid.UUID
) -> Any:
    return result_service.verify_order(
        session=session, order_id=order_id, user_id=current_user.id
    )
