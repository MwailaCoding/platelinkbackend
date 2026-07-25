from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import json
from pydantic import BaseModel

from app.core.deps import get_db
from models import Restaurant, Table as Tables, Reservations, Waitlist, ReservationTimeSlots, Staff
from app.core.deps import get_current_user as get_current_restaurant, get_current_active_staff as get_current_staff

router = APIRouter(prefix="/reservations", tags=["Reservations"])

# ============================================================
# SCHEMAS
# ============================================================

class CreateReservationRequest(BaseModel):
    table_id: Optional[str] = None
    reservation_time: str
    duration_minutes: int = 90
    party_size: int
    guest_name: str
    guest_phone: str
    guest_email: Optional[str] = None
    special_requests: Optional[str] = None
    occasion: Optional[str] = None
    payment_method: Optional[str] = None

class CancelReservationRequest(BaseModel):
    reason: Optional[str] = None

class SeatReservationRequest(BaseModel):
    table_id: Optional[str] = None

class AddToWaitlistRequest(BaseModel):
    guest_name: str
    guest_phone: str
    party_size: int

class SeatWaitlistRequest(BaseModel):
    table_id: str

class ReservationSettingsRequest(BaseModel):
    auto_release_minutes: int = 15
    require_deposit_for_party_size: int = 6
    deposit_amount: int = 1000
    max_reservation_days_ahead: int = 30
    min_cancel_hours: int = 2
    no_show_penalty: int = 500

# ============================================================
# MOCKS
# ============================================================

# Mock celery task decorator
class CeleryMock:
    def task(self, f):
        f.apply_async = lambda args, countdown=0: None
        return f

celery = CeleryMock()

def get_reservation_time_slots(restaurant_id, weekday):
    # Mock return default slots
    class Slot:
        def __init__(self):
            from datetime import time
            self.start_time = time(18, 0)
    return [Slot()]

def get_restaurant_settings(restaurant_id):
    return {
        "auto_release_minutes": 15,
        "require_deposit_for_party_size": 6,
        "deposit_amount": 1000,
        "max_reservation_days_ahead": 30,
        "min_cancel_hours": 2,
        "no_show_penalty": 500
    }

def update_restaurant_setting(restaurant_id, key, val):
    pass

async def process_deposit_payment(amount, phone_number, reservation_id):
    class PaymentMock:
        id = None
    return PaymentMock()

async def refund_deposit(payment_id):
    pass

def send_reservation_confirmation(guest_phone, guest_email, reservation, restaurant):
    pass

async def send_cancellation_confirmation(guest_phone, reservation, restaurant):
    pass

def send_no_show_notification(phone, guest_name, restaurant_name):
    pass

def send_waitlist_confirmation(guest_phone, guest_name, restaurant):
    pass

async def send_table_ready_notification(phone, guest_name, restaurant_name):
    pass

class Orders: # Mock for turnover query
    restaurant_id = None
    status = None
    completed_at = None

# ============================================================
# RESERVATION CRUD
# ============================================================

