"""Database models enums for PlateLink role-based access control."""
from enum import Enum

class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class RestaurantSize(str, Enum):
    SMALL = "small"          # 1-10 staff
    MEDIUM = "medium"        # 11-30 staff
    LARGE = "large"          # 31-80 staff
    ENTERPRISE = "enterprise"  # 80+ staff

class PermissionAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"

class PermissionCategory(str, Enum):
    DASHBOARD = "dashboard"
    ORDERS = "orders"
    MENU = "menu"
    TABLES = "tables"
    STAFF = "staff"
    PAYMENTS = "payments"
    REPORTS = "reports"
    SETTINGS = "settings"
