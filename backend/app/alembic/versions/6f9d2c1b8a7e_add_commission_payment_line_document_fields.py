"""add commission payment line document fields

Revision ID: 6f9d2c1b8a7e
Revises: 5e8c1a2b3d4f
"""

import sqlalchemy as sa
from alembic import op

revision = "6f9d2c1b8a7e"
down_revision = "5e8c1a2b3d4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for column in (
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("patient_first_name", sa.String(length=100), nullable=True),
        sa.Column("patient_last_name", sa.String(length=100), nullable=True),
        sa.Column("insured_commission_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("non_insured_commission_amount", sa.Numeric(12, 2), nullable=True),
    ):
        op.add_column("doctor_commission_payment_entries", column)

    op.execute(
        """
        UPDATE doctor_commission_payment_entries AS payment_line
        SET order_date = orders.created_at,
            patient_first_name = patients.first_name,
            patient_last_name = patients.last_name,
            insured_commission_amount = COALESCE(
                (
                    SELECT entry.insured_commission_amount
                    FROM doctor_commission_entries AS entry
                    WHERE entry.id = payment_line.commission_entry_id
                ),
                0
            ),
            non_insured_commission_amount = COALESCE(
                (
                    SELECT entry.non_insured_commission_amount
                    FROM doctor_commission_entries AS entry
                    WHERE entry.id = payment_line.commission_entry_id
                ),
                0
            )
        FROM orders
        JOIN patients ON patients.id = orders.patient_id
        WHERE orders.id = payment_line.order_id
        """
    )

    for column in (
        "order_date",
        "patient_first_name",
        "patient_last_name",
        "insured_commission_amount",
        "non_insured_commission_amount",
    ):
        op.alter_column("doctor_commission_payment_entries", column, nullable=False)


def downgrade() -> None:
    for column in (
        "non_insured_commission_amount",
        "insured_commission_amount",
        "patient_last_name",
        "patient_first_name",
        "order_date",
    ):
        op.drop_column("doctor_commission_payment_entries", column)