@router.get("/available-slots")
async def get_available_slots(
    date: str,
    party_size: int,
    duration_minutes: int = 90,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Get available reservation time slots for a given date"""
    target_date = datetime.strptime(date, "%Y-%m-%d")
    start_of_day = target_date.replace(hour=0, minute=0, second=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59)
    
    available_tables = db.query(Tables).filter(
        Tables.restaurant_id == restaurant.id,
        Tables.capacity >= party_size,
        Tables.is_active == True
    ).all()
    
    existing_reservations = db.query(Reservations).filter(
        Reservations.restaurant_id == restaurant.id,
        Reservations.reservation_time.between(start_of_day, end_of_day),
        Reservations.status.in_(['confirmed', 'seated'])
    ).all()
    
    time_slots = get_reservation_time_slots(restaurant.id, target_date.weekday())
    
    available_slots = []
    for slot in time_slots:
        slot_time = datetime.combine(target_date, slot.start_time)
        slot_end = slot_time + timedelta(minutes=duration_minutes)
        
        is_available = True
        for reservation in existing_reservations:
            res_start = reservation.reservation_time
            if res_start.tzinfo is None:
                import datetime as dt
                res_start = res_start.replace(tzinfo=dt.timezone.utc)
            if slot_time.tzinfo is None:
                import datetime as dt
                slot_time = slot_time.replace(tzinfo=dt.timezone.utc)
            if slot_end.tzinfo is None:
                import datetime as dt
                slot_end = slot_end.replace(tzinfo=dt.timezone.utc)
                
            res_end = res_start + timedelta(minutes=reservation.duration_minutes)
            
            if (slot_time < res_end and slot_end > res_start):
                is_available = False
                break
        
        if is_available:
            available_slots.append({
                "time": slot_time.strftime("%H:%M"),
                "available_tables": len(available_tables)
            })
    
    return {"date": date, "available_slots": available_slots}


@router.post("/create")
async def create_reservation(
    request: CreateReservationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Create a new table reservation"""
    reservation_start = datetime.fromisoformat(request.reservation_time)
    reservation_end = reservation_start + timedelta(minutes=request.duration_minutes)
    
    settings = get_restaurant_settings(restaurant.id)
    
    if request.table_id:
        conflicting = db.query(Reservations).filter(
            Reservations.restaurant_id == restaurant.id,
            Reservations.table_id == request.table_id,
            Reservations.reservation_time < reservation_end,
            Reservations.reservation_time + timedelta(minutes=request.duration_minutes) > reservation_start,
            Reservations.status.in_(['confirmed', 'seated'])
        ).first()
        
        if conflicting:
            raise HTTPException(400, "Table already reserved for this time")
    
    deposit_amount = 0
    if request.party_size >= settings.get('require_deposit_for_party_size', 6):
        deposit_amount = settings.get('deposit_amount', 1000)
    
    reservation = Reservations(
        restaurant_id=restaurant.id,
        table_id=request.table_id,
        guest_name=request.guest_name,
        guest_phone=request.guest_phone,
        guest_email=request.guest_email,
        party_size=request.party_size,
        reservation_time=reservation_start,
        duration_minutes=request.duration_minutes,
        special_requests=request.special_requests,
        occasion=request.occasion,
        deposit_amount=deposit_amount,
        status='confirmed'
    )
    db.add(reservation)
    db.flush()
    
    if deposit_amount > 0 and request.payment_method:
        payment = await process_deposit_payment(
            amount=deposit_amount,
            phone_number=request.guest_phone,
            reservation_id=reservation.id
        )
        reservation.deposit_paid = True
        reservation.deposit_payment_id = payment.id
    
    db.commit()
    
    background_tasks.add_task(
        send_reservation_confirmation,
        guest_phone=request.guest_phone,
        guest_email=request.guest_email,
        reservation=reservation,
        restaurant=restaurant
    )
    
    schedule_auto_release(reservation.id, reservation_start, settings.get('auto_release_minutes', 15))
    
    return {"success": True, "reservation_id": reservation.id}


@router.put("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: str,
    request: CancelReservationRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    """Cancel a reservation"""
    reservation = db.query(Reservations).filter(
        Reservations.id == reservation_id,
        Reservations.restaurant_id == restaurant.id
    ).first()
    
    if not reservation:
        raise HTTPException(404, "Reservation not found")
    
    settings = get_restaurant_settings(restaurant.id)
    hours_before = settings.get('min_cancel_hours', 2)
    
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    cancel_deadline = reservation.reservation_time - timedelta(hours=hours_before)
    if cancel_deadline.tzinfo is None:
        cancel_deadline = cancel_deadline.replace(tzinfo=dt.timezone.utc)
    
    if now > cancel_deadline and reservation.deposit_paid:
        reservation.status = 'cancelled'
        reservation.cancelled_at = now
    else:
        reservation.status = 'cancelled'
        reservation.cancelled_at = now
        if reservation.deposit_paid:
            await refund_deposit(reservation.deposit_payment_id)
    
    db.commit()
    await send_cancellation_confirmation(
        guest_phone=reservation.guest_phone,
        reservation=reservation,
        restaurant=restaurant
    )
    
    return {"success": True}


@router.post("/{reservation_id}/mark-no-show")
async def mark_no_show(
    reservation_id: str,
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    import datetime as dt
    reservation = db.query(Reservations).filter(
        Reservations.id == reservation_id
    ).first()
    
    if not reservation:
        raise HTTPException(404, "Reservation not found")
    
    reservation.status = 'no_show'
    reservation.no_show_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    return {"success": True}


@router.post("/{reservation_id}/seat")
async def seat_reservation(
    reservation_id: str,
    request: SeatReservationRequest,
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    import datetime as dt
    reservation = db.query(Reservations).filter(
        Reservations.id == reservation_id
    ).first()
    
    if not reservation:
        raise HTTPException(404, "Reservation not found")
    
    reservation.status = 'seated'
    reservation.seated_at = dt.datetime.now(dt.timezone.utc)
    
    table = db.query(Tables).filter(Tables.id == reservation.table_id).first()
    if table:
        table.status = 'occupied'
    
    db.commit()
    return {"success": True}


# ============================================================
# WAITLIST MANAGEMENT
# ============================================================

@router.get("/waitlist")
async def get_waitlist(
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    waitlist = db.query(Waitlist).filter(
        Waitlist.restaurant_id == restaurant.id,
        Waitlist.status == 'waiting'
    ).order_by(Waitlist.joined_at).all()
    
    avg_turnover = get_average_table_turnover(restaurant.id, db)
    
    for idx, entry in enumerate(waitlist):
        entry.position = idx + 1
        entry.estimated_wait_minutes = (idx + 1) * avg_turnover
        
        db.query(Waitlist).filter(Waitlist.id == entry.id).update({
            "position": entry.position,
            "estimated_wait_minutes": entry.estimated_wait_minutes
        })
    
    db.commit()
    
    return {
        "waitlist": waitlist,
        "current_wait_time": avg_turnover * len(waitlist) if waitlist else 0
    }


@router.post("/waitlist/add")
async def add_to_waitlist(
    request: AddToWaitlistRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    existing = db.query(Waitlist).filter(
        Waitlist.restaurant_id == restaurant.id,
        Waitlist.guest_phone == request.guest_phone,
        Waitlist.status == 'waiting'
    ).first()
    
    if existing:
        raise HTTPException(400, "Guest already on waitlist")
    
    waitlist_entry = Waitlist(
        restaurant_id=restaurant.id,
        guest_name=request.guest_name,
        guest_phone=request.guest_phone,
        party_size=request.party_size,
        status='waiting'
    )
    db.add(waitlist_entry)
    db.commit()
    
    background_tasks.add_task(
        send_waitlist_confirmation,
        guest_phone=request.guest_phone,
        guest_name=request.guest_name,
        restaurant=restaurant
    )
    
    return {"success": True, "waitlist_id": waitlist_entry.id}


@router.post("/waitlist/{waitlist_id}/notify")
async def notify_waitlist_guest(
    waitlist_id: str,
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    import datetime as dt
    waitlist_entry = db.query(Waitlist).filter(
        Waitlist.id == waitlist_id
    ).first()
    
    if not waitlist_entry:
        raise HTTPException(404, "Waitlist entry not found")
    
    waitlist_entry.status = 'notified'
    waitlist_entry.notified_at = dt.datetime.now(dt.timezone.utc)
    waitlist_entry.sms_sent = True
    waitlist_entry.sms_sent_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    
    # Mocking restaurant.name for now since we don't fetch it explicitly here
    await send_table_ready_notification(
        phone=waitlist_entry.guest_phone,
        guest_name=waitlist_entry.guest_name,
        restaurant_name="The Restaurant"
    )
    
    return {"success": True}


@router.post("/waitlist/{waitlist_id}/seat")
async def seat_waitlist_guest(
    waitlist_id: str,
    request: SeatWaitlistRequest,
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    import datetime as dt
    waitlist_entry = db.query(Waitlist).filter(
        Waitlist.id == waitlist_id
    ).first()
    
    if not waitlist_entry:
        raise HTTPException(404, "Waitlist entry not found")
    
    waitlist_entry.status = 'seated'
    waitlist_entry.seated_at = dt.datetime.now(dt.timezone.utc)
    
    table = db.query(Tables).filter(Tables.id == request.table_id).first()
    if table:
        table.status = 'occupied'
    
    db.commit()
    
    return {"success": True}


# ============================================================
# WAIT TIME CALCULATION
# ============================================================

def get_average_table_turnover(restaurant_id: str, db: Session) -> int:
    return 75


def calculate_dynamic_wait_time(waitlist_position: int, current_occupancy: float) -> int:
    base_time = 15
    occupancy_multiplier = 1 + (current_occupancy / 100)
    estimated_wait = waitlist_position * base_time * occupancy_multiplier
    return min(estimated_wait, 120)


# ============================================================
# RESERVATION SETTINGS
# ============================================================

@router.get("/settings")
async def get_reservation_settings_api(
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    settings = get_restaurant_settings(restaurant.id)
    return {
        "auto_release_minutes": settings.get('auto_release_minutes', 15),
        "require_deposit_for_party_size": settings.get('require_deposit_for_party_size', 6),
        "deposit_amount": settings.get('deposit_amount', 1000),
        "max_reservation_days_ahead": settings.get('max_reservation_days_ahead', 30),
        "min_cancel_hours": settings.get('min_cancel_hours', 2),
        "no_show_penalty": settings.get('no_show_penalty', 500)
    }


@router.put("/settings")
async def update_reservation_settings_api(
    request: ReservationSettingsRequest,
    db: Session = Depends(get_db),
    restaurant: Restaurant = Depends(get_current_restaurant)
):
    current_settings = get_restaurant_settings(restaurant.id)
    
    updated_settings = {
        **current_settings,
        "auto_release_minutes": request.auto_release_minutes,
        "require_deposit_for_party_size": request.require_deposit_for_party_size,
        "deposit_amount": request.deposit_amount,
        "max_reservation_days_ahead": request.max_reservation_days_ahead,
        "min_cancel_hours": request.min_cancel_hours,
        "no_show_penalty": request.no_show_penalty
    }
    
    update_restaurant_setting(restaurant.id, 'reservation_settings', json.dumps(updated_settings))
    return {"success": True}


# ============================================================
# AUTO-RELEASE TASK (Celery)
# ============================================================

@celery.task
def auto_release_reservation(reservation_id: str):
    # This is a mocked celery task logic
    pass


def schedule_auto_release(reservation_id: str, reservation_time: datetime, grace_minutes: int):
    import datetime as dt
    release_time = reservation_time + timedelta(minutes=grace_minutes)
    now = dt.datetime.now(dt.timezone.utc)
    if release_time.tzinfo is None:
        release_time = release_time.replace(tzinfo=dt.timezone.utc)
        
    delay_seconds = (release_time - now).total_seconds()
    if delay_seconds > 0:
        auto_release_reservation.apply_async(
            args=[reservation_id],
            countdown=delay_seconds
        )
