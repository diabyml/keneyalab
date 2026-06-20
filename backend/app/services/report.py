"""Versioned report templates, rendering snapshots, release, and delivery."""

import re
import uuid
from datetime import date, datetime, timezone
from html import escape
from html.parser import HTMLParser
from typing import Any

from pydantic import EmailStr, TypeAdapter
from sqlmodel import Session, select

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.lis import (
    Category,
    CategoryReportRendererUpdate,
    DeliveryStatus,
    Report,
    ReportChannel,
    ReportComponent,
    ReportComponentCreate,
    ReportComponentPublic,
    ReportComponentsPublic,
    ReportComponentType,
    ReportComponentUpdate,
    ReportComponentVersion,
    ReportComponentVersionPublic,
    ReportDefaultUpdate,
    ReportDeliveryRequest,
    ReportPreviewPublic,
    ReportPublic,
    ReportReleaseRequest,
    ReportRenderer,
    ReportRendererCreate,
    ReportRendererPublic,
    ReportRenderersPublic,
    ReportRendererUpdate,
    ReportRendererVersion,
    ReportRendererVersionPublic,
    ReportSettings,
    ReportSettingsPublic,
    ReportsPublic,
    ReportTemplateVersionStatus,
    ResultStatus,
)
from app.repositories import report as report_repo
from app.services import lab_settings as lab_settings_service
from app.services import result as result_service
from app.utils import send_email

GENDER_LABELS = {
    "male": "Masculin",
    "female": "Féminin",
}

ALLOWED_TAGS = {
    "div",
    "span",
    "p",
    "strong",
    "em",
    "small",
    "section",
    "header",
    "footer",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "img",
    "br",
    "hr",
}
VOID_TAGS = {"img", "br", "hr"}
ALLOWED_ATTRS = {"class", "alt", "src", "width", "height", "colspan", "rowspan"}
FORBIDDEN_JS = re.compile(
    r"\b(import|export|require|fetch|XMLHttpRequest|WebSocket|EventSource|"
    r"localStorage|sessionStorage|document\.cookie|window\.parent|window\.top)\b"
)


