"""Staff business logic service."""
import logging
from uuid import UUID
from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from apps.api.app.models.user import User
from apps.api.app.models.staff import Staff
from apps.api.app.models.role import Role
from apps.api.app.models.performance import StaffPerformance
from apps.api.app.models.shift import StaffAttendance
from apps.api.app.models.enums import UserStatus
from apps.api.app.core.auth import hash_password
from apps.api.app.core.email import send_welcome_email

logger = logging.getLogger(__name__)

class StaffService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_staff(
        self,
        restaurant_id: UUID,
        user_data: Dict[str, Any],
        staff_data: Dict[str, Any]
    ) -> Staff:
        """Create a new staff member with user account."""
        email = user_data["email"].lower().strip()

        # Check duplicate email
        stmt = select(User).where(User.email == email)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Verify role exists
        role_id = user_data["role_id"]
        role_stmt = select(Role).where(Role.id == role_id)
        role_res = await self.db.execute(role_stmt)
        role = role_res.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role specified does not exist"
            )

        raw_password = user_data.get("password") or f"TempPass_{user_data.get('pin', '1234')}!"
        hashed_pass = hash_password(raw_password)

        new_user = User(
            email=email,
            phone=user_data.get("phone"),
            password_hash=hashed_pass,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role_id=role_id,
            restaurant_id=restaurant_id,
            branch_id=user_data.get("branch_id"),
            pin=user_data.get("pin"),
            status=UserStatus.ACTIVE
        )
        self.db.add(new_user)
        await self.db.flush()

        new_staff = Staff(
            user_id=new_user.id,
            employee_id=staff_data.get("employee_id") or f"EMP-{new_user.id.hex[:6].upper()}",
            department=staff_data.get("department"),
            position=staff_data.get("position"),
            hire_date=staff_data.get("hire_date") or date.today(),
            salary=staff_data.get("salary"),
            shift_preferences=staff_data.get("shift_preferences") or [],
            skills=staff_data.get("skills") or [],
            certifications=staff_data.get("certifications") or []
        )
        self.db.add(new_staff)
        await self.db.commit()

        # Re-query with eager loading
        full_staff_stmt = (
            select(Staff)
            .options(selectinload(Staff.user).selectinload(User.role))
            .where(Staff.id == new_staff.id)
        )
        full_res = await self.db.execute(full_staff_stmt)
        staff_obj = full_res.scalar_one()

        if user_data.get("send_invite", True):
            await send_welcome_email(
                to=email,
                first_name=new_user.first_name,
                last_name=new_user.last_name,
                restaurant_name="Restaurant",
                login_url="http://localhost:3000/login",
                pin=new_user.pin or "N/A"
            )

        return staff_obj

    async def get_staff(
        self,
        staff_id: UUID,
        restaurant_id: UUID
    ) -> Optional[Staff]:
        """Get staff member by ID with restaurant scope validation."""
        stmt = (
            select(Staff)
            .join(User, Staff.user_id == User.id)
            .options(selectinload(Staff.user).selectinload(User.role))
            .where(Staff.id == staff_id, User.restaurant_id == restaurant_id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_staff_by_user(
        self,
        user_id: UUID,
        restaurant_id: UUID
    ) -> Optional[Staff]:
        """Get staff member by user ID."""
        stmt = (
            select(Staff)
            .join(User, Staff.user_id == User.id)
            .options(selectinload(Staff.user).selectinload(User.role))
            .where(Staff.user_id == user_id, User.restaurant_id == restaurant_id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_staff(
        self,
        restaurant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        role_id: Optional[UUID] = None,
        department: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List staff members with filtering and pagination."""
        stmt = (
            select(Staff)
            .join(User, Staff.user_id == User.id)
            .options(selectinload(Staff.user).selectinload(User.role))
            .where(User.restaurant_id == restaurant_id)
        )

        if status:
            stmt = stmt.where(User.status == status)
        if role_id:
            stmt = stmt.where(User.role_id == role_id)
        if department:
            stmt = stmt.where(Staff.department == department)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.email.ilike(pattern),
                    Staff.employee_id.ilike(pattern)
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.offset(skip).limit(limit)
        res = await self.db.execute(stmt)
        staff_list = res.scalars().all()

        formatted_list = []
        for s in staff_list:
            u = s.user
            item = {
                "id": s.id,
                "user_id": s.user_id,
                "employee_id": s.employee_id,
                "department": s.department,
                "position": s.position,
                "hire_date": s.hire_date,
                "salary": s.salary,
                "shift_preferences": s.shift_preferences or [],
                "skills": s.skills or [],
                "certifications": s.certifications or [],
                "status": u.status if u else "active",
                "created_at": s.created_at,
                "email": u.email if u else "",
                "first_name": u.first_name if u else "",
                "last_name": u.last_name if u else "",
                "phone": u.phone if u else None,
                "role": {"id": u.role.id, "name": u.role.name} if u and u.role else None,
                "branch": None
            }
            formatted_list.append(item)

        return formatted_list, total

    async def update_staff(
        self,
        staff_id: UUID,
        restaurant_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[Staff]:
        """Update staff member details."""
        staff = await self.get_staff(staff_id, restaurant_id)
        if not staff:
            return None

        # Fields on Staff model
        for field in ["employee_id", "department", "position", "hire_date", "salary", "shift_preferences", "skills", "certifications"]:
            if field in update_data and update_data[field] is not None:
                setattr(staff, field, update_data[field])

        # Fields on User model
        if staff.user:
            if "status" in update_data and update_data["status"] is not None:
                staff.user.status = update_data["status"]

        await self.db.commit()
        await self.db.refresh(staff)
        return staff

    async def delete_staff(
        self,
        staff_id: UUID,
        restaurant_id: UUID
    ) -> bool:
        """Soft delete staff by setting user status to INACTIVE."""
        staff = await self.get_staff(staff_id, restaurant_id)
        if not staff or not staff.user:
            return False

        staff.user.status = UserStatus.INACTIVE
        await self.db.commit()
        return True

    async def get_staff_performance(
        self,
        staff_id: UUID,
        restaurant_id: UUID,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for staff member."""
        staff = await self.get_staff(staff_id, restaurant_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff member not found")

        stmt = select(StaffPerformance).where(StaffPerformance.staff_id == staff_id)
        if period_start:
            stmt = stmt.where(StaffPerformance.period_start >= period_start)
        if period_end:
            stmt = stmt.where(StaffPerformance.period_end <= period_end)

        res = await self.db.execute(stmt)
        metrics = res.scalars().all()

        avg_rating = 0.0
        if metrics:
            ratings = [m.rating for m in metrics if m.rating is not None]
            if ratings:
                avg_rating = sum(ratings) / len(ratings)

        return {
            "staff_id": staff_id,
            "employee_id": staff.employee_id,
            "average_rating": round(avg_rating, 2),
            "total_metrics_recorded": len(metrics),
            "metrics": [
                {
                    "metric_type": m.metric_type,
                    "metric_value": m.metric_value,
                    "target_value": m.target_value,
                    "achieved_percentage": m.achieved_percentage,
                    "rating": m.rating,
                    "period_start": m.period_start,
                    "period_end": m.period_end,
                }
                for m in metrics
            ]
        }

    async def get_online_staff(
        self,
        restaurant_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get staff members currently checked in on shift."""
        stmt = (
            select(StaffAttendance)
            .join(Staff, StaffAttendance.staff_id == Staff.id)
            .join(User, Staff.user_id == User.id)
            .options(selectinload(StaffAttendance.staff).selectinload(Staff.user))
            .where(
                User.restaurant_id == restaurant_id,
                StaffAttendance.check_out.is_(None)
            )
        )
        res = await self.db.execute(stmt)
        active_attendances = res.scalars().all()

        online_staff = []
        for att in active_attendances:
            s = att.staff
            u = s.user if s else None
            online_staff.append({
                "staff_id": s.id if s else None,
                "user_id": u.id if u else None,
                "first_name": u.first_name if u else "",
                "last_name": u.last_name if u else "",
                "department": s.department if s else None,
                "position": s.position if s else None,
                "check_in": att.check_in,
                "check_in_method": att.check_in_method,
            })

        return online_staff
