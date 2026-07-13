"""kitchen_system

Revision ID: 8ee6ea06d509
Revises: 7ff6ea06d508
Create Date: 2026-06-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8ee6ea06d509'
down_revision: Union[str, None] = '7ff6ea06d508'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create kitchen_stations table
    op.create_table(
        'kitchen_stations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('restaurant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('station_type', sa.String(length=50), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create station_prep_times table
    op.create_table(
        'station_prep_times',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('restaurant_id', sa.UUID(), nullable=False),
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('item_category', sa.String(length=50), nullable=False),
        sa.Column('default_seconds', sa.Integer(), server_default='600', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['station_id'], ['kitchen_stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create kitchen_routing_rules table
    op.create_table(
        'kitchen_routing_rules',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('restaurant_id', sa.UUID(), nullable=False),
        sa.Column('source_station_id', sa.UUID(), nullable=True),
        sa.Column('target_station_id', sa.UUID(), nullable=False),
        sa.Column('item_keyword', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_station_id'], ['kitchen_stations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_station_id'], ['kitchen_stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Create kitchen_display_settings table
    op.create_table(
        'kitchen_display_settings',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('restaurant_id', sa.UUID(), nullable=False),
        sa.Column('station_id', sa.UUID(), nullable=False),
        sa.Column('sound_alerts_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('new_order_volume', sa.Integer(), server_default='70', nullable=False),
        sa.Column('ready_order_volume', sa.Integer(), server_default='80', nullable=False),
        sa.Column('theme', sa.String(length=20), server_default='dark', nullable=False),
        sa.Column('font_size', sa.String(length=10), server_default='large', nullable=False),
        sa.Column('show_timer', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('show_modifiers', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('auto_accept', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('prep_time_buffer_percent', sa.Integer(), server_default='10', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['station_id'], ['kitchen_stations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Add station_id to menu_items table
    op.add_column('menu_items', sa.Column('station_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_menu_items_station_id', 'menu_items', 'kitchen_stations', ['station_id'], ['id'], ondelete='SET NULL')

    # 6. Add kitchen_station_id to staff table
    op.add_column('staff', sa.Column('kitchen_station_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_staff_kitchen_station_id', 'staff', 'kitchen_stations', ['kitchen_station_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_staff_kitchen_station_id', 'staff', type_='foreignkey')
    op.drop_column('staff', 'kitchen_station_id')

    op.drop_constraint('fk_menu_items_station_id', 'menu_items', type_='foreignkey')
    op.drop_column('menu_items', 'station_id')

    op.drop_table('kitchen_display_settings')
    op.drop_table('kitchen_routing_rules')
    op.drop_table('station_prep_times')
    op.drop_table('kitchen_stations')
