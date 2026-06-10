"""Add audited order revisions.

Revision ID: f6b7c8d9e0a1
Revises: 8d3cd52e6e37
"""

from alembic import op

revision = "f6b7c8d9e0a1"
down_revision = "8d3cd52e6e37"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE orders ADD COLUMN revision_number INTEGER NOT NULL DEFAULT 1")
    op.execute(
        """
        CREATE TABLE order_revisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            revision_number INTEGER NOT NULL CHECK (revision_number >= 1),
            correction_reason TEXT NOT NULL,
            old_values JSONB NOT NULL,
            new_values JSONB NOT NULL,
            effects JSONB NOT NULL DEFAULT '{}'::jsonb,
            performed_by_id UUID NOT NULL REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_order_revision UNIQUE (order_id, revision_number)
        )
        """
    )
    op.execute("CREATE INDEX idx_order_revisions_order_id ON order_revisions(order_id)")

    op.execute("ALTER TABLE order_items ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute(
        "ALTER TABLE order_items ADD COLUMN revision_id UUID REFERENCES order_revisions(id)"
    )
    op.execute(
        "ALTER TABLE order_items ADD COLUMN source_catalog_ids JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute(
        "UPDATE order_items SET source_catalog_ids = jsonb_build_array(catalog_id::text)"
    )
    op.execute(
        "CREATE INDEX idx_order_items_active ON order_items(order_id) WHERE is_active = TRUE"
    )

    op.execute(
        "ALTER TABLE order_specimens ADD COLUMN is_superseded BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE order_specimens ADD COLUMN superseded_revision_id UUID "
        "REFERENCES order_revisions(id)"
    )
    op.execute(
        "ALTER TABLE analyte_results ADD COLUMN is_superseded BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE analyte_results ADD COLUMN superseded_revision_id UUID "
        "REFERENCES order_revisions(id)"
    )

    op.execute(
        """
        CREATE TABLE customer_credits (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id UUID NOT NULL REFERENCES orders(id),
            source_invoice_id UUID NOT NULL REFERENCES invoices(id),
            order_revision_id UUID NOT NULL REFERENCES order_revisions(id),
            amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
            reason TEXT NOT NULL,
            is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
            created_by_id UUID NOT NULL REFERENCES "user"(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE doctor_commission_adjustments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            commission_entry_id UUID NOT NULL REFERENCES doctor_commission_entries(id),
            order_revision_id UUID NOT NULL REFERENCES order_revisions(id),
            amount NUMERIC(12, 2) NOT NULL,
            reason TEXT NOT NULL,
            is_settled BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE doctor_commission_adjustments")
    op.execute("DROP TABLE customer_credits")
    op.execute("ALTER TABLE analyte_results DROP COLUMN superseded_revision_id")
    op.execute("ALTER TABLE analyte_results DROP COLUMN is_superseded")
    op.execute("ALTER TABLE order_specimens DROP COLUMN superseded_revision_id")
    op.execute("ALTER TABLE order_specimens DROP COLUMN is_superseded")
    op.execute("ALTER TABLE order_items DROP COLUMN source_catalog_ids")
    op.execute("ALTER TABLE order_items DROP COLUMN revision_id")
    op.execute("ALTER TABLE order_items DROP COLUMN is_active")
    op.execute("DROP TABLE order_revisions")
    op.execute("ALTER TABLE orders DROP COLUMN revision_number")
