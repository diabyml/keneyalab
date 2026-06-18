"""Customize analytes per ordered test.

Revision ID: 1e5f8a9b0c21
Revises: 0d4e7f8a9b10
"""

from alembic import op

revision = "1e5f8a9b0c21"
down_revision = "0d4e7f8a9b10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ADD COLUMN analyte_id UUID REFERENCES analytes(id)"
    )
    op.execute(
        """
        UPDATE order_catalog_item_analytes target
        SET analyte_id = source.analyte_id
        FROM catalog_item_analytes source
        WHERE source.id = target.catalog_item_analyte_id
        """
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ALTER COLUMN analyte_id SET NOT NULL"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ALTER COLUMN catalog_item_analyte_id DROP NOT NULL"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ADD COLUMN removed_revision_id UUID REFERENCES order_revisions(id)"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes ADD COLUMN removal_reason TEXT"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "DROP CONSTRAINT uq_order_catalog_item_analyte"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ADD CONSTRAINT uq_order_catalog_item_analyte "
        "UNIQUE (order_item_id, analyte_id)"
    )
    op.execute(
        "CREATE INDEX idx_order_catalog_item_analytes_active "
        "ON order_catalog_item_analytes(order_item_id) WHERE is_active = TRUE"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_order_catalog_item_analytes_active")
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "DROP CONSTRAINT uq_order_catalog_item_analyte"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ADD CONSTRAINT uq_order_catalog_item_analyte "
        "UNIQUE (order_item_id, catalog_item_analyte_id)"
    )
    op.execute(
        "ALTER TABLE order_catalog_item_analytes "
        "ALTER COLUMN catalog_item_analyte_id SET NOT NULL"
    )
    op.execute("ALTER TABLE order_catalog_item_analytes DROP COLUMN removal_reason")
    op.execute(
        "ALTER TABLE order_catalog_item_analytes DROP COLUMN removed_revision_id"
    )
    op.execute("ALTER TABLE order_catalog_item_analytes DROP COLUMN is_active")
    op.execute("ALTER TABLE order_catalog_item_analytes DROP COLUMN analyte_id")
