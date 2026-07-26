"""RBAC Default Permissions and Roles Seeding Module."""
import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission

logger = logging.getLogger(__name__)

DEFAULT_PERMISSIONS = [
    {"name": "view_dashboard", "resource": "dashboard", "action": "read", "category": "dashboard", "description": "View main dashboard analytics"},
    {"name": "view_orders", "resource": "orders", "action": "read", "category": "orders", "description": "View active and past orders"},
    {"name": "create_orders", "resource": "orders", "action": "create", "category": "orders", "description": "Create new customer orders"},
    {"name": "update_orders", "resource": "orders", "action": "update", "category": "orders", "description": "Update order status or items"},
    {"name": "cancel_orders", "resource": "orders", "action": "delete", "category": "orders", "description": "Cancel or void active orders"},
    {"name": "view_staff", "resource": "staff", "action": "read", "category": "staff", "description": "View staff members roster"},
    {"name": "add_staff", "resource": "staff", "action": "create", "category": "staff", "description": "Invite or create new staff members"},
    {"name": "edit_staff", "resource": "staff", "action": "update", "category": "staff", "description": "Edit staff roles and details"},
    {"name": "delete_staff", "resource": "staff", "action": "delete", "category": "staff", "description": "Deactivate or remove staff members"},
    {"name": "manage_roles", "resource": "roles", "action": "manage", "category": "staff", "description": "Manage custom roles and access levels"},
    {"name": "manage_permissions", "resource": "permissions", "action": "manage", "category": "staff", "description": "Assign or update role permissions"},
    {"name": "view_menu", "resource": "menu", "action": "read", "category": "menu", "description": "View restaurant menu items"},
    {"name": "manage_menu", "resource": "menu", "action": "manage", "category": "menu", "description": "Add, edit, or delete menu items"},
    {"name": "view_tables", "resource": "tables", "action": "read", "category": "tables", "description": "View floor plan and table status"},
    {"name": "manage_tables", "resource": "tables", "action": "manage", "category": "tables", "description": "Configure tables and floor plans"},
    {"name": "view_shifts", "resource": "shifts", "action": "read", "category": "staff", "description": "View staff shift rosters"},
    {"name": "manage_shifts", "resource": "shifts", "action": "manage", "category": "staff", "description": "Assign or manage staff shifts"},
    {"name": "process_payments", "resource": "payments", "action": "update", "category": "payments", "description": "Process payments and split bills"},
    {"name": "view_reports", "resource": "reports", "action": "read", "category": "reports", "description": "View daily sales and staff reports"},
    {"name": "export_reports", "resource": "reports", "action": "export", "category": "reports", "description": "Export analytics and financial reports"},
    {"name": "manage_settings", "resource": "settings", "action": "manage", "category": "settings", "description": "Manage restaurant profile and settings"},
    {"name": "view_links", "resource": "links", "action": "read", "category": "links", "description": "View restaurant links, custom domain, and QR codes"},
    {"name": "manage_links", "resource": "links", "action": "manage", "category": "links", "description": "Create, edit, or delete links, custom domain, and QR codes"},
    {"name": "manage_till", "resource": "till", "action": "manage", "category": "payments", "description": "Open/close shift and manage till reconciliation"},
    {"name": "view_receipts", "resource": "receipts", "action": "read", "category": "payments", "description": "View and generate digital receipts"},
    {"name": "split_bills", "resource": "payments", "action": "manage", "category": "payments", "description": "Split bills into multiple guest checks"},
]

DEFAULT_ROLES = [
    {
        "name": "Owner",
        "description": "System-wide Owner with full administrative control",
        "level": 100,
        "is_system": True,
        "is_custom": False,
        "permissions": ["all"]
    },
    {
        "name": "Manager",
        "description": "Store Manager with operational control",
        "level": 80,
        "is_system": True,
        "is_custom": False,
        "permissions": [
            "view_dashboard", "view_orders", "update_orders", "cancel_orders",
            "view_staff", "add_staff", "edit_staff",
            "view_menu", "manage_menu",
            "view_tables", "manage_tables",
            "view_shifts", "manage_shifts",
            "process_payments",
            "view_reports", "export_reports",
            "view_links", "manage_links"
        ]
    },
    {
        "name": "Cashier",
        "description": "POS Cashier handling payments and active orders",
        "level": 30,
        "is_system": True,
        "is_custom": False,
        "permissions": ["view_dashboard", "view_orders", "process_payments", "view_reports"]
    },
    {
        "name": "Waiter",
        "description": "Service staff taking orders and managing tables",
        "level": 20,
        "is_system": True,
        "is_custom": False,
        "permissions": ["view_dashboard", "view_orders", "create_orders", "update_orders", "view_tables"]
    },
    {
        "name": "Kitchen",
        "description": "Back-of-house kitchen staff viewing and preparing orders",
        "level": 20,
        "is_system": True,
        "is_custom": False,
        "permissions": ["view_orders", "update_orders"]
    },
    {
        "name": "Host",
        "description": "Host managing seating and floor plans",
        "level": 20,
        "is_system": True,
        "is_custom": False,
        "permissions": ["view_dashboard", "view_tables", "manage_tables"]
    },
    {
        "name": "Stock Manager",
        "description": "Inventory and menu manager",
        "level": 40,
        "is_system": True,
        "is_custom": False,
        "permissions": ["view_dashboard", "view_menu", "manage_menu", "view_reports"]
    }
]

def seed_permissions(db: Session):
    """Idempotently seed default RBAC permissions."""
    permission_map = {}
    for p_data in DEFAULT_PERMISSIONS:
        stmt = select(Permission).where(Permission.name == p_data["name"])
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            perm = Permission(**p_data)
            db.add(perm)
            db.flush()
            permission_map[p_data["name"]] = perm
        else:
            permission_map[p_data["name"]] = existing
    return permission_map

def seed_system_roles(db: Session):
    """Idempotently seed system roles."""
    role_map = {}
    for r_data in DEFAULT_ROLES:
        stmt = select(Role).where(Role.name == r_data["name"], Role.restaurant_id.is_(None))
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            role = Role(
                name=r_data["name"],
                description=r_data["description"],
                level=r_data["level"],
                is_system=r_data["is_system"],
                is_custom=r_data["is_custom"],
                restaurant_id=None
            )
            db.add(role)
            db.flush()
            role_map[r_data["name"]] = role
        else:
            role_map[r_data["name"]] = existing
    return role_map

def seed_role_permissions(db: Session, permission_map, role_map):
    """Link roles to their default permissions."""
    all_permissions = list(permission_map.values())
    for r_data in DEFAULT_ROLES:
        role = role_map.get(r_data["name"])
        if not role:
            continue
        
        target_perms = all_permissions if "all" in r_data["permissions"] else [permission_map[p_name] for p_name in r_data["permissions"] if p_name in permission_map]
        
        for perm in target_perms:
            stmt = select(RolePermission).where(RolePermission.role_id == role.id, RolePermission.permission_id == perm.id)
            existing = db.execute(stmt).scalar_one_or_none()
            if not existing:
                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                db.add(rp)

def seed_rbac_data(db: Session):
    """Run all RBAC seeding steps idempotently."""
    logger.info("Seeding default RBAC permissions and system roles...")
    permission_map = seed_permissions(db)
    role_map = seed_system_roles(db)
    seed_role_permissions(db, permission_map, role_map)
    db.commit()
    logger.info("RBAC data seeding completed successfully.")
