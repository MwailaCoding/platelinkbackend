"""Shift and attendance business logic service."""
import logging
from uuid import UUID
from datetime import date, time, datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from apps.api.app.models.shift import StaffShift, StaffAttendance
from apps.api.app.models.staff import Staff
from apps.api.app.models.user import User

logger = logging.getLogger(__name__)

class ShiftService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_shift(
        self,
        staff_id: UUID,
        restaurant_id: UUID,
        shift_data: Dict[str, Any]
    ) -> StaffShift:
        """Create shift for staff member."""
        # Verify staff exists in restaurant
        stmt = (
            select(Staff)
            .join(User, Staff.user_id == User.id)
            .where(Staff.id == staff_id, User.restaurant_id == restaurant_id)
        )
        res = await self.db.execute(stmt)
        staff = res.scalar_one_or_none()
        if not staff:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found in this restaurant"
            )

        shift = StaffShift(
            staff_id=staff_id,
            shift_date=shift_data["shift_date"],
            start_time=shift_data["start_time"],
            end_time=shift_data["end_time"],
            break_start=shift_data.get("break_start"),
            break_end=shift_data.get("break_end"),
            status=shift_data.get("status", "scheduled"),
            notes=shift_data.get("notes"),
            created_by=shift_data.get("created_by")
        )
        self.db.add(shift)
        await self.db.commit()
        await self.db.refresh(shift)
        return shift

    async def get_shift(
        self,
        shift_id: UUID,
        restaurant_id: UUID
    ) -> Optional[StaffShift]:
        """Get shift by ID."""
        stmt = (
            select(StaffShift)
            .join(Staff, StaffShift.staff_id == Staff.id)
            .join(User, Staff.user_id == User.id)
            .where(StaffShift.id == shift_id, User.restaurant_id == restaurant_id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_shifts(
        self,
        restaurant_id: UUID,
        start_date: date,
        end_date: date,
        staff_id: Optional[UUID] = None
    ) -> List[StaffShift]:
        """List shifts in a date range."""
        stmt = (
            select(StaffShift)
            .join(Staff, StaffShift.staff_id == Staff.id)
            .join(User, Staff.user_id == User.id)
            .where(
                User.restaurant_id == restaurant_id,
                StaffShift.shift_date >= start_date,
                StaffShift.shift_date <= end_date
            )
        )
        if staff_id:
            stmt = stmt.where(StaffShift.staff_id == staff_id)

        stmt = stmt.order_by(StaffShift.shift_date, StaffShift.start_time)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def update_shift(
        self,
        shift_id: UUID,
        restaurant_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[StaffShift]:
        """Update shift details."""
        shift = await self.get_shift(shift_id, restaurant_id)
        if not shift:
            return None

        for field in ["shift_date", "start_time", "end_time", "break_start", "break_end", "status", "notes"]:
            if field in update_data and update_data[field] is not None:
                setattr(shift, field, update_data[field])

        await self.db.commit()
        await self.db.refresh(shift)
        return shift

    async def delete_shift(
        self,
        shift_id: UUID,
        restaurant_id: UUID
    ) -> bool:
        """Delete shift."""
        shift = await self.get_shift(shift_id, restaurant_id)
        if not shift:
            return False

        await self.db.delete(shift)
        await self.db.commit()
        return True

    async def check_in(
        self,
        user_or_staff_id: UUID,
        restaurant_id: UUID,
        method: str = "pin",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        shift_id: Optional[UUID] = None
    ) -> StaffAttendance:
        """Staff check-in process."""
        # Find staff profile
        staff_stmt = (
            select(Staff)
            .join(User, Staff.user_id == User.id)
            .where(
                or_(Staff.id == user_or_staff_id, Staff.user_id == user_or_staff_id),
                User.restaurant_id == restaurant_id
            )
        )
        res = await self.db.execute(staff_stmt)
        staff = res.scalar_one_or_none()

        if not staff:
            raise HTTPException(status_code=404, detail="Staff member profile not found")

        # Check if already checked in
        active_stmt = select(StaffAttendance).where(
            StaffAttendance.staff_id == staff.id,
            StaffAttendance.check_out.is_(None)
        )
        active_res = await self.db.execute(active_stmt)
        if active_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Staff member is already checked in")

        attendance = StaffAttendance(
            staff_id=staff.id,
            shift_id=shift_id,
            check_in=datetime.now(timezone.utc),
            check_in_method=method,
            status="present",
            notes=f"Lat: {latitude}, Long: {longitude}" if latitude and longitude else None
        )
        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def check_out(
        self,
        user_or_staff_id: UUID,
        restaurant_id: UUID,
        method: str = "pin"
    ) -> StaffAttendance:
        """Staff check-out process."""
        staff_stmt = (
            select(Staff)
            .join(User, Staff.user_id == User.id)
            .where(
                or_(Staff.id == user_or_staff_id, Staff.user_id == user_or_staff_id),
                User.restaurant_id == restaurant_id
            )
        )
        res = await self.db.execute(staff_stmt)
        staff = res.scalar_one_or_none()

        if not staff:
            raise HTTPException(status_code=404, detail="Staff member profile not found")

        active_stmt = select(StaffAttendance).where(
            StaffAttendance.staff_id == staff.id,
            StaffAttendance.check_out.is_(None)
        )
        active_res = await self.db.execute(active_stmt)
        attendance = active_res.scalar_one_or_none()

        if not attendance:
            raise HTTPException(status_code=400, detail="No active check-in found for staff member")

        attendance.check_out = datetime.now(timezone.utc)
        attendance.check_out_method = method
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def get_attendance(
        self,
        staff_id: UUID,
        start_date: date,
        end_date: date
    ) -> List[StaffAttendance]:
        """Get staff attendance history."""
        stmt = (
            select(StaffAttendance)
            .where(
                StaffAttendance.staff_id == staff_id,
                func.date(StaffAttendance.check_in) >= start_date,
                func.date(StaffAttendance.check_in) <= end_date
            )
            .order_by(StaffAttendance.check_in.desc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_shift_summary(
        self,
        restaurant_id: UUID,
        target_date: date
    ) -> Dict[str, Any]:
        """Get daily shift summary for restaurant."""
        shifts = await self.list_shifts(restaurant_id, target_date, target_date)
        scheduled_count = len(shifts)
        completed_count = sum(1 for s in shifts if s.status == "completed")
        in_progress_count = sum(1 for s in shifts if s.status == "in_progress")

        # Get total checked in currently
        online_stmt = (
            select(func.count(StaffAttendance.id))
            .join(Staff, StaffAttendance.staff_id == Staff.id)
            .join(User, Staff.user_id == User.id)
            .where(
                User.restaurant_id == restaurant_id,
                func.date(StaffAttendance.check_in) == target_date,
                StaffAttendance.check_out.is_(None)
            )
        )
        online_res = await self.db.execute(online_stmt)
        currently_online = online_res.scalar_one()

        return {
            "date": target_date,
            "total_scheduled": scheduled_count,
            "completed_shifts": completed_count,
            "in_progress_shifts": in_progress_count,
            "currently_online_staff": currently_online,
            "shifts": [
                {
                    "id": s.id,
                    "staff_id": s.staff_id,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "status": s.status,
                }
                for s in shifts
            ]
        }
