import uuid
from datetime import datetime, timezone

from app.models.lis import DeliveryStatus, Report, ReportChannel
from app.services.report import _render_report_pdf, render_interpretation_html


def _snapshot():
    return {
        "order": {
            "id": str(uuid.uuid4()),
            "accession_number": "KL-TEST-001",
            "status": "completed",
            "revision_number": 1,
        },
        "patient": {
            "id": str(uuid.uuid4()),
            "identifier": "PAT-001",
            "name": "Aminata Diallo",
            "date_of_birth": "1992-05-04",
            "age": 34,
            "gender": "female",
            "gender_label": "Féminin",
            "context": "À jeun",
        },
        "doctor": {"name": "Dr Moussa Diallo"},
        "lab": {"display_name": "Keneya Lab"},
        "categories": [
            {
                "id": str(uuid.uuid4()),
                "name": "Hématologie",
                "tests": [
                    {
                        "order_item_id": str(uuid.uuid4()),
                        "catalog_id": str(uuid.uuid4()),
                        "catalog_code": "NFS",
                        "catalog_name": "Numération formule sanguine",
                        "analytes": [
                            {
                                "analyte_id": "hb",
                                "analyte_code": "HB",
                                "analyte_name": "Hémoglobine",
                                "data_type": "numeric",
                                "unit_name": "g/dL",
                                "reference_text": "12,0 - 16,0",
                                "result_value": "11.4",
                                "status": "verified",
                                "is_abnormal": True,
                                "comments": [],
                            }
                        ],
                    }
                ],
            }
        ],
        "totals": {"results": 1, "verified": 1},
    }


def test_render_interpretation_variables_and_strips_unsafe_html() -> None:
    html = (
        "<p>Patient : "
        '<span data-variable-kind="patient" data-variable-field="name">nom</span>'
        "</p><p>Hb : "
        '<span data-variable-kind="analyte" data-variable-id="hb" '
        'data-variable-field="result_value">résultat</span></p>'
        "<script>alert(1)</script>"
    )

    rendered, plain_text = render_interpretation_html(html, _snapshot())

    assert rendered is not None
    assert "Aminata Diallo" in rendered
    assert "11.4" in rendered
    assert "script" not in rendered
    assert plain_text is not None and "Aminata Diallo" in plain_text


def test_render_report_pdf_uses_html_interpretation() -> None:
    snapshot = _snapshot()
    snapshot["interpretation"] = {
        "html": "<p><strong>Interprétation riche</strong></p>",
        "plain_text": "Interprétation riche",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by_name": "Dr Fatou Keita",
    }
    report = Report(
        order_id=uuid.uuid4(),
        version=1,
        released_by_id=uuid.uuid4(),
        released_at=datetime.now(timezone.utc),
        channel=ReportChannel.whatsapp,
        delivery_status=DeliveryStatus.pending,
        snapshot=snapshot,
        template_snapshot={},
        render_config={},
        delivery_metadata={},
    )

    pdf = _render_report_pdf(report)

    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
