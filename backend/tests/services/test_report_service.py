import uuid
from datetime import date

import pytest

from app.core.exceptions import BusinessRuleError
from app.models.lis import Report, ReportChannel
from app.services.report import (
    _patient_age,
    _report_email_html,
    _validate_email_recipient,
    sanitize_html,
    validate_css,
    validate_jsx,
)


def test_sanitize_html_removes_scripts_and_event_handlers() -> None:
    source = (
        '<div class="header" onclick="steal()">Bonjour '
        "<script>alert(1)</script><strong>Keneya</strong></div>"
    )

    rendered = sanitize_html(source)

    assert "<script" not in rendered
    assert "onclick" not in rendered
    assert "<strong>Keneya</strong>" in rendered
    assert "alert(1)" not in rendered


@pytest.mark.parametrize(
    "source",
    [
        '@import url("https://example.com/theme.css");',
        "div { background: expression(alert(1)); }",
        "div { background-image: url(javascript:alert(1)); }",
        "div { background-image: url(https://tracker.example/pixel); }",
    ],
)
def test_validate_css_rejects_unsafe_constructs(source: str) -> None:
    with pytest.raises(BusinessRuleError):
        validate_css(source)


@pytest.mark.parametrize(
    "source",
    [
        'import React from "react"; function Renderer() { return <div /> }',
        "function Renderer() { fetch('/api/v1/users'); return <div /> }",
        "function Renderer() { return <div>{document.cookie}</div> }",
        "function Other() { return <div /> }",
    ],
)
def test_validate_jsx_rejects_app_and_network_access(source: str) -> None:
    with pytest.raises(BusinessRuleError):
        validate_jsx(source)


def test_validate_jsx_accepts_renderer_contract() -> None:
    source = (
        "function Renderer({ category, ReportKit }) { "
        "return <ReportKit.ClinicalTable category={category} /> }"
    )

    assert validate_jsx(source) == source


def test_report_email_uses_immutable_snapshot_and_escapes_values() -> None:
    report = Report(
        order_id=uuid.uuid4(),
        released_by_id=uuid.uuid4(),
        channel=ReportChannel.email,
        snapshot={
            "order": {"accession_number": "KL-001"},
            "patient": {"name": "Aminata <Traoré>", "identifier": "PAT-1"},
            "doctor": {"name": "Dr Diallo"},
            "lab": {"display_name": "Keneya Lab"},
            "categories": [
                {
                    "name": "Bactériologie",
                    "tests": [
                        {
                            "catalog_name": "Antibiogramme",
                            "analytes": [
                                {
                                    "analyte_name": "Amoxicilline",
                                    "result_value": "Sensible",
                                    "unit_name": None,
                                    "reference_text": None,
                                    "is_abnormal": False,
                                    "comments": [],
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    )

    html = _report_email_html(report, "À remettre au patient")

    assert "KL-001" in html
    assert "Antibiogramme" in html
    assert "Amoxicilline" in html
    assert "Sensible" in html
    assert "Aminata &lt;Traoré&gt;" in html
    assert "À remettre au patient" in html


def test_validate_email_recipient_rejects_invalid_address() -> None:
    with pytest.raises(BusinessRuleError, match="Adresse e-mail invalide"):
        _validate_email_recipient("not-an-email")


@pytest.mark.parametrize(
    ("date_of_birth", "as_of", "expected"),
    [
        (date(2000, 6, 20), date(2026, 6, 20), 26),
        (date(2000, 6, 21), date(2026, 6, 20), 25),
        (date(2000, 2, 29), date(2026, 2, 28), 25),
        (date(2000, 2, 29), date(2026, 3, 1), 26),
    ],
)
def test_patient_age(
    date_of_birth: date, as_of: date, expected: int
) -> None:
    assert _patient_age(date_of_birth, as_of) == expected