class _SafeHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.blocked_depth = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in {"script", "style", "iframe", "object"}:
            self.blocked_depth += 1
            return
        if self.blocked_depth:
            return
        if tag not in ALLOWED_TAGS:
            return
        safe_attrs = []
        for name, value in attrs:
            if name not in ALLOWED_ATTRS or value is None:
                continue
            if name == "src" and not (
                value.startswith("https://")
                or value.startswith("data:image/")
                or value.startswith("{{")
            ):
                continue
            safe_attrs.append(f'{name}="{escape(value, quote=True)}"')
        suffix = f" {' '.join(safe_attrs)}" if safe_attrs else ""
        self.parts.append(f"<{tag}{suffix}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "iframe", "object"} and self.blocked_depth:
            self.blocked_depth -= 1
            return
        if self.blocked_depth:
            return
        if tag in ALLOWED_TAGS and tag not in VOID_TAGS:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if not self.blocked_depth:
            self.parts.append(escape(data))


def sanitize_html(value: str) -> str:
    parser = _SafeHTMLParser()
    parser.feed(value)
    return "".join(parser.parts)


def validate_css(value: str) -> str:
    if re.search(
        r"@import|expression\s*\(|javascript\s*:|behavior\s*:|url\s*\(",
        value,
        re.I,
    ):
        raise BusinessRuleError("Le CSS contient une instruction interdite")
    return value.strip()


def validate_jsx(value: str) -> str:
    source = value.strip()
    if not source:
        raise BusinessRuleError("Le code React du rendu est obligatoire")
    if FORBIDDEN_JS.search(source):
        raise BusinessRuleError(
            "Les imports, accès réseau et accès au contexte de l'application sont interdits"
        )
    if "function Renderer" not in source and "const Renderer" not in source:
        raise BusinessRuleError(
            "Le code doit déclarer un composant nommé Renderer"
        )
    return source


def _settings(*, session: Session) -> ReportSettings:
    settings = report_repo.get_settings(session=session)
    if settings is None:
        settings = ReportSettings(id=1)
        session.add(settings)
        session.flush()
    return settings


def _component_public(
    *, session: Session, component: ReportComponent
) -> ReportComponentPublic:
    settings = _settings(session=session)
    default_id = {
        ReportComponentType.header: settings.default_header_id,
        ReportComponentType.patient_doctor_details: settings.default_details_id,
        ReportComponentType.footer: settings.default_footer_id,
    }[component.component_type]
    draft = report_repo.get_component_version(
        session=session,
        component_id=component.id,
        status=ReportTemplateVersionStatus.draft,
    )
    published = report_repo.get_component_version(
        session=session,
        component_id=component.id,
        status=ReportTemplateVersionStatus.published,
    )
    return ReportComponentPublic(
        **component.model_dump(),
        draft_version=(
            ReportComponentVersionPublic.model_validate(draft) if draft else None
        ),
        published_version=(
            ReportComponentVersionPublic.model_validate(published)
            if published
            else None
        ),
        is_default=component.id == default_id,
    )


def list_components(
    *, session: Session, component_type: ReportComponentType | None = None
) -> ReportComponentsPublic:
    rows = report_repo.list_components(
        session=session, component_type=component_type
    )
    return ReportComponentsPublic(
        data=[_component_public(session=session, component=row) for row in rows],
        count=len(rows),
    )


def get_component(
    *, session: Session, component_id: uuid.UUID
) -> ReportComponentPublic:
    component = report_repo.get_component(
        session=session, component_id=component_id
    )
    if component is None:
        raise NotFoundError("Composant de rapport non trouvé")
    return _component_public(session=session, component=component)


def create_component(
    *,
    session: Session,
    component_in: ReportComponentCreate,
    user_id: uuid.UUID,
) -> ReportComponentPublic:
    component = ReportComponent(
        name=component_in.name.strip(),
        description=(component_in.description or "").strip() or None,
        component_type=component_in.component_type,
        created_by_id=user_id,
    )
    session.add(component)
    session.flush()
    session.add(
        ReportComponentVersion(
            component_id=component.id,
            version=1,
            html_source=sanitize_html(component_in.html_source),
            css_source=validate_css(component_in.css_source),
            created_by_id=user_id,
        )
    )
    session.commit()
    session.refresh(component)
    return _component_public(session=session, component=component)


def update_component(
    *,
    session: Session,
    component_id: uuid.UUID,
    component_in: ReportComponentUpdate,
    user_id: uuid.UUID,
) -> ReportComponentPublic:
    component = report_repo.get_component(
        session=session, component_id=component_id
    )
    if component is None:
        raise NotFoundError("Composant de rapport non trouvé")
    updates = component_in.model_dump(
        exclude_unset=True, exclude={"html_source", "css_source"}
    )
    for field, value in updates.items():
        setattr(component, field, value.strip() if isinstance(value, str) else value)
    draft = report_repo.get_component_version(
        session=session,
        component_id=component.id,
        status=ReportTemplateVersionStatus.draft,
    )
    published = report_repo.get_component_version(
        session=session,
        component_id=component.id,
        status=ReportTemplateVersionStatus.published,
    )
    if draft is None:
        draft = ReportComponentVersion(
            component_id=component.id,
            version=report_repo.next_component_version(
                session=session, component_id=component.id
            ),
            html_source=published.html_source if published else "",
            css_source=published.css_source if published else "",
            created_by_id=user_id,
        )
    if component_in.html_source is not None:
        draft.html_source = sanitize_html(component_in.html_source)
    if component_in.css_source is not None:
        draft.css_source = validate_css(component_in.css_source)
    draft.updated_at = datetime.now(timezone.utc)
    component.updated_at = datetime.now(timezone.utc)
    session.add(component)
    session.add(draft)
    session.commit()
    return _component_public(session=session, component=component)


def publish_component(
    *, session: Session, component_id: uuid.UUID, user_id: uuid.UUID
) -> ReportComponentPublic:
    component = report_repo.get_component(
        session=session, component_id=component_id
    )
    if component is None:
        raise NotFoundError("Composant de rapport non trouvé")
    draft = report_repo.get_component_version(
        session=session,
        component_id=component.id,
        status=ReportTemplateVersionStatus.draft,
    )
    if draft is None:
        raise BusinessRuleError("Aucun brouillon à publier")
    current = report_repo.get_component_version(
        session=session,
        component_id=component.id,
        status=ReportTemplateVersionStatus.published,
    )
    if current:
        current.status = ReportTemplateVersionStatus.archived
        session.add(current)
    draft.status = ReportTemplateVersionStatus.published
    draft.published_by_id = user_id
    draft.published_at = datetime.now(timezone.utc)
    session.add(draft)
    session.commit()
    return _component_public(session=session, component=component)


def archive_component(
    *, session: Session, component_id: uuid.UUID
) -> ReportComponentPublic:
    component = report_repo.get_component(
        session=session, component_id=component_id
    )
    if component is None:
        raise NotFoundError("Composant de rapport non trouvé")
    settings = _settings(session=session)
    if component.id in {
        settings.default_header_id,
        settings.default_details_id,
        settings.default_footer_id,
    }:
        raise BusinessRuleError("Le composant par défaut ne peut pas être archivé")
    component.is_archived = True
    session.add(component)
    session.commit()
    return _component_public(session=session, component=component)


def _renderer_public(
    *, session: Session, renderer: ReportRenderer
) -> ReportRendererPublic:
    settings = _settings(session=session)
    draft = report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer.id,
        status=ReportTemplateVersionStatus.draft,
    )
    published = report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer.id,
        status=ReportTemplateVersionStatus.published,
    )
    return ReportRendererPublic(
        **renderer.model_dump(),
        draft_version=(
            ReportRendererVersionPublic.model_validate(draft) if draft else None
        ),
        published_version=(
            ReportRendererVersionPublic.model_validate(published)
            if published
            else None
        ),
        is_default=renderer.id == settings.default_renderer_id,
    )


