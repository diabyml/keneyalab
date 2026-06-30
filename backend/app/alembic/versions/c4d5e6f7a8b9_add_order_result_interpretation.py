"""Add order result interpretation.

Revision ID: c4d5e6f7a8b9
Revises: b8e2c4d6f910
"""

from alembic import op

revision = "c4d5e6f7a8b9"
down_revision = "b8e2c4d6f910"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE orders ADD COLUMN interpretation_html TEXT")
    op.execute(
        'ALTER TABLE orders ADD COLUMN interpretation_updated_by_id UUID REFERENCES "user"(id)'
    )
    op.execute("ALTER TABLE orders ADD COLUMN interpretation_updated_at TIMESTAMPTZ")


def downgrade() -> None:
    op.execute("ALTER TABLE orders DROP COLUMN interpretation_updated_at")
    op.execute("ALTER TABLE orders DROP COLUMN interpretation_updated_by_id")
    op.execute("ALTER TABLE orders DROP COLUMN interpretation_html")
