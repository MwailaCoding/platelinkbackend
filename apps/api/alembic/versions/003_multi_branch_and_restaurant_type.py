"""Add multi-branch and restaurant type fields to database schema

Revision ID: 003
Revises: 002
Create Date: 2026-07-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Upgrade restaurants table
    op.add_column('restaurants', sa.Column('type', sa.String(length=50), nullable=False, server_default='casual_dining'))
    op.add_column('restaurants', sa.Column('is_multi_branch', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('restaurants', sa.Column('parent_restaurant_id', sa.Uuid(), sa.ForeignKey('restaurants.id', ondelete='SET NULL'), nullable=True))
    op.add_column('restaurants', sa.Column('logo_url', sa.String(length=255), nullable=True))
    op.add_column('restaurants', sa.Column('primary_color', sa.String(length=7), nullable=False, server_default='#F97316'))
    op.add_column('restaurants', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))

    # Upgrade branches table
    op.add_column('branches', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('branches', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('branches', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('branches', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('branches', sa.Column('manager_id', sa.Uuid(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('branches', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('branches', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_unique_constraint('uq_branches_restaurant_name', 'branches', ['restaurant_id', 'name'])

def downgrade() -> None:
    op.drop_constraint('uq_branches_restaurant_name', 'branches', type_='unique')
    op.drop_column('branches', 'updated_at')
    op.drop_column('branches', 'is_active')
    op.drop_column('branches', 'manager_id')
    op.drop_column('branches', 'email')
    op.drop_column('branches', 'phone')
    op.drop_column('branches', 'city')
    op.drop_column('branches', 'address')

    op.drop_column('restaurants', 'updated_at')
    op.drop_column('restaurants', 'primary_color')
    op.drop_column('restaurants', 'logo_url')
    op.drop_column('restaurants', 'parent_restaurant_id')
    op.drop_column('restaurants', 'is_multi_branch')
    op.drop_column('restaurants', 'type')