def list_renderers(*, session: Session) -> ReportRenderersPublic:
    rows = report_repo.list_renderers(session=session)
    return ReportRenderersPublic(
        data=[_renderer_public(session=session, renderer=row) for row in rows],
        count=len(rows),
    )


def get_renderer(
    *, session: Session, renderer_id: uuid.UUID
) -> ReportRendererPublic:
    renderer = report_repo.get_renderer(session=session, renderer_id=renderer_id)
    if renderer is None:
        raise NotFoundError("Rendu de rapport non trouvé")
    return _renderer_public(session=session, renderer=renderer)


def create_renderer(
    *,
    session: Session,
    renderer_in: ReportRendererCreate,
    user_id: uuid.UUID,
) -> ReportRendererPublic:
    renderer = ReportRenderer(
        name=renderer_in.name.strip(),
        description=(renderer_in.description or "").strip() or None,
        created_by_id=user_id,
    )
    session.add(renderer)
    session.flush()
    session.add(
        ReportRendererVersion(
            renderer_id=renderer.id,
            version=1,
            jsx_source=validate_jsx(renderer_in.jsx_source),
            css_source=validate_css(renderer_in.css_source),
            created_by_id=user_id,
        )
    )
    session.commit()
    session.refresh(renderer)
    return _renderer_public(session=session, renderer=renderer)


def update_renderer(
    *,
    session: Session,
    renderer_id: uuid.UUID,
    renderer_in: ReportRendererUpdate,
    user_id: uuid.UUID,
) -> ReportRendererPublic:
    renderer = report_repo.get_renderer(session=session, renderer_id=renderer_id)
    if renderer is None:
        raise NotFoundError("Rendu de rapport non trouvé")
    updates = renderer_in.model_dump(
        exclude_unset=True, exclude={"jsx_source", "css_source"}
    )
    for field, value in updates.items():
        setattr(renderer, field, value.strip() if isinstance(value, str) else value)
    draft = report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer.id,
        status=ReportTemplateVersionStatus.draft,
    )
    published = report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer.id,
        status=ReportTemplateVersionStatus.published,
    )
    if draft is None:
        draft = ReportRendererVersion(
            renderer_id=renderer.id,
            version=report_repo.next_renderer_version(
                session=session, renderer_id=renderer.id
            ),
            jsx_source=published.jsx_source if published else "",
            css_source=published.css_source if published else "",
            created_by_id=user_id,
        )
    if renderer_in.jsx_source is not None:
        draft.jsx_source = validate_jsx(renderer_in.jsx_source)
    if renderer_in.css_source is not None:
        draft.css_source = validate_css(renderer_in.css_source)
    draft.updated_at = datetime.now(timezone.utc)
    renderer.updated_at = datetime.now(timezone.utc)
    session.add(renderer)
    session.add(draft)
    session.commit()
    return _renderer_public(session=session, renderer=renderer)


def publish_renderer(
    *, session: Session, renderer_id: uuid.UUID, user_id: uuid.UUID
) -> ReportRendererPublic:
    renderer = report_repo.get_renderer(session=session, renderer_id=renderer_id)
    if renderer is None:
        raise NotFoundError("Rendu de rapport non trouvé")
    draft = report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer.id,
        status=ReportTemplateVersionStatus.draft,
    )
    if draft is None:
        raise BusinessRuleError("Aucun brouillon à publier")
    current = report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer.id,
        status=ReportTemplateVersionStatus.published,
    )
    if current:
        current.status = ReportTemplateVersionStatus.archived
        session.add(current)
    draft.status = ReportTemplateVersionStatus.published
    draft.published_by_id = user_id
    draft.published_at = datetime.now(timezone.utc)
    session.add(draft)
    session.commit()
    return _renderer_public(session=session, renderer=renderer)


