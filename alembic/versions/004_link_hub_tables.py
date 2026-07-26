"""004_link_hub_tables

Revision ID: 004
Revises: 003
Create Date: 2026-07-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create links table
    op.create_table(
        'links',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.Text(), server_default='primary', nullable=False),
        sa.Column('slug', sa.Text(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('custom_domain', sa.Text(), nullable=True),
        sa.Column('domain_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.UniqueConstraint('custom_domain')
    )
    op.create_index('ix_links_restaurant_id', 'links', ['restaurant_id'], unique=False)
    op.create_index('ix_links_type', 'links', ['type'], unique=False)
    op.create_index('ix_links_slug', 'links', ['slug'], unique=False)
    op.create_index('ix_links_custom_domain', 'links', ['custom_domain'], unique=False)

    # 2. Create qr_codes table
    op.create_table(
        'qr_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('table_number', sa.Text(), nullable=False),
        sa.Column('qr_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('qr_image_url', sa.Text(), nullable=True),
        sa.Column('scan_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('order_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_scanned', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_qr_codes_restaurant_id', 'qr_codes', ['restaurant_id'], unique=False)
    op.create_index('ix_qr_codes_branch_id', 'qr_codes', ['branch_id'], unique=False)
    op.create_index('ix_qr_codes_table_number', 'qr_codes', ['table_number'], unique=False)

    # 3. Create link_analytics table
    op.create_table(
        'link_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('link_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('views', sa.Integer(), server_default='0', nullable=False),
        sa.Column('clicks', sa.Integer(), server_default='0', nullable=False),
        sa.Column('conversions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('source', sa.Text(), server_default='qr', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['link_id'], ['links.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('link_id', 'date', 'source', name='uq_link_analytics_link_date_source')
    )
    op.create_index('ix_link_analytics_link_id', 'link_analytics', ['link_id'], unique=False)
    op.create_index('ix_link_analytics_date', 'link_analytics', ['date'], unique=False)
    op.create_index('ix_link_analytics_source', 'link_analytics', ['source'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_link_analytics_source', table_name='link_analytics')
    op.drop_index('ix_link_analytics_date', table_name='link_analytics')
    op.drop_index('ix_link_analytics_link_id', table_name='link_analytics')
    op.drop_table('link_analytics')

    op.drop_index('ix_qr_codes_table_number', table_name='qr_codes')
    op.drop_index('ix_qr_codes_branch_id', table_name='qr_codes')
    op.drop_index('ix_qr_codes_restaurant_id', table_name='qr_codes')
    op.drop_table('qr_codes')

    op.drop_index('ix_links_custom_domain', table_name='links')
    op.drop_index('ix_links_slug', table_name='links')
    op.drop_index('ix_links_type', table_name='links')
    op.drop_index('ix_links_restaurant_id', table_name='links')
    op.drop_table('links')
