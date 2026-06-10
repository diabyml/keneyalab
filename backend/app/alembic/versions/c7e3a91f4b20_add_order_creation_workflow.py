"""Add complete order creation workflow.

Revision ID: c7e3a91f4b20
Revises: 2f4c8a1b9d0e
"""

from alembic import context, op

revision = "c7e3a91f4b20"
down_revision = "2f4c8a1b9d0e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with context.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE specimen_status ADD VALUE IF NOT EXISTS 'pending' BEFORE 'collected'"
        )
    op.execute(
        "CREATE TYPE payment_transaction_status AS ENUM ('completed', 'refunded')"
    )
    op.execute(
        """
        CREATE TABLE daily_sequences (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sequence_date DATE NOT NULL,
            sequence_type VARCHAR(30) NOT NULL,
            current_value INTEGER NOT NULL DEFAULT 0,
            CONSTRAINT uq_daily_sequence UNIQUE (sequence_date, sequence_type)
        )
        """
    )
    op.execute("ALTER TABLE orders ADD COLUMN accession_number VARCHAR(30)")
    op.execute(
        """
        UPDATE orders target
        SET accession_number = numbered.accession_number
        FROM (
            SELECT id,
                'ORD-' || TO_CHAR(created_at, 'YYYYMMDD') || '-' ||
                LPAD(ROW_NUMBER() OVER (
                    PARTITION BY created_at::date ORDER BY created_at, id
                )::text, 4, '0') AS accession_number
            FROM orders
        ) numbered
        WHERE numbered.id = target.id
        """
    )
    op.execute("ALTER TABLE orders ALTER COLUMN accession_number SET NOT NULL")
    op.execute(
        "ALTER TABLE orders ADD CONSTRAINT uq_orders_accession_number UNIQUE (accession_number)"
    )
    op.execute("ALTER TABLE orders ALTER COLUMN doctor_id DROP NOT NULL")
    op.execute(
        "ALTER TABLE order_specimens ALTER COLUMN status SET DEFAULT 'pending'::specimen_status"
    )
    op.execute(
        "ALTER TABLE order_specimens ADD COLUMN required_volume_ml NUMERIC(6, 2)"
    )
    op.execute("ALTER TABLE order_specimens ADD COLUMN collection_instructions TEXT")
    op.execute(
        "ALTER TABLE order_items ADD COLUMN insurance_provider_name VARCHAR(255)"
    )
    op.execute(
        """
        CREATE TABLE order_item_specimens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_item_id UUID NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
            order_specimen_id UUID NOT NULL REFERENCES order_specimens(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_order_item_specimen UNIQUE (order_item_id, order_specimen_id)
        )
        """
    )
    op.execute(
        """
        INSERT INTO order_item_specimens (order_item_id, order_specimen_id)
        SELECT id, order_specimen_id
        FROM order_items
        WHERE order_specimen_id IS NOT NULL
        """
    )
    op.execute("DROP INDEX IF EXISTS idx_order_items_order_specimen_id")
    op.execute("ALTER TABLE order_items DROP COLUMN order_specimen_id")
    op.execute("ALTER TABLE invoices ADD COLUMN discount_reason TEXT")
    op.execute(
        """
        CREATE TABLE payment_transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            payment_method_id UUID NOT NULL REFERENCES payment_methods(id),
            status payment_transaction_status NOT NULL DEFAULT 'completed',
            collected_by_id UUID NOT NULL REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX idx_payment_transactions_invoice_id ON payment_transactions(invoice_id)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE order_items ADD COLUMN order_specimen_id UUID")
    op.execute(
        """
        UPDATE order_items oi
        SET order_specimen_id = links.order_specimen_id
        FROM (
            SELECT DISTINCT ON (order_item_id) order_item_id, order_specimen_id
            FROM order_item_specimens
            ORDER BY order_item_id, created_at
        ) links
        WHERE links.order_item_id = oi.id
        """
    )
    op.execute(
        "ALTER TABLE order_items ADD CONSTRAINT order_items_order_specimen_id_fkey "
        "FOREIGN KEY (order_specimen_id) REFERENCES order_specimens(id)"
    )
    op.execute(
        "CREATE INDEX idx_order_items_order_specimen_id ON order_items(order_specimen_id)"
    )
    op.execute("DROP TABLE payment_transactions")
    op.execute("ALTER TABLE invoices DROP COLUMN discount_reason")
    op.execute("DROP TABLE order_item_specimens")
    op.execute("ALTER TABLE order_items DROP COLUMN insurance_provider_name")
    op.execute("ALTER TABLE order_specimens DROP COLUMN collection_instructions")
    op.execute("ALTER TABLE order_specimens DROP COLUMN required_volume_ml")
    op.execute(
        "ALTER TABLE order_specimens ALTER COLUMN status SET DEFAULT 'collected'::specimen_status"
    )
    op.execute("ALTER TABLE orders ALTER COLUMN doctor_id SET NOT NULL")
    op.execute("ALTER TABLE orders DROP CONSTRAINT uq_orders_accession_number")
    op.execute("ALTER TABLE orders DROP COLUMN accession_number")
    op.execute("DROP TABLE daily_sequences")
    op.execute("DROP TYPE payment_transaction_status")
