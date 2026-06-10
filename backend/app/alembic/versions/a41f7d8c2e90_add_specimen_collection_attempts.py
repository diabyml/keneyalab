"""Add specimen collection attempts and rejection audit fields.

Revision ID: a41f7d8c2e90
Revises: c7e3a91f4b20
"""

from alembic import op

revision = "a41f7d8c2e90"
down_revision = "c7e3a91f4b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE order_specimens "
        "ADD COLUMN replaces_specimen_id UUID REFERENCES order_specimens(id)"
    )
    op.execute(
        "ALTER TABLE order_specimens "
        "ADD COLUMN attempt_number INTEGER NOT NULL DEFAULT 1"
    )
    op.execute("ALTER TABLE order_specimens ADD COLUMN rejected_at TIMESTAMPTZ")
    op.execute(
        'ALTER TABLE order_specimens ADD COLUMN rejected_by UUID REFERENCES "user"(id)'
    )
    op.execute(
        "CREATE INDEX idx_order_specimens_replaces_specimen_id "
        "ON order_specimens(replaces_specimen_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX idx_order_specimens_replaces_specimen_id")
    op.execute("ALTER TABLE order_specimens DROP COLUMN rejected_by")
    op.execute("ALTER TABLE order_specimens DROP COLUMN rejected_at")
    op.execute("ALTER TABLE order_specimens DROP COLUMN attempt_number")
    op.execute("ALTER TABLE order_specimens DROP COLUMN replaces_specimen_id")
