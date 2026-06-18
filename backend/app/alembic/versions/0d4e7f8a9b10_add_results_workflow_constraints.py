"""Add results workflow constraints.

Revision ID: 0d4e7f8a9b10
Revises: 7a1c2d3e4f50
"""

from alembic import op

revision = "0d4e7f8a9b10"
down_revision = "7a1c2d3e4f50"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE critical_notifications
        ADD COLUMN acknowledged_by_id UUID REFERENCES "user"(id)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_active_analyte_result
        ON analyte_results(order_item_id, analyte_id, specimen_id)
        WHERE is_superseded = FALSE
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_open_critical_notification
        ON critical_notifications(analyte_result_id)
        WHERE acknowledged = FALSE
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_open_critical_notification")
    op.execute("DROP INDEX IF EXISTS uq_active_analyte_result")
    op.execute(
        "ALTER TABLE critical_notifications DROP COLUMN acknowledged_by_id"
    )
