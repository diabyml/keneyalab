"""Add invoice numbering, line snapshots, refunds, and transfers.

Revision ID: b52e8f9d3a01
Revises: a41f7d8c2e90
"""

from alembic import op

revision = "b52e8f9d3a01"
down_revision = "a41f7d8c2e90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE invoices ADD COLUMN invoice_number VARCHAR(30)")
    op.execute(
        """
        UPDATE invoices target
        SET invoice_number = numbered.invoice_number
        FROM (
            SELECT id,
                'FAC-' || TO_CHAR(created_at, 'YYYYMMDD') || '-' ||
                LPAD(DENSE_RANK() OVER (
                    PARTITION BY created_at::date
                    ORDER BY order_id
                )::text, 4, '0') AS invoice_number
            FROM invoices
        ) numbered
        WHERE numbered.id = target.id
        """
    )
    op.execute("ALTER TABLE invoices ALTER COLUMN invoice_number SET NOT NULL")
    op.execute(
        "ALTER TABLE invoices ADD CONSTRAINT uq_invoice_number_version "
        "UNIQUE (invoice_number, version)"
    )
    op.execute(
        """
        INSERT INTO daily_sequences (
            id, sequence_date, sequence_type, current_value
        )
        SELECT gen_random_uuid(), created_at::date, 'invoice', COUNT(DISTINCT order_id)
        FROM invoices
        GROUP BY created_at::date
        ON CONFLICT (sequence_date, sequence_type)
        DO UPDATE SET current_value = GREATEST(
            daily_sequences.current_value, EXCLUDED.current_value
        )
        """
    )
    op.execute(
        """
        CREATE TABLE invoice_lines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            order_item_id UUID NOT NULL REFERENCES order_items(id),
            catalog_code VARCHAR(100) NOT NULL,
            catalog_name VARCHAR(255) NOT NULL,
            amount NUMERIC(12, 2) NOT NULL,
            is_covered_by_insurance BOOLEAN NOT NULL DEFAULT FALSE,
            insurance_provider_name VARCHAR(255),
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        INSERT INTO invoice_lines (
            invoice_id, order_item_id, catalog_code, catalog_name, amount,
            is_covered_by_insurance, insurance_provider_name, sort_order
        )
        SELECT
            i.id, oi.id, c.code, c.name, oi.price_charged,
            oi.is_covered_by_insurance, oi.insurance_provider_name, oi.sort_order
        FROM invoices i
        JOIN order_items oi ON oi.order_id = i.order_id
        JOIN catalog c ON c.id = oi.catalog_id
        """
    )
    op.execute("CREATE INDEX idx_invoice_lines_invoice_id ON invoice_lines(invoice_id)")
    op.execute(
        """
        CREATE TABLE payment_refunds (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            payment_id UUID NOT NULL REFERENCES payment_transactions(id) ON DELETE CASCADE,
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            payment_method_id UUID NOT NULL REFERENCES payment_methods(id),
            reason TEXT NOT NULL,
            refunded_by_id UUID NOT NULL REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_payment_refunds_payment_id ON payment_refunds(payment_id)"
    )
    op.execute(
        """
        CREATE TABLE invoice_balance_transfers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_invoice_id UUID NOT NULL REFERENCES invoices(id),
            target_invoice_id UUID NOT NULL REFERENCES invoices(id),
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            created_by_id UUID NOT NULL REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_invoice_transfer_distinct
                CHECK (source_invoice_id <> target_invoice_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_invoice_transfers_source "
        "ON invoice_balance_transfers(source_invoice_id)"
    )
    op.execute(
        "CREATE INDEX idx_invoice_transfers_target "
        "ON invoice_balance_transfers(target_invoice_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE invoice_balance_transfers")
    op.execute("DROP TABLE payment_refunds")
    op.execute("DROP TABLE invoice_lines")
    op.execute("ALTER TABLE invoices DROP CONSTRAINT uq_invoice_number_version")
    op.execute("ALTER TABLE invoices DROP COLUMN invoice_number")
