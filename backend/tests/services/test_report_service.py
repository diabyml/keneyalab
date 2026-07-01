import uuid
from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import pytest

from app.core.exceptions import BusinessRuleError
from app.models.lis import Report, ReportChannel
from app.services.report import (
    _apply_render_config,
    _patient_age,
    _report_email_html,
    _validate_email_recipient,
    sanitize_html,
    validate_css,
    validate_jsx,
)


def _load_migration(name: str) -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "app" / "alembic" / "versions" / name
    spec = spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _render_config_snapshot() -> dict:
    return {
        "order": {"accession_number": "KL-001"},
        "patient": {"name": "Aminata"},
        "doctor": {"name": "Dr Diallo"},
        "lab": {"display_name": "Keneya Lab"},
        "interpretation": {"html": "<p>Conclusion clinique.</p>"},
        "categories": [
            {
                "id": "cat-a",
                "name": "Biochimie",
                "tests": [
                    {
                        "order_item_id": "item-a",
                        "catalog_name": "Créatinine",
                        "analytes": [
                            {"analyte_id": "crea", "analyte_name": "Créatinine"},
                            {"analyte_id": "uree", "analyte_name": "Urée"},
                        ],
                    }
                ],
            },
            {
                "id": "cat-b",
                "name": "Coagulation",
                "tests": [
                    {
                        "order_item_id": "item-b",
                        "catalog_name": "TP - INR",
                        "analytes": [
                            {"analyte_id": "tp", "analyte_name": "TP"},
                            {"analyte_id": "inr", "analyte_name": "INR"},
                        ],
                    }
                ],
            },
        ],
    }


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


@pytest.mark.parametrize(
    "migration_name",
    [
        "d1e2f3a4b5c6_add_antibiogramme_report_renderer.py",
        "e2f3a4b5c6d7_remove_antibiogramme_comments_column.py",
    ],
)
def test_builtin_antibiogramme_renderer_sources_are_valid(
    migration_name: str,
) -> None:
    migration = _load_migration(migration_name)

    assert (
        validate_jsx(migration.ANTIBIOGRAMME_RENDERER_JSX)
        == migration.ANTIBIOGRAMME_RENDERER_JSX
    )
    assert (
        validate_css(migration.ANTIBIOGRAMME_RENDERER_CSS)
        == migration.ANTIBIOGRAMME_RENDERER_CSS
    )
    assert "Commentaires" not in migration.ANTIBIOGRAMME_RENDERER_JSX
    assert "antibio-comment" not in migration.ANTIBIOGRAMME_RENDERER_CSS


def test_builtin_clinical_renderer_columns_are_fixed() -> None:
    migration = _load_migration("f3a4b5c6d7e8_align_clinical_renderer_columns.py")

    assert (
        validate_css(migration.CLINICAL_RENDERER_CSS) == migration.CLINICAL_RENDERER_CSS
    )
    assert "table-layout:fixed" in migration.CLINICAL_RENDERER_CSS
    assert "th:nth-child(1)" in migration.CLINICAL_RENDERER_CSS
    assert "td:nth-child(4)" in migration.CLINICAL_RENDERER_CSS


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


def test_apply_render_config_orders_filters_and_keeps_page_breaks() -> None:
    snapshot, config = _apply_render_config(
        _render_config_snapshot(),
        {
            "section_order": ["cat-b", "interpretation", "footer"],
            "category_order": ["cat-b"],
            "category_page_breaks": {"cat-b": True, "cat-a": False},
            "interpretation_page_break": True,
            "footer_spacing_mm": 12,
            "hidden_analyte_ids": ["inr", "uree"],
        },
    )

    assert config == {
        "section_order": ["cat-b", "interpretation", "cat-a"],
        "category_order": ["cat-b", "cat-a"],
        "category_page_breaks": {"cat-b": True},
        "interpretation_page_break": True,
        "footer_spacing_mm": 12,
        "hidden_analyte_ids": ["inr", "uree"],
    }
    assert [category["id"] for category in snapshot["categories"]] == [
        "cat-b",
        "cat-a",
    ]
    assert snapshot["categories"][0]["tests"][0]["analytes"] == [
        {"analyte_id": "tp", "analyte_name": "TP"}
    ]
    assert snapshot["categories"][1]["tests"][0]["analytes"] == [
        {"analyte_id": "crea", "analyte_name": "Créatinine"}
    ]


def test_apply_render_config_removes_empty_tests_and_categories() -> None:
    snapshot, _ = _apply_render_config(
        _render_config_snapshot(),
        {"hidden_analyte_ids": ["tp", "inr"]},
    )

    assert [category["id"] for category in snapshot["categories"]] == ["cat-a"]


def test_apply_render_config_rejects_unknown_category() -> None:
    with pytest.raises(BusinessRuleError, match="catégorie inconnue"):
        _apply_render_config(
            _render_config_snapshot(),
            {"category_order": ["missing"]},
        )


def test_apply_render_config_rejects_unknown_analyte() -> None:
    with pytest.raises(BusinessRuleError, match="ligne de résultat inconnue"):
        _apply_render_config(
            _render_config_snapshot(),
            {"hidden_analyte_ids": ["missing"]},
        )


def test_apply_render_config_accepts_missing_config() -> None:
    snapshot, config = _apply_render_config(_render_config_snapshot(), None)

    assert [category["id"] for category in snapshot["categories"]] == [
        "cat-a",
        "cat-b",
    ]
    assert config["section_order"] == ["cat-a", "cat-b", "interpretation"]
    assert config["interpretation_page_break"] is False
    assert config["footer_spacing_mm"] == 4
    assert config["hidden_analyte_ids"] == []


def test_apply_render_config_accepts_zero_footer_spacing() -> None:
    _, config = _apply_render_config(
        _render_config_snapshot(),
        {"footer_spacing_mm": 0},
    )

    assert config["footer_spacing_mm"] == 0


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
def test_patient_age(date_of_birth: date, as_of: date, expected: int) -> None:
    assert _patient_age(date_of_birth, as_of) == expected
