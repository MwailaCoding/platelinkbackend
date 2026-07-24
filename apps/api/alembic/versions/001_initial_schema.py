"""Initial migration: Phase 1 RBAC Schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create Enums
    user_status = postgresql.ENUM('pending', 'active', 'inactive', 'suspended', name='userstatus')
    user_status.create(op.get_bind(), checkfirst=True)

    restaurant_size = postgresql.ENUM('small', 'medium', 'large', 'enterprise', name='restaurantsize')
    restaurant_size.create(op.get_bind(), checkfirst=True)

    permission_action = postgresql.ENUM('create', 'read', 'update', 'delete', 'manage', name='permissionaction')
    permission_action.create(op.get_bind(), checkfirst=True)

    permission_category = postgresql.ENUM('dashboard', 'orders', 'menu', 'tables', 'staff', 'payments', 'reports', 'settings', name='permissioncategory')
    permission_category.create(op.get_bind(), checkfirst=True)

    # 2. Create Restaurants Table
    op.create_table(
        'restaurants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('size', sa.Enum('small', 'medium', 'large', 'enterprise', name='restaurantsize'), nullable=False, server_default='small'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('slug', name='uq_restaurants_slug')
    )
    op.create_index('idx_restaurants_slug', 'restaurants', ['slug'])

    # 3. Create Branches Table
    op.create_table(
        'branches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('idx_branches_restaurant_id', 'branches', ['restaurant_id'])

    # 4. Create Permissions Table
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.Enum('create', 'read', 'update', 'delete', 'manage', name='permissionaction'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.Enum('dashboard', 'orders', 'menu', 'tables', 'staff', 'payments', 'reports', 'settings', name='permissioncategory'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('name', name='uq_permissions_name')
    )
    op.create_index('idx_permissions_name', 'permissions', ['name'])

    # 5. Create Roles Table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_custom', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('restaurant_size', sa.Enum('small', 'medium', 'large', 'enterprise', name='restaurantsize'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('restaurant_id', 'name', name='uq_roles_restaurant_name')
    )
    op.create_index('idx_roles_restaurant_id', 'roles', ['restaurant_id'])

    # 6. Create RolePermissions Junction Table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 7. Create Users Table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('pin', sa.String(length=4), nullable=True),
        sa.Column('status', sa.Enum('pending', 'active', 'inactive', 'suspended', name='userstatus'), nullable=False, server_default='pending'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_restaurant_id', 'users', ['restaurant_id'])
    op.create_index('idx_users_role_id', 'users', ['role_id'])
    op.create_index('idx_users_status', 'users', ['status'])

def downgrade() -> None:
    op.drop_index('idx_users_status', table_name='users')
    op.drop_index('idx_users_role_id', table_name='users')
    op.drop_index('idx_users_restaurant_id', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')

    op.drop_table('role_permissions')

    op.drop_index('idx_roles_restaurant_id', table_name='roles')
    op.drop_table('roles')

    op.drop_index('idx_permissions_name', table_name='permissions')
    op.drop_table('permissions')

    op.drop_index('idx_branches_restaurant_id', table_name='branches')
    op.drop_table('branches')

    op.drop_index('idx_restaurants_slug', table_name='restaurants')
    op.drop_table('restaurants')

    op.execute("DROP TYPE IF EXISTS permissioncategory")
    op.execute("DROP TYPE IF EXISTS permissionaction")
    op.execute("DROP TYPE IF EXISTS restaurantsize")
    op.execute("DROP TYPE IF EXISTS userstatus")
