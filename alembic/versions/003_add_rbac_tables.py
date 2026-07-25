"""003_add_rbac_tables

Revision ID: 003
Revises: 002
Create Date: 2026-07-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create permissions table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('resource', sa.Text(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_permissions_name', 'permissions', ['name'], unique=True)
    op.create_index('ix_permissions_category', 'permissions', ['category'], unique=False)

    # 2. Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('level', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_custom', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('restaurant_id', 'name', name='uq_roles_restaurant_name')
    )
    op.create_index('ix_roles_restaurant_id', 'roles', ['restaurant_id'], unique=False)
    op.create_index('ix_roles_name', 'roles', ['name'], unique=False)

    # 3. Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # 4. Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['staff.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['staff.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'], unique=False)
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_user_roles_role_id', table_name='user_roles')
    op.drop_index('ix_user_roles_user_id', table_name='user_roles')
    op.drop_table('user_roles')

    op.drop_table('role_permissions')

    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_index('ix_roles_restaurant_id', table_name='roles')
    op.drop_table('roles')

    op.drop_index('ix_permissions_category', table_name='permissions')
    op.drop_index('ix_permissions_name', table_name='permissions')
    op.drop_table('permissions')
