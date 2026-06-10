"""extend validation rules v1

Revision ID: b6a8c2d9e4f1
Revises: 7f8a9b0c1d2e
Create Date: 2026-06-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b6a8c2d9e4f1"
down_revision = "7f8a9b0c1d2e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "validation_rules",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "validation_rules",
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("validation_rules", sa.Column("regex_pattern", sa.Text(), nullable=True))
    op.add_column("validation_rules", sa.Column("validation_message", sa.Text(), nullable=True))
    op.add_column(
        "validation_rules",
        sa.Column("allowed_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "validation_rules",
        sa.Column("abnormal_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "validation_rules",
        sa.Column("critical_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(
        "idx_validation_rules_active",
        "validation_rules",
        ["analyte_id", "is_active", "priority"],
    )
    op.alter_column("validation_rules", "is_active", server_default=None)
    op.alter_column("validation_rules", "is_required", server_default=None)


def downgrade():
    op.drop_index("idx_validation_rules_active", table_name="validation_rules")
    op.drop_column("validation_rules", "critical_values")
    op.drop_column("validation_rules", "abnormal_values")
    op.drop_column("validation_rules", "allowed_values")
    op.drop_column("validation_rules", "validation_message")
    op.drop_column("validation_rules", "regex_pattern")
    op.drop_column("validation_rules", "is_required")
    op.drop_column("validation_rules", "is_active")