def archive_renderer(
    *, session: Session, renderer_id: uuid.UUID
) -> ReportRendererPublic:
    renderer = report_repo.get_renderer(session=session, renderer_id=renderer_id)
    if renderer is None:
        raise NotFoundError("Rendu de rapport non trouvé")
    settings = _settings(session=session)
    if renderer.id == settings.default_renderer_id:
        raise BusinessRuleError("Le rendu par défaut ne peut pas être archivé")
    assigned = session.exec(
        select(Category.id).where(Category.report_renderer_id == renderer.id)
    ).first()
    if assigned:
        raise BusinessRuleError("Ce rendu est encore affecté à une catégorie")
    renderer.is_archived = True
    session.add(renderer)
    session.commit()
    return _renderer_public(session=session, renderer=renderer)


def get_settings(*, session: Session) -> ReportSettingsPublic:
    return ReportSettingsPublic.model_validate(_settings(session=session))


def set_default_component(
    *,
    session: Session,
    component_type: ReportComponentType,
    request: ReportDefaultUpdate,
    user_id: uuid.UUID,
) -> ReportSettingsPublic:
    component = report_repo.get_component(
        session=session, component_id=request.template_id
    )
    if component is None or component.component_type != component_type:
        raise BusinessRuleError("Composant incompatible")
    published = report_repo.get_component_version(
        session=session,
        component_id=component.id,
        status=ReportTemplateVersionStatus.published,
    )
    if published is None or component.is_archived:
        raise BusinessRuleError("Le composant doit être publié et actif")
    settings = _settings(session=session)
    field = {
        ReportComponentType.header: "default_header_id",
        ReportComponentType.patient_doctor_details: "default_details_id",
        ReportComponentType.footer: "default_footer_id",
    }[component_type]
    setattr(settings, field, component.id)
    settings.updated_by_id = user_id
    settings.updated_at = datetime.now(timezone.utc)
    session.add(settings)
    session.commit()
    return ReportSettingsPublic.model_validate(settings)


def set_default_renderer(
    *,
    session: Session,
    request: ReportDefaultUpdate,
    user_id: uuid.UUID,
) -> ReportSettingsPublic:
    renderer = report_repo.get_renderer(
        session=session, renderer_id=request.template_id
    )
    if renderer is None or renderer.is_archived:
        raise BusinessRuleError("Rendu introuvable ou archivé")
    if report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer.id,
        status=ReportTemplateVersionStatus.published,
    ) is None:
        raise BusinessRuleError("Le rendu doit être publié")
    settings = _settings(session=session)
    settings.default_renderer_id = renderer.id
    settings.updated_by_id = user_id
    settings.updated_at = datetime.now(timezone.utc)
    session.add(settings)
    session.commit()
    return ReportSettingsPublic.model_validate(settings)


def assign_category_renderer(
    *,
    session: Session,
    category_id: uuid.UUID,
    request: CategoryReportRendererUpdate,
) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise NotFoundError("Catégorie non trouvée")
    if request.report_renderer_id is not None:
        renderer = report_repo.get_renderer(
            session=session, renderer_id=request.report_renderer_id
        )
        if renderer is None or renderer.is_archived:
            raise BusinessRuleError("Rendu introuvable ou archivé")
        if report_repo.get_renderer_version(
            session=session,
            renderer_id=renderer.id,
            status=ReportTemplateVersionStatus.published,
        ) is None:
            raise BusinessRuleError("Le rendu doit être publié")
    category.report_renderer_id = request.report_renderer_id
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def _published_component_snapshot(
    *, session: Session, component_id: uuid.UUID | None, label: str
) -> dict[str, Any]:
    if component_id is None:
        raise BusinessRuleError(f"Aucun composant {label} par défaut")
    component = report_repo.get_component(
        session=session, component_id=component_id
    )
    version = report_repo.get_component_version(
        session=session,
        component_id=component_id,
        status=ReportTemplateVersionStatus.published,
    )
    if component is None or version is None:
        raise BusinessRuleError(f"Le composant {label} par défaut n'est pas publié")
    return {
        "id": str(component.id),
        "name": component.name,
        "version_id": str(version.id),
        "version": version.version,
        "html_source": version.html_source,
        "css_source": version.css_source,
    }


