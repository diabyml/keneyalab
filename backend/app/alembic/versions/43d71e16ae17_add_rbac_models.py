"""add_rbac_models

Revision ID: 43d71e16ae17
Revises: fe56fa70289e
Create Date: 2026-05-31 15:13:50.965885

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '43d71e16ae17'
down_revision = 'fe56fa70289e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('permissions',
    sa.Column('resource', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('action', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('resource', 'action', name='uq_permissions_resource_action')
    )
    op.create_table('roles',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('is_default', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_roles_name')
    )
    op.create_table('role_permissions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('role_id', sa.Uuid(), nullable=False),
    sa.Column('permission_id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permissions')
    )
    op.create_table('user_roles',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('role_id', sa.Uuid(), nullable=False),
    sa.Column('assigned_by_id', sa.Uuid(), nullable=True),  # nullable + SET NULL
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['assigned_by_id'], ['user.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')
