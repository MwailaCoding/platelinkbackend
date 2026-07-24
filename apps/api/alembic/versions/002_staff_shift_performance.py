"""Add staff, shifts, attendance, performance, reviews, and invitations tables

Revision ID: 002_staff_shift_performance
Revises: 001_initial_schema
Create Date: 2026-07-24 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_staff_shift_performance'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create Staff Table
    op.create_table(
        'staff',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('employee_id', sa.String(length=50), unique=True, nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('position', sa.String(length=100), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('salary', sa.Float(), nullable=True),
        sa.Column('shift_preferences', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('skills', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('certifications', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_staff_employee_id', 'staff', ['employee_id'])
    op.create_index('ix_staff_user_id', 'staff', ['user_id'])

    # 2. Create StaffShifts Table
    op.create_table(
        'staff_shifts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shift_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('break_start', sa.Time(), nullable=True),
        sa.Column('break_end', sa.Time(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='scheduled', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_staff_shifts_date', 'staff_shifts', ['shift_date'])
    op.create_index('ix_staff_shifts_staff_id', 'staff_shifts', ['staff_id'])

    # 3. Create StaffAttendance Table
    op.create_table(
        'staff_attendance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shift_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('staff_shifts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('check_in', sa.DateTime(timezone=True), nullable=False),
        sa.Column('check_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_in_method', sa.String(length=20), nullable=False, server_default='pin'),
        sa.Column('check_out_method', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='present', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_staff_attendance_staff_id', 'staff_attendance', ['staff_id'])

    # 4. Create StaffPerformance Table
    op.create_table(
        'staff_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=True),
        sa.Column('achieved_percentage', sa.Float(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 5. Create StaffReviews Table
    op.create_table(
        'staff_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('staff_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('review_date', sa.Date(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('strengths', sa.Text(), nullable=True),
        sa.Column('improvements', sa.Text(), nullable=True),
        sa.Column('goals', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )

    # 6. Create StaffInvitations Table
    op.create_table(
        'staff_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('token', sa.String(length=255), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False)
    )
    op.create_index('ix_staff_invitations_token', 'staff_invitations', ['token'])
    op.create_index('ix_staff_invitations_email', 'staff_invitations', ['email'])

def downgrade() -> None:
    op.drop_index('ix_staff_invitations_email', table_name='staff_invitations')
    op.drop_index('ix_staff_invitations_token', table_name='staff_invitations')
    op.drop_table('staff_invitations')

    op.drop_table('staff_reviews')
    op.drop_table('staff_performance')

    op.drop_index('ix_staff_attendance_staff_id', table_name='staff_attendance')
    op.drop_table('staff_attendance')

    op.drop_index('ix_staff_shifts_staff_id', table_name='staff_shifts')
    op.drop_index('ix_staff_shifts_date', table_name='staff_shifts')
    op.drop_table('staff_shifts')

    op.drop_index('ix_staff_user_id', table_name='staff')
    op.drop_index('ix_staff_employee_id', table_name='staff')
    op.drop_table('staff')
