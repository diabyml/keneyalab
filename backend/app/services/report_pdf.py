from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import BusinessRuleError
from app.models.lis import Report


def render_report_pdf(*, report: Report) -> bytes:
    if not settings.REPORT_RENDERER_URL:
        raise BusinessRuleError(
            "Le service de rendu PDF des rapports n'est pas configuré"
        )

    try:
        response = httpx.post(
            settings.REPORT_RENDERER_URL,
            json=_renderer_payload(report=report),
            timeout=45,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        message = _renderer_error_message(exc.response)
        raise BusinessRuleError(message) from exc
    except httpx.HTTPError as exc:
        raise BusinessRuleError(
            "Le service de rendu PDF des rapports est indisponible"
        ) from exc

    content_type = response.headers.get("content-type", "")
    if "application/pdf" not in content_type:
        raise BusinessRuleError("Le service de rendu n'a pas retourné un PDF")
    if not response.content:
        raise BusinessRuleError("Le rapport PDF généré est vide")
    return response.content


def _renderer_payload(*, report: Report) -> dict[str, Any]:
    return {
        "snapshot": report.snapshot,
        "template_snapshot": report.template_snapshot,
        "render_config": report.render_config,
        "voided": report.is_voided,
    }


def _renderer_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    detail = payload.get("detail") if isinstance(payload, dict) else None
    if detail:
        return f"Le rendu PDF du rapport a échoué : {detail}"
    return "Le rendu PDF du rapport a échoué"