def _patient_age(date_of_birth: date, as_of: date | None = None) -> int:
    reference_date = as_of or datetime.now(timezone.utc).date()
    return reference_date.year - date_of_birth.year - (
        (reference_date.month, reference_date.day)
        < (date_of_birth.month, date_of_birth.day)
    )


def _build_snapshot(
    *, session: Session, order_id: uuid.UUID
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    workspace = result_service.get_workspace(
        session=session, order_id=order_id, include_audit=False
    )
    lab = lab_settings_service.get_settings_public(session=session)
    settings = _settings(session=session)
    subject = report_repo.get_report_subject(session=session, order_id=order_id)
    if subject is None:
        raise NotFoundError("Demande ou patient introuvable")
    _, patient, doctor, doctor_title = subject
    blockers: list[str] = []
    if workspace.total_count == 0:
        blockers.append("Aucun résultat à publier")
    for test in workspace.tests:
        for analyte in test.analytes:
            if analyte.status != ResultStatus.verified:
                blockers.append(
                    f"{test.catalog_name} — {analyte.analyte_name} n'est pas vérifié"
                )

    categories: dict[str, dict[str, Any]] = {}
    renderer_snapshots: dict[str, dict[str, Any]] = {}
    for test in workspace.tests:
        category_key = str(test.category_id or "uncategorized")
        category = categories.setdefault(
            category_key,
            {
                "id": str(test.category_id) if test.category_id else None,
                "name": test.category_name or "Sans catégorie",
                "tests": [],
            },
        )
        category["tests"].append(test.model_dump(mode="json"))
        db_category = (
            session.get(Category, test.category_id) if test.category_id else None
        )
        renderer_id = (
            db_category.report_renderer_id if db_category else None
        ) or settings.default_renderer_id
        if renderer_id is None:
            raise BusinessRuleError("Aucun rendu de rapport par défaut")
        renderer = report_repo.get_renderer(
            session=session, renderer_id=renderer_id
        )
        version = report_repo.get_renderer_version(
            session=session,
            renderer_id=renderer_id,
            status=ReportTemplateVersionStatus.published,
        )
        if renderer is None or version is None:
            raise BusinessRuleError(
                f"Le rendu de la catégorie {category['name']} n'est pas publié"
            )
        renderer_snapshots[category_key] = {
            "id": str(renderer.id),
            "name": renderer.name,
            "version_id": str(version.id),
            "version": version.version,
            "jsx_source": version.jsx_source,
            "css_source": version.css_source,
        }

    snapshot = {
        "order": {
            "id": str(workspace.order_id),
            "accession_number": workspace.accession_number,
            "status": workspace.order_status.value,
            "revision_number": workspace.revision_number,
        },
        "patient": {
            "id": str(workspace.patient_id),
            "identifier": workspace.patient_identifier,
            "name": workspace.patient_name,
            "date_of_birth": workspace.patient_date_of_birth.isoformat(),
            "age": _patient_age(workspace.patient_date_of_birth),
            "gender": workspace.patient_gender.value,
            "gender_label": GENDER_LABELS.get(
                workspace.patient_gender.value, workspace.patient_gender.value
            ),
            "context": workspace.patient_context_name,
            "phone": patient.phone,
            "address": patient.address,
        },
        "doctor": {
            "name": workspace.doctor_name or "Sans prescripteur",
            "title": doctor_title.name if doctor_title else None,
            "provenance": doctor.provenance if doctor else None,
            "phone": doctor.phone if doctor else None,
        },
        "lab": lab.model_dump(mode="json"),
        "categories": list(categories.values()),
        "totals": {
            "results": workspace.total_count,
            "verified": workspace.verified_count,
        },
    }
    template_snapshot = {
        "header": _published_component_snapshot(
            session=session, component_id=settings.default_header_id, label="d'en-tête"
        ),
        "details": _published_component_snapshot(
            session=session,
            component_id=settings.default_details_id,
            label="de détails",
        ),
        "footer": _published_component_snapshot(
            session=session, component_id=settings.default_footer_id, label="de pied de page"
        ),
        "renderers": renderer_snapshots,
    }
    return snapshot, template_snapshot, blockers


def get_preview(*, session: Session, order_id: uuid.UUID) -> ReportPreviewPublic:
    snapshot, templates, blockers = _build_snapshot(
        session=session, order_id=order_id
    )
    return ReportPreviewPublic(
        order_id=order_id,
        can_release=not blockers,
        blockers=blockers,
        snapshot=snapshot,
        template_snapshot=templates,
    )


def get_sample_preview(*, session: Session) -> ReportPreviewPublic:
    settings = _settings(session=session)
    lab = lab_settings_service.get_settings_public(session=session)
    renderer_id = settings.default_renderer_id
    if renderer_id is None:
        raise BusinessRuleError("Aucun rendu par défaut")
    renderer = report_repo.get_renderer(session=session, renderer_id=renderer_id)
    version = report_repo.get_renderer_version(
        session=session,
        renderer_id=renderer_id,
        status=ReportTemplateVersionStatus.published,
    )
    if renderer is None or version is None:
        raise BusinessRuleError("Le rendu par défaut n'est pas publié")
    snapshot = {
        "order": {
            "id": None,
            "accession_number": "KL-2026-000123",
            "status": "completed",
            "revision_number": 1,
        },
        "patient": {
            "id": None,
            "identifier": "PAT-00124",
            "name": "Aminata Traoré",
            "date_of_birth": "1987-04-12",
            "age": 39,
            "gender": "female",
            "gender_label": "Féminin",
            "context": "À jeun",
            "phone": "+223 70 12 34 56",
            "address": "Hamdallaye ACI 2000, Bamako",
        },
        "doctor": {
            "name": "Moussa Diallo",
            "title": "Dr",
            "provenance": "Clinique Les Acacias",
            "phone": "+223 20 22 33 44",
        },
        "lab": lab.model_dump(mode="json"),
        "categories": [
            {
                "id": None,
                "name": "Hématologie",
                "tests": [
                    {
                        "order_item_id": "sample",
                        "catalog_id": "sample",
                        "catalog_code": "NFS",
                        "catalog_name": "Numération formule sanguine",
                        "category_name": "Hématologie",
                        "analytes": [
                            {
                                "analyte_id": "sample-hb",
                                "analyte_code": "HB",
                                "analyte_name": "Hémoglobine",
                                "data_type": "numeric",
                                "unit_name": "g/dL",
                                "reference_text": "12,0 – 16,0",
                                "result_value": "11.4",
                                "status": "verified",
                                "is_abnormal": True,
                                "is_critical": False,
                                "verified_by_name": "Dr Fatou Keita",
                                "verified_at": "2026-06-18T10:30:00Z",
                                "comments": [],
                            }
                        ],
                    }
                ],
            }
        ],
        "totals": {"results": 1, "verified": 1},
    }
    templates = {
        "header": _published_component_snapshot(
            session=session, component_id=settings.default_header_id, label="d'en-tête"
        ),
        "details": _published_component_snapshot(
            session=session, component_id=settings.default_details_id, label="de détails"
        ),
        "footer": _published_component_snapshot(
            session=session, component_id=settings.default_footer_id, label="de pied de page"
        ),
        "renderers": {
            "uncategorized": {
                "id": str(renderer.id),
                "name": renderer.name,
                "version_id": str(version.id),
                "version": version.version,
                "jsx_source": version.jsx_source,
                "css_source": version.css_source,
            }
        },
    }
    return ReportPreviewPublic(
        can_release=False,
        blockers=["Les données d'exemple ne peuvent pas être publiées"],
        snapshot=snapshot,
        template_snapshot=templates,
    )


def _validate_email_recipient(recipient: str) -> str:
    try:
        return str(TypeAdapter(EmailStr).validate_python(recipient.strip()))
    except ValueError as exc:
        raise BusinessRuleError("Adresse e-mail invalide") from exc


def _report_email_html(report: Report, recipient_note: str | None = None) -> str:
    snapshot = dict(report.snapshot or {})
    order = dict(snapshot.get("order") or {})
    patient = dict(snapshot.get("patient") or {})
    doctor = dict(snapshot.get("doctor") or {})
    lab = dict(snapshot.get("lab") or {})

    category_sections: list[str] = []
    for category in snapshot.get("categories") or []:
        test_sections: list[str] = []
        for test in category.get("tests") or []:
            rows: list[str] = []
            for analyte in test.get("analytes") or []:
                value = analyte.get("result_value") or (
                    "Image jointe au résultat"
                    if analyte.get("image_url")
                    else "—"
                )
                flags = []
                if analyte.get("is_critical"):
                    flags.append("Critique")
                elif analyte.get("is_abnormal"):
                    flags.append("Anormal")
                comments = "; ".join(
                    str(comment.get("comment", ""))
                    for comment in analyte.get("comments") or []
                    if comment.get("comment")
                )
                rows.append(
                    "<tr>"
                    f"<td>{escape(str(analyte.get('analyte_name') or '—'))}</td>"
                    f"<td><strong>{escape(str(value))}</strong></td>"
                    f"<td>{escape(str(analyte.get('unit_name') or '—'))}</td>"
                    f"<td>{escape(str(analyte.get('reference_text') or '—'))}</td>"
                    f"<td>{escape(', '.join(flags) or 'Normal')}</td>"
                    f"<td>{escape(comments or '—')}</td>"
                    "</tr>"
                )
            test_sections.append(
                f"<h3>{escape(str(test.get('catalog_name') or 'Analyse'))}</h3>"
                '<table role="presentation" width="100%" cellspacing="0" '
                'cellpadding="7" style="border-collapse:collapse;margin-bottom:18px">'
                "<thead><tr>"
                "<th>Analyse</th><th>Résultat</th><th>Unité</th>"
                "<th>Valeurs de référence</th><th>État</th><th>Commentaires</th>"
                "</tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>"
            )
        category_sections.append(
            f"<h2>{escape(str(category.get('name') or 'Résultats'))}</h2>"
            f"{''.join(test_sections)}"
        )

    note_html = (
        '<div style="margin:16px 0;padding:12px;background:#f8fafc;'
        'border-left:3px solid #0f766e">'
        f"<strong>Message :</strong> {escape(recipient_note)}</div>"
        if recipient_note
        else ""
    )
    lab_name = escape(str(lab.get("display_name") or "Keneya Lab"))
    accession = escape(str(order.get("accession_number") or ""))
    patient_name = escape(str(patient.get("name") or ""))
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <style>
    body {{ margin:0; background:#f1f5f9; color:#172033; font-family:Arial,sans-serif; }}
    .page {{ max-width:900px; margin:24px auto; background:#fff; padding:32px; }}
    h1 {{ margin:0; color:#0f766e; font-size:24px; }}
    h2 {{ margin-top:28px; color:#0f766e; border-bottom:1px solid #cbd5e1; }}
    h3 {{ margin-bottom:8px; }}
    th {{ background:#f1f5f9; text-align:left; font-size:12px; }}
    td, th {{ border:1px solid #dbe3ec; vertical-align:top; }}
    td {{ font-size:13px; }}
    .meta {{ margin:22px 0; padding:16px; background:#f8fafc; }}
    .muted {{ color:#64748b; font-size:12px; }}
  </style>
</head>
<body>
  <div class="page">
    <h1>{lab_name}</h1>
    <p class="muted">Compte rendu d'analyses médicales — version {report.version}</p>
    <div class="meta">
      <strong>Patient :</strong> {patient_name}<br>
      <strong>Identifiant :</strong> {escape(str(patient.get("identifier") or "—"))}<br>
      <strong>Demande :</strong> {accession}<br>
      <strong>Prescripteur :</strong> {escape(str(doctor.get("name") or "—"))}
    </div>
    {note_html}
    {''.join(category_sections)}
    <p class="muted">
      Ce message contient des données médicales confidentielles. S'il ne vous est
      pas destiné, veuillez le supprimer et prévenir l'expéditeur.
    </p>
  </div>
</body>
</html>"""


def _send_report_email(
    *,
    session: Session,
    report: Report,
    recipient: str,
    recipient_note: str | None,
) -> ReportPublic:
    metadata = dict(report.delivery_metadata or {})
    attempts = list(metadata.get("attempts", []))
    attempt = {
        "channel": ReportChannel.email.value,
        "recipient": recipient,
        "recipient_note": recipient_note,
        "status": DeliveryStatus.pending.value,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "provider": "smtp",
    }
    attempts.append(attempt)
    snapshot = dict(report.snapshot or {})
    accession = str((snapshot.get("order") or {}).get("accession_number") or "")
    try:
        send_email(
            email_to=recipient,
            subject=f"Compte rendu d'analyses {accession}".strip(),
            html_content=_report_email_html(report, recipient_note),
        )
    except Exception as exc:
        attempt["status"] = DeliveryStatus.failed.value
        attempt["failed_at"] = datetime.now(timezone.utc).isoformat()
        attempt["error"] = str(exc)
        report.channel = ReportChannel.email
        report.recipient_note = recipient_note
        report.delivery_status = DeliveryStatus.failed
        report.delivery_metadata = {"attempts": attempts, "provider": "smtp"}
        session.add(report)
        session.commit()
        raise BusinessRuleError(
            "Le rapport a été publié, mais l'envoi par e-mail a échoué"
        ) from exc

    attempt["status"] = DeliveryStatus.sent.value
    attempt["sent_at"] = datetime.now(timezone.utc).isoformat()
    report.channel = ReportChannel.email
    report.recipient_note = recipient_note
    report.delivery_status = DeliveryStatus.sent
    report.delivery_metadata = {"attempts": attempts, "provider": "smtp"}
    session.add(report)
    session.commit()
    session.refresh(report)
    return ReportPublic.model_validate(report)


def release_report(
    *,
    session: Session,
    order_id: uuid.UUID,
    user_id: uuid.UUID,
    request: ReportReleaseRequest,
) -> ReportPublic:
    recipient = (
        _validate_email_recipient(request.recipient)
        if request.channel == ReportChannel.email and request.recipient
        else None
    )
    if request.channel == ReportChannel.email and recipient is None:
        raise BusinessRuleError(
            "L'adresse e-mail est obligatoire pour publier et envoyer"
        )
    if request.channel not in {
        ReportChannel.print,
        ReportChannel.portal,
        ReportChannel.email,
    }:
        raise BusinessRuleError("Canal de publication invalide")
    snapshot, templates, blockers = _build_snapshot(
        session=session, order_id=order_id
    )
    if blockers:
        raise BusinessRuleError(
            "Tous les résultats doivent être vérifiés avant publication"
        )
    for previous in report_repo.list_order_reports(
        session=session, order_id=order_id
    ):
        if not previous.is_voided:
            previous.is_voided = True
            session.add(previous)
    report = Report(
        order_id=order_id,
        version=report_repo.next_report_version(
            session=session, order_id=order_id
        ),
        released_by_id=user_id,
        channel=request.channel,
        recipient_note=request.recipient_note,
        delivery_status=(
            DeliveryStatus.sent
            if request.channel in {ReportChannel.print, ReportChannel.portal}
            else DeliveryStatus.pending
        ),
        snapshot=snapshot,
        template_snapshot=templates,
        delivery_metadata={},
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    if request.channel == ReportChannel.email and recipient:
        return _send_report_email(
            session=session,
            report=report,
            recipient=recipient,
            recipient_note=request.recipient_note,
        )
    return ReportPublic.model_validate(report)


def get_report(*, session: Session, report_id: uuid.UUID) -> ReportPublic:
    report = report_repo.get_report(session=session, report_id=report_id)
    if report is None:
        raise NotFoundError("Rapport non trouvé")
    return ReportPublic.model_validate(report)


def list_order_reports(
    *, session: Session, order_id: uuid.UUID
) -> ReportsPublic:
    reports = report_repo.list_order_reports(session=session, order_id=order_id)
    return ReportsPublic(
        data=[ReportPublic.model_validate(report) for report in reports],
        count=len(reports),
    )


def void_report(*, session: Session, report_id: uuid.UUID) -> ReportPublic:
    report = report_repo.get_report(session=session, report_id=report_id)
    if report is None:
        raise NotFoundError("Rapport non trouvé")
    report.is_voided = True
    session.add(report)
    session.commit()
    session.refresh(report)
    return ReportPublic.model_validate(report)


def deliver_report(
    *,
    session: Session,
    report_id: uuid.UUID,
    request: ReportDeliveryRequest,
) -> ReportPublic:
    report = report_repo.get_report(session=session, report_id=report_id)
    if report is None:
        raise NotFoundError("Rapport non trouvé")
    if report.is_voided:
        raise BusinessRuleError("Un rapport annulé ne peut pas être envoyé")
    if request.channel not in {ReportChannel.email, ReportChannel.whatsapp}:
        raise BusinessRuleError("Canal d'envoi invalide")
    recipient = request.recipient.strip()
    if request.channel == ReportChannel.email:
        return _send_report_email(
            session=session,
            report=report,
            recipient=_validate_email_recipient(recipient),
            recipient_note=request.recipient_note,
        )
    elif not re.fullmatch(r"\+?[0-9][0-9 .-]{6,20}", recipient):
        raise BusinessRuleError("Numéro WhatsApp invalide")
    metadata = dict(report.delivery_metadata or {})
    attempts = list(metadata.get("attempts", []))
    attempts.append(
        {
            "channel": request.channel.value,
            "recipient": recipient,
            "recipient_note": request.recipient_note,
            "status": "not_configured",
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    report.channel = request.channel
    report.recipient_note = request.recipient_note
    report.delivery_status = DeliveryStatus.pending
    report.delivery_metadata = {"attempts": attempts, "provider": "not_configured"}
    session.add(report)
    session.commit()
    session.refresh(report)
    return ReportPublic.model_validate(report)
