"""Add report render configuration.

Revision ID: a7c9d2e4f631
Revises: 9b2c3d4e5f61
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a7c9d2e4f631"
down_revision = "9b2c3d4e5f61"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "render_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.alter_column("reports", "render_config", server_default=None)


def downgrade() -> None:
    op.drop_column("reports", "render_config")
