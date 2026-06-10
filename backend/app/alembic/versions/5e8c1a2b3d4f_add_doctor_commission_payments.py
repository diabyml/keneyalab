"""add doctor commission payment workflow

Revision ID: 5e8c1a2b3d4f
Revises: f6b7c8d9e0a1
"""

import sqlalchemy as sa
from alembic import op

revision = "5e8c1a2b3d4f"
down_revision = "f6b7c8d9e0a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "doctor_commission_payments",
        sa.Column("payment_method_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "doctor_commission_payments",
        sa.Column("reference", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "doctor_commission_payments",
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_commission_payment_method",
        "doctor_commission_payments",
        "payment_methods",
        ["payment_method_id"],
        ["id"],
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("commission_adjustment_id", sa.Uuid(), nullable=True),
    )
    op.alter_column(
        "doctor_commission_payment_entries",
        "commission_entry_id",
        existing_type=sa.Uuid(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_commission_payment_adjustment",
        "doctor_commission_payment_entries",
        "doctor_commission_adjustments",
        ["commission_adjustment_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_payment_adjustment",
        "doctor_commission_payment_entries",
        ["commission_payment_id", "commission_adjustment_id"],
    )
    op.create_check_constraint(
        "ck_commission_payment_line_source",
        "doctor_commission_payment_entries",
        "(commission_entry_id IS NOT NULL) <> (commission_adjustment_id IS NOT NULL)",
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("order_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("accession_number", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("invoice_number", sa.String(length=30), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("line_type", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("insured_net_amount", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("non_insured_net_amount", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "doctor_commission_payment_entries",
        sa.Column("source_created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_commission_payment_line_order",
        "doctor_commission_payment_entries",
        "orders",
        ["order_id"],
        ["id"],
    )
    op.execute(
        """
        UPDATE doctor_commission_payment_entries AS payment_line
        SET order_id = entry.order_id,
            accession_number = orders.accession_number,
            invoice_number = invoices.invoice_number,
            line_type = 'entry',
            description = 'Commission',
            insured_net_amount = entry.insured_net_amount,
            non_insured_net_amount = entry.non_insured_net_amount,
            amount = entry.commission_amount,
            source_created_at = entry.created_at
        FROM doctor_commission_entries AS entry
        JOIN orders ON orders.id = entry.order_id
        JOIN invoices ON invoices.order_id = orders.id AND invoices.is_voided = false
        WHERE payment_line.commission_entry_id = entry.id
        """
    )
    for column in (
        "order_id",
        "accession_number",
        "invoice_number",
        "line_type",
        "description",
        "insured_net_amount",
        "non_insured_net_amount",
        "amount",
        "source_created_at",
    ):
        op.alter_column(
            "doctor_commission_payment_entries", column, nullable=False
        )
    op.execute(
        """
        UPDATE doctor_commission_payments
        SET payment_method_id = (
            SELECT id FROM payment_methods
            WHERE is_deleted = false ORDER BY created_at LIMIT 1
        )
        WHERE payment_method_id IS NULL
        """
    )
    op.alter_column(
        "doctor_commission_payments",
        "payment_method_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_commission_payment_line_order",
        "doctor_commission_payment_entries",
        type_="foreignkey",
    )
    for column in (
        "source_created_at",
        "amount",
        "non_insured_net_amount",
        "insured_net_amount",
        "description",
        "line_type",
        "invoice_number",
        "accession_number",
        "order_id",
    ):
        op.drop_column("doctor_commission_payment_entries", column)
    op.drop_constraint(
        "ck_commission_payment_line_source",
        "doctor_commission_payment_entries",
        type_="check",
    )
    op.drop_constraint(
        "uq_payment_adjustment",
        "doctor_commission_payment_entries",
        type_="unique",
    )
    op.drop_constraint(
        "fk_commission_payment_adjustment",
        "doctor_commission_payment_entries",
        type_="foreignkey",
    )
    op.drop_column("doctor_commission_payment_entries", "commission_adjustment_id")
    op.alter_column(
        "doctor_commission_payment_entries",
        "commission_entry_id",
        existing_type=sa.Uuid(),
        nullable=False,
    )
    op.drop_constraint(
        "fk_commission_payment_method",
        "doctor_commission_payments",
        type_="foreignkey",
    )
    op.drop_column("doctor_commission_payments", "note")
    op.drop_column("doctor_commission_payments", "reference")
    op.drop_column("doctor_commission_payments", "payment_method_id")
