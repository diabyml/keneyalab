"""Align clinical renderer columns.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
"""

import sqlalchemy as sa
from alembic import op

revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


CLINICAL_RENDERER_VERSION_ID = "54444444-4444-4444-8444-444444444444"

CLINICAL_RENDERER_CSS = (
    ".report-category{margin:18px 0}"
    ".report-category h2{font-size:14px;color:#0f766e;border-bottom:1px solid #cbd5e1;padding-bottom:6px}"
    ".clinical-table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:11px}"
    ".clinical-table th,.clinical-table td{padding:7px 6px;border-bottom:1px solid #e2e8f0;text-align:left;vertical-align:top}"
    ".clinical-table th{color:#475569;font-weight:600}"
    ".clinical-table th:nth-child(1),.clinical-table td:nth-child(1){width:24%}"
    ".clinical-table th:nth-child(2),.clinical-table td:nth-child(2){width:14%}"
    ".clinical-table th:nth-child(3),.clinical-table td:nth-child(3){width:10%}"
    ".clinical-table th:nth-child(4),.clinical-table td:nth-child(4){width:52%}"
    ".clinical-table td{overflow-wrap:anywhere}"
    ".clinical-table .report-test-heading th{width:auto}"
    ".result-abnormal{font-weight:700;color:#b45309}"
    ".result-critical{font-weight:800;color:#b91c1c}"
)


def upgrade() -> None:
    op.get_bind().execute(
        sa.text(
            """
            UPDATE report_renderer_versions
            SET css_source = :css_source
            WHERE id = :version_id
            """
        ),
        {
            "version_id": CLINICAL_RENDERER_VERSION_ID,
            "css_source": CLINICAL_RENDERER_CSS,
        },
    )


def downgrade() -> None:
    pass
