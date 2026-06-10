"""add default commission rates to finance settings

Revision ID: 8d3cd52e6e37
Revises: d4f7a2c9e610
Create Date: 2026-06-06 21:55:02.631335

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8d3cd52e6e37"
down_revision = "d4f7a2c9e610"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "finance_settings",
        sa.Column(
            "default_commission_rate",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
        ),
    )
    op.add_column(
        "finance_settings",
        sa.Column(
            "default_insurance_commission_rate",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("finance_settings", "default_insurance_commission_rate")
    op.drop_column("finance_settings", "default_commission_rate")
