"""007_cashier_pin_access

Revision ID: 007
Revises: 006
Create Date: 2026-07-26 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Add PIN columns to staff table if they don't exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_staff_cols = [c['name'] for c in inspector.get_columns('staff')]

    if 'cashier_pin' not in existing_staff_cols:
        op.add_column('staff', sa.Column('cashier_pin', sa.String(length=4), nullable=True))
    if 'pin_set_at' not in existing_staff_cols:
        op.add_column('staff', sa.Column('pin_set_at', sa.DateTime(timezone=True), nullable=True))
    if 'pin_attempts' not in existing_staff_cols:
        op.add_column('staff', sa.Column('pin_attempts', sa.Integer(), server_default='0', nullable=False))
    if 'pin_locked_at' not in existing_staff_cols:
        op.add_column('staff', sa.Column('pin_locked_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Create cashier_sessions table
    tables = inspector.get_table_names()
    if 'cashier_sessions' not in tables:
        op.create_table(
            'cashier_sessions',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('terminal_id', sa.String(length=50), nullable=True),
            sa.Column('logged_in_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('logged_out_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['staff.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_cashier_sessions_user_id', 'cashier_sessions', ['user_id'], unique=False)
        op.create_index('ix_cashier_sessions_status', 'cashier_sessions', ['status'], unique=False)
        op.create_index('ix_cashier_sessions_last_activity_at', 'cashier_sessions', ['last_activity_at'], unique=False)

def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'cashier_sessions' in tables:
        op.drop_index('ix_cashier_sessions_last_activity_at', table_name='cashier_sessions')
        op.drop_index('ix_cashier_sessions_status', table_name='cashier_sessions')
        op.drop_index('ix_cashier_sessions_user_id', table_name='cashier_sessions')
        op.drop_table('cashier_sessions')

    existing_staff_cols = [c['name'] for c in inspector.get_columns('staff')]
    if 'pin_locked_at' in existing_staff_cols:
        op.drop_column('staff', 'pin_locked_at')
    if 'pin_attempts' in existing_staff_cols:
        op.drop_column('staff', 'pin_attempts')
    if 'pin_set_at' in existing_staff_cols:
        op.drop_column('staff', 'pin_set_at')
    if 'cashier_pin' in existing_staff_cols:
        op.drop_column('staff', 'cashier_pin')
