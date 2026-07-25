# app/models/enums.py
import enum

class SubscriptionPlan(enum.Enum):
    starter = 'starter'
    pro = 'pro'
    enterprise = 'enterprise'

class SubscriptionStatus(enum.Enum):
    active = 'active'
    expired = 'expired'
    trial = 'trial'

class StaffRole(enum.Enum):
    owner = 'owner'
    manager = 'manager'
    waiter = 'waiter'
    chef = 'chef'
    cashier = 'cashier'

class ShiftType(enum.Enum):
    morning = 'morning'
    afternoon = 'afternoon'
    evening = 'evening'
    night = 'night'
    full = 'full'

class TableStatus(enum.Enum):
    available = 'available'
    occupied = 'occupied'
    ordering = 'ordering'
    ordered = 'ordered'
    ready = 'ready'
    eating = 'eating'
    bill_requested = 'bill_requested'
    cleaning = 'cleaning'
    reserved = 'reserved'
    held = 'held'

class OrderStatus(enum.Enum):
    received = 'received'
    pending = 'pending'
    preparing = 'preparing'
    ready = 'ready'
    served = 'served'
    completed = 'completed'
    cancelled = 'cancelled'

class PaymentStatus(enum.Enum):
    pending = 'pending'
    paid = 'paid'
    failed = 'failed'
    refunded = 'refunded'
    partially_paid = 'partially_paid'

class PaymentMethod(enum.Enum):
    cash = 'cash'
    mpesa = 'mpesa'
    card = 'card'
    bank_transfer = 'bank_transfer'

class CallStatus(enum.Enum):
    pending = 'pending'
    acknowledged = 'acknowledged'
    completed = 'completed'

class SessionStatus(enum.Enum):
    active = 'active'
    closed = 'closed'
    expired = 'expired'
