"""normalize panel catalog prices

Revision ID: 2f4c8a1b9d0e
Revises: b6a8c2d9e4f1
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op

revision = "2f4c8a1b9d0e"
down_revision = "b6a8c2d9e4f1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE catalog SET price = 0.00 WHERE type = 'panel'")


def downgrade():
    pass
