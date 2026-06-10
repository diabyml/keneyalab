"""add manual commission adjustments

Revision ID: 7a1c2d3e4f50
Revises: 6f9d2c1b8a7e
"""

from alembic import op

revision = "7a1c2d3e4f50"
down_revision = "6f9d2c1b8a7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE doctor_commission_adjustments
            ALTER COLUMN order_revision_id DROP NOT NULL,
            ADD COLUMN created_by_id UUID REFERENCES "user"(id),
            ADD CONSTRAINT ck_commission_adjustment_source CHECK (
                (order_revision_id IS NOT NULL) <> (created_by_id IS NOT NULL)
            )
        """
    )
    op.execute(
        """
        CREATE INDEX idx_commission_adjustments_entry_created
        ON doctor_commission_adjustments (commission_entry_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX idx_commission_adjustments_unsettled
        ON doctor_commission_adjustments (commission_entry_id)
        WHERE is_settled = FALSE
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX idx_commission_adjustments_unsettled")
    op.execute("DROP INDEX idx_commission_adjustments_entry_created")
    op.execute(
        """
        DELETE FROM audit_logs
        WHERE table_name = 'doctor_commission_adjustments'
          AND record_id IN (
              SELECT id
              FROM doctor_commission_adjustments
              WHERE order_revision_id IS NULL
          )
        """
    )
    op.execute(
        """
        DELETE FROM doctor_commission_payment_entries
        WHERE commission_adjustment_id IN (
            SELECT id
            FROM doctor_commission_adjustments
            WHERE order_revision_id IS NULL
        )
        """
    )
    op.execute(
        """
        DELETE FROM doctor_commission_adjustments
        WHERE order_revision_id IS NULL
        """
    )
    op.execute(
        """
        ALTER TABLE doctor_commission_adjustments
            DROP CONSTRAINT ck_commission_adjustment_source,
            DROP COLUMN created_by_id,
            ALTER COLUMN order_revision_id SET NOT NULL
        """
    )
