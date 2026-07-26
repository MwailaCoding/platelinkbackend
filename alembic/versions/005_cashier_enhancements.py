"""Migration 005: Cashier enhancements tables (cashier_shifts, payment_transactions, digital_receipts).

Revision ID: 005
Revises: 004
Create Date: 2026-07-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create cashier_shifts table
    op.create_table(
        'cashier_shifts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('terminal_id', sa.String(length=20), nullable=False, server_default='Terminal-1'),
        sa.Column('cashier_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('opening_float', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('closing_float', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('expected_cash', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('actual_cash', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('variance', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['cashier_id'], ['staff.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cashier_shifts_cashier_id', 'cashier_shifts', ['cashier_id'])
    op.create_index('ix_cashier_shifts_status', 'cashier_shifts', ['status'])

    # 2. Create payment_transactions table
    op.create_table(
        'payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('method', sa.String(length=20), server_default='cash', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('mpesa_receipt', sa.String(length=50), nullable=True),
        sa.Column('mpesa_phone', sa.String(length=20), nullable=True),
        sa.Column('card_reference', sa.String(length=50), nullable=True),
        sa.Column('cash_received', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('cash_change', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('processed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['processed_by'], ['staff.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['shift_id'], ['cashier_shifts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payment_transactions_order_id', 'payment_transactions', ['order_id'])
    op.create_index('ix_payment_transactions_restaurant_id', 'payment_transactions', ['restaurant_id'])
    op.create_index('ix_payment_transactions_shift_id', 'payment_transactions', ['shift_id'])
    op.create_index('ix_payment_transactions_processed_by', 'payment_transactions', ['processed_by'])
    op.create_index('ix_payment_transactions_method', 'payment_transactions', ['method'])
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['status'])

    # 3. Create digital_receipts table
    op.create_table(
        'digital_receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('receipt_url', sa.String(length=255), nullable=False),
        sa.Column('sent_via', sa.String(length=20), server_default='print', nullable=False),
        sa.Column('sent_to', sa.String(length=255), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_delivered', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['staff.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_digital_receipts_order_id', 'digital_receipts', ['order_id'])
    op.create_index('ix_digital_receipts_sent_via', 'digital_receipts', ['sent_via'])

def downgrade() -> None:
    op.drop_table('digital_receipts')
    op.drop_table('payment_transactions')
    op.drop_table('cashier_shifts')
