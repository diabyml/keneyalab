"""Report repository - database access only."""

import uuid

from sqlmodel import Session, col, func, select

from app.models.lis import (
    Doctor,
    Order,
    Patient,
    Report,
    ReportComponent,
    ReportComponentType,
    ReportComponentVersion,
    ReportRenderer,
    ReportRendererVersion,
    ReportSettings,
    ReportTemplateVersionStatus,
    Title,
)


def get_settings(*, session: Session) -> ReportSettings | None:
    return session.get(ReportSettings, 1)


def list_components(
    *, session: Session, component_type: ReportComponentType | None = None
) -> list[ReportComponent]:
    statement = select(ReportComponent)
    if component_type is not None:
        statement = statement.where(ReportComponent.component_type == component_type)
    return list(
        session.exec(statement.order_by(col(ReportComponent.name).asc())).all()
    )


def get_component(
    *, session: Session, component_id: uuid.UUID
) -> ReportComponent | None:
    return session.get(ReportComponent, component_id)


def get_component_version(
    *,
    session: Session,
    component_id: uuid.UUID,
    status: ReportTemplateVersionStatus,
) -> ReportComponentVersion | None:
    return session.exec(
        select(ReportComponentVersion)
        .where(
            ReportComponentVersion.component_id == component_id,
            ReportComponentVersion.status == status,
        )
        .order_by(col(ReportComponentVersion.version).desc())
    ).first()


def next_component_version(*, session: Session, component_id: uuid.UUID) -> int:
    value = session.exec(
        select(func.max(ReportComponentVersion.version)).where(
            ReportComponentVersion.component_id == component_id
        )
    ).one()
    return int(value or 0) + 1


def list_renderers(*, session: Session) -> list[ReportRenderer]:
    return list(
        session.exec(select(ReportRenderer).order_by(col(ReportRenderer.name).asc())).all()
    )


def get_renderer(*, session: Session, renderer_id: uuid.UUID) -> ReportRenderer | None:
    return session.get(ReportRenderer, renderer_id)


def get_renderer_version(
    *,
    session: Session,
    renderer_id: uuid.UUID,
    status: ReportTemplateVersionStatus,
) -> ReportRendererVersion | None:
    return session.exec(
        select(ReportRendererVersion)
        .where(
            ReportRendererVersion.renderer_id == renderer_id,
            ReportRendererVersion.status == status,
        )
        .order_by(col(ReportRendererVersion.version).desc())
    ).first()


def next_renderer_version(*, session: Session, renderer_id: uuid.UUID) -> int:
    value = session.exec(
        select(func.max(ReportRendererVersion.version)).where(
            ReportRendererVersion.renderer_id == renderer_id
        )
    ).one()
    return int(value or 0) + 1


def get_report(*, session: Session, report_id: uuid.UUID) -> Report | None:
    return session.get(Report, report_id)


def list_order_reports(*, session: Session, order_id: uuid.UUID) -> list[Report]:
    return list(
        session.exec(
            select(Report)
            .where(Report.order_id == order_id)
            .order_by(col(Report.version).desc())
        ).all()
    )


def next_report_version(*, session: Session, order_id: uuid.UUID) -> int:
    value = session.exec(
        select(func.max(Report.version)).where(Report.order_id == order_id)
    ).one()
    return int(value or 0) + 1


def get_report_subject(*, session: Session, order_id: uuid.UUID):
    return session.exec(
        select(Order, Patient, Doctor, Title)
        .join(Patient, Order.patient_id == Patient.id)
        .join(Doctor, Order.doctor_id == Doctor.id, isouter=True)
        .join(Title, Doctor.title_id == Title.id, isouter=True)
        .where(Order.id == order_id)
    ).first()
