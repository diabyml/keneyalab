import uuid
from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models.lis import (
    CategoryPublic,
    CategoryReportRendererUpdate,
    ReportComponentCreate,
    ReportComponentPublic,
    ReportComponentsPublic,
    ReportComponentType,
    ReportComponentUpdate,
    ReportDefaultUpdate,
    ReportDeliveryRequest,
    ReportPreviewPublic,
    ReportPublic,
    ReportReleaseRequest,
    ReportRendererCreate,
    ReportRendererPublic,
    ReportRenderersPublic,
    ReportRendererUpdate,
    ReportSettingsPublic,
    ReportsPublic,
)
from app.services import report as report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/components",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportComponentsPublic,
)
def read_report_components(
    session: SessionDep,
    component_type: ReportComponentType | None = None,
) -> Any:
    return report_service.list_components(
        session=session, component_type=component_type
    )


@router.post(
    "/components",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportComponentPublic,
)
def create_report_component(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    component_in: ReportComponentCreate,
) -> Any:
    return report_service.create_component(
        session=session, component_in=component_in, user_id=current_user.id
    )


@router.get(
    "/components/{component_id}",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportComponentPublic,
)
def read_report_component(session: SessionDep, component_id: uuid.UUID) -> Any:
    return report_service.get_component(
        session=session, component_id=component_id
    )


@router.put(
    "/components/{component_id}",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportComponentPublic,
)
def update_report_component(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    component_id: uuid.UUID,
    component_in: ReportComponentUpdate,
) -> Any:
    return report_service.update_component(
        session=session,
        component_id=component_id,
        component_in=component_in,
        user_id=current_user.id,
    )


@router.post(
    "/components/{component_id}/publish",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportComponentPublic,
)
def publish_report_component(
    session: SessionDep, current_user: CurrentUser, component_id: uuid.UUID
) -> Any:
    return report_service.publish_component(
        session=session, component_id=component_id, user_id=current_user.id
    )


@router.post(
    "/components/{component_id}/archive",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportComponentPublic,
)
def archive_report_component(
    session: SessionDep, component_id: uuid.UUID
) -> Any:
    return report_service.archive_component(
        session=session, component_id=component_id
    )


@router.get(
    "/renderers",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportRenderersPublic,
)
def read_report_renderers(session: SessionDep) -> Any:
    return report_service.list_renderers(session=session)


@router.post(
    "/renderers",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportRendererPublic,
)
def create_report_renderer(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    renderer_in: ReportRendererCreate,
) -> Any:
    return report_service.create_renderer(
        session=session, renderer_in=renderer_in, user_id=current_user.id
    )


@router.get(
    "/renderers/{renderer_id}",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportRendererPublic,
)
def read_report_renderer(session: SessionDep, renderer_id: uuid.UUID) -> Any:
    return report_service.get_renderer(session=session, renderer_id=renderer_id)


@router.put(
    "/renderers/{renderer_id}",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportRendererPublic,
)
def update_report_renderer(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    renderer_id: uuid.UUID,
    renderer_in: ReportRendererUpdate,
) -> Any:
    return report_service.update_renderer(
        session=session,
        renderer_id=renderer_id,
        renderer_in=renderer_in,
        user_id=current_user.id,
    )


@router.post(
    "/renderers/{renderer_id}/publish",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportRendererPublic,
)
def publish_report_renderer(
    session: SessionDep, current_user: CurrentUser, renderer_id: uuid.UUID
) -> Any:
    return report_service.publish_renderer(
        session=session, renderer_id=renderer_id, user_id=current_user.id
    )


@router.post(
    "/renderers/{renderer_id}/archive",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportRendererPublic,
)
def archive_report_renderer(
    session: SessionDep, renderer_id: uuid.UUID
) -> Any:
    return report_service.archive_renderer(
        session=session, renderer_id=renderer_id
    )


@router.get(
    "/settings",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportSettingsPublic,
)
def read_report_settings(session: SessionDep) -> Any:
    return report_service.get_settings(session=session)


@router.put(
    "/settings/components/{component_type}",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportSettingsPublic,
)
def set_default_report_component(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    component_type: ReportComponentType,
    request_in: ReportDefaultUpdate,
) -> Any:
    return report_service.set_default_component(
        session=session,
        component_type=component_type,
        request=request_in,
        user_id=current_user.id,
    )


@router.put(
    "/settings/renderer",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportSettingsPublic,
)
def set_default_report_renderer(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    request_in: ReportDefaultUpdate,
) -> Any:
    return report_service.set_default_renderer(
        session=session, request=request_in, user_id=current_user.id
    )


@router.put(
    "/categories/{category_id}/renderer",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=CategoryPublic,
)
def assign_category_report_renderer(
    *,
    session: SessionDep,
    category_id: uuid.UUID,
    request_in: CategoryReportRendererUpdate,
) -> Any:
    return report_service.assign_category_renderer(
        session=session, category_id=category_id, request=request_in
    )


@router.get(
    "/sample-preview",
    dependencies=[Depends(require_permission("reports", "manage_templates"))],
    response_model=ReportPreviewPublic,
)
def read_sample_report_preview(session: SessionDep) -> Any:
    return report_service.get_sample_preview(session=session)


@router.get(
    "/orders/{order_id}/preview",
    dependencies=[Depends(require_permission("reports", "view"))],
    response_model=ReportPreviewPublic,
)
def read_order_report_preview(session: SessionDep, order_id: uuid.UUID) -> Any:
    return report_service.get_preview(session=session, order_id=order_id)


@router.post(
    "/orders/{order_id}/release",
    dependencies=[Depends(require_permission("reports", "release"))],
    response_model=ReportPublic,
)
def release_order_report(
    session: SessionDep,
    current_user: CurrentUser,
    order_id: uuid.UUID,
    request_in: ReportReleaseRequest,
) -> Any:
    return report_service.release_report(
        session=session,
        order_id=order_id,
        user_id=current_user.id,
        request=request_in,
    )


@router.get(
    "/orders/{order_id}",
    dependencies=[Depends(require_permission("reports", "view"))],
    response_model=ReportsPublic,
)
def read_order_reports(session: SessionDep, order_id: uuid.UUID) -> Any:
    return report_service.list_order_reports(session=session, order_id=order_id)


@router.get(
    "/{report_id}",
    dependencies=[Depends(require_permission("reports", "view"))],
    response_model=ReportPublic,
)
def read_report(session: SessionDep, report_id: uuid.UUID) -> Any:
    return report_service.get_report(session=session, report_id=report_id)


@router.post(
    "/{report_id}/void",
    dependencies=[Depends(require_permission("reports", "void"))],
    response_model=ReportPublic,
)
def void_report(session: SessionDep, report_id: uuid.UUID) -> Any:
    return report_service.void_report(session=session, report_id=report_id)


@router.post(
    "/{report_id}/deliver",
    dependencies=[Depends(require_permission("reports", "release"))],
    response_model=ReportPublic,
)
def deliver_report(
    *,
    session: SessionDep,
    report_id: uuid.UUID,
    request_in: ReportDeliveryRequest,
) -> Any:
    return report_service.deliver_report(
        session=session, report_id=report_id, request=request_in
    )
