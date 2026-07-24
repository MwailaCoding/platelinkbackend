"""Database seeding module for default system permissions and roles."""
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from apps.api.app.models.permission import Permission
from apps.api.app.models.role import Role
from apps.api.app.models.enums import (
    PermissionAction,
    PermissionCategory,
    RestaurantSize,
)

logger = logging.getLogger(__name__)

# Standard Permissions Definitions
DEFAULT_PERMISSIONS: List[Dict[str, Any]] = [
    # Dashboard
    {"name": "view_dashboard", "resource": "dashboard", "action": PermissionAction.READ, "category": PermissionCategory.DASHBOARD, "description": "View overall dashboard metrics"},
    {"name": "manage_dashboard", "resource": "dashboard", "action": PermissionAction.MANAGE, "category": PermissionCategory.DASHBOARD, "description": "Manage dashboard widgets and view key analytics"},
    
    # Orders
    {"name": "view_orders", "resource": "orders", "action": PermissionAction.READ, "category": PermissionCategory.ORDERS, "description": "View active and past orders"},
    {"name": "create_order", "resource": "orders", "action": PermissionAction.CREATE, "category": PermissionCategory.ORDERS, "description": "Create new customer order"},
    {"name": "edit_order", "resource": "orders", "action": PermissionAction.UPDATE, "category": PermissionCategory.ORDERS, "description": "Modify active order details or items"},
    {"name": "cancel_order", "resource": "orders", "action": PermissionAction.DELETE, "category": PermissionCategory.ORDERS, "description": "Cancel order or void items"},
    {"name": "manage_orders", "resource": "orders", "action": PermissionAction.MANAGE, "category": PermissionCategory.ORDERS, "description": "Full control over all restaurant orders"},

    # Menu
    {"name": "view_menu", "resource": "menu", "action": PermissionAction.READ, "category": PermissionCategory.MENU, "description": "View menu items and pricing"},
    {"name": "create_menu_item", "resource": "menu", "action": PermissionAction.CREATE, "category": PermissionCategory.MENU, "description": "Add new menu item or category"},
    {"name": "edit_menu_item", "resource": "menu", "action": PermissionAction.UPDATE, "category": PermissionCategory.MENU, "description": "Update menu item details or availability"},
    {"name": "delete_menu_item", "resource": "menu", "action": PermissionAction.DELETE, "category": PermissionCategory.MENU, "description": "Delete menu item or category"},
    {"name": "manage_menu", "resource": "menu", "action": PermissionAction.MANAGE, "category": PermissionCategory.MENU, "description": "Manage entire menu structure and pricing"},

    # Tables
    {"name": "view_tables", "resource": "tables", "action": PermissionAction.READ, "category": PermissionCategory.TABLES, "description": "View table layout and status"},
    {"name": "manage_tables", "resource": "tables", "action": PermissionAction.MANAGE, "category": PermissionCategory.TABLES, "description": "Manage floor plan and table assignments"},

    # Staff
    {"name": "view_staff", "resource": "staff", "action": PermissionAction.READ, "category": PermissionCategory.STAFF, "description": "View restaurant staff members"},
    {"name": "add_staff", "resource": "staff", "action": PermissionAction.CREATE, "category": PermissionCategory.STAFF, "description": "Invite or add new staff member"},
    {"name": "edit_staff", "resource": "staff", "action": PermissionAction.UPDATE, "category": PermissionCategory.STAFF, "description": "Update staff details, status, or PIN"},
    {"name": "delete_staff", "resource": "staff", "action": PermissionAction.DELETE, "category": PermissionCategory.STAFF, "description": "Deactivate or remove staff member"},
    {"name": "manage_roles", "resource": "roles", "action": PermissionAction.MANAGE, "category": PermissionCategory.STAFF, "description": "Manage custom roles and access levels"},
    {"name": "manage_permissions", "resource": "permissions", "action": PermissionAction.MANAGE, "category": PermissionCategory.STAFF, "description": "Assign or update role permissions"},

    # Payments
    {"name": "view_payments", "resource": "payments", "action": PermissionAction.READ, "category": PermissionCategory.PAYMENTS, "description": "View payment transactions and receipts"},
    {"name": "process_payment", "resource": "payments", "action": PermissionAction.CREATE, "category": PermissionCategory.PAYMENTS, "description": "Process payments and split bills"},
    {"name": "refund_payment", "resource": "payments", "action": PermissionAction.UPDATE, "category": PermissionCategory.PAYMENTS, "description": "Issue refunds or void payments"},
    {"name": "manage_payments", "resource": "payments", "action": PermissionAction.MANAGE, "category": PermissionCategory.PAYMENTS, "description": "Manage payment gateways and accounting"},

    # Reports
    {"name": "view_reports", "resource": "reports", "action": PermissionAction.READ, "category": PermissionCategory.REPORTS, "description": "View daily sales and performance reports"},
    {"name": "export_reports", "resource": "reports", "action": PermissionAction.UPDATE, "category": PermissionCategory.REPORTS, "description": "Export detailed analytics and audit logs"},
    {"name": "manage_reports", "resource": "reports", "action": PermissionAction.MANAGE, "category": PermissionCategory.REPORTS, "description": "Configure customized reporting dashboards"},

    # Settings
    {"name": "view_settings", "resource": "settings", "action": PermissionAction.READ, "category": PermissionCategory.SETTINGS, "description": "View restaurant profile and settings"},
    {"name": "manage_settings", "resource": "settings", "action": PermissionAction.MANAGE, "category": PermissionCategory.SETTINGS, "description": "Update store configuration and operating hours"},
]

SYSTEM_ROLES: List[Dict[str, Any]] = [
    {"name": "Owner", "description": "System-wide Owner with full administrative control", "level": 100, "is_system": True, "is_custom": False},
    {"name": "Manager", "description": "General Manager overseeing daily store operations", "level": 80, "is_system": True, "is_custom": False},
    {"name": "Waiter", "description": "Front of house staff taking orders and serving tables", "level": 20, "is_system": True, "is_custom": False},
    {"name": "Kitchen", "description": "Back of house kitchen staff managing prep line", "level": 20, "is_system": True, "is_custom": False},
    {"name": "Cashier", "description": "Front desk staff handling register and payments", "level": 30, "is_system": True, "is_custom": False},
    {"name": "Host", "description": "Seating coordinator and table manager", "level": 10, "is_system": True, "is_custom": False},
    {"name": "Stock Manager", "description": "Inventory and supplier coordinator", "level": 40, "is_system": True, "is_custom": False},
    {"name": "Observer", "description": "Read-only view of reports and dashboards", "level": 5, "is_system": True, "is_custom": False},
]

SIZE_BASED_ROLES: Dict[RestaurantSize, List[Dict[str, Any]]] = {
    RestaurantSize.SMALL: [
        {"name": "Owner (Full)", "description": "Owner executing operational & management duties", "level": 100, "restaurant_size": RestaurantSize.SMALL},
        {"name": "Manager", "description": "Shift manager handling tables, orders & staff", "level": 70, "restaurant_size": RestaurantSize.SMALL},
        {"name": "Waiter", "description": "Order entry & table service", "level": 20, "restaurant_size": RestaurantSize.SMALL},
        {"name": "Kitchen", "description": "Line cook & order prep", "level": 20, "restaurant_size": RestaurantSize.SMALL},
    ],
    RestaurantSize.MEDIUM: [
        {"name": "Owner (Strategic)", "description": "Strategic owner overseeing enterprise reports", "level": 100, "restaurant_size": RestaurantSize.MEDIUM},
        {"name": "GM", "description": "General Manager handling operations & scheduling", "level": 85, "restaurant_size": RestaurantSize.MEDIUM},
        {"name": "FOH Manager", "description": "Front of House Manager supervising service", "level": 60, "restaurant_size": RestaurantSize.MEDIUM},
        {"name": "Kitchen Manager", "description": "Head Chef supervising kitchen staff", "level": 60, "restaurant_size": RestaurantSize.MEDIUM},
        {"name": "Waiter", "description": "Table server & order taking", "level": 20, "restaurant_size": RestaurantSize.MEDIUM},
        {"name": "Cashier", "description": "POS operator & billing clerk", "level": 30, "restaurant_size": RestaurantSize.MEDIUM},
    ],
    RestaurantSize.LARGE: [
        {"name": "Owner (Executive)", "description": "Executive Director / Board Member", "level": 100, "restaurant_size": RestaurantSize.LARGE},
        {"name": "GM", "description": "General Manager", "level": 90, "restaurant_size": RestaurantSize.LARGE},
        {"name": "FOH Director", "description": "Director of Front of House", "level": 75, "restaurant_size": RestaurantSize.LARGE},
        {"name": "Executive Chef", "description": "Executive Head Chef", "level": 75, "restaurant_size": RestaurantSize.LARGE},
        {"name": "Floor Manager", "description": "Shift Floor Manager", "level": 50, "restaurant_size": RestaurantSize.LARGE},
        {"name": "Sous Chef", "description": "Assistant Head Chef", "level": 50, "restaurant_size": RestaurantSize.LARGE},
    ],
    RestaurantSize.ENTERPRISE: [
        {"name": "Corporate Owner", "description": "Multi-unit corporate owner", "level": 100, "restaurant_size": RestaurantSize.ENTERPRISE},
        {"name": "Regional Director", "description": "Regional Operations Director", "level": 95, "restaurant_size": RestaurantSize.ENTERPRISE},
        {"name": "GM", "description": "Store General Manager", "level": 85, "restaurant_size": RestaurantSize.ENTERPRISE},
        {"name": "Department Heads", "description": "Department Lead (FOH / BOH / Purchasing)", "level": 70, "restaurant_size": RestaurantSize.ENTERPRISE},
    ]
}

async def seed_default_permissions(db: AsyncSession) -> List[Permission]:
    """Seed base permissions into the database."""
    permissions = []
    for item in DEFAULT_PERMISSIONS:
        stmt = select(Permission).where(Permission.name == item["name"])
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if not existing:
            perm = Permission(**item)
            db.add(perm)
            permissions.append(perm)
        else:
            permissions.append(existing)
    await db.flush()
    logger.info(f"Seeded {len(permissions)} default permissions.")
    return permissions

async def seed_system_roles(db: AsyncSession) -> List[Role]:
    """Seed system roles (restaurant_id is None)."""
    # Fetch permissions for assignment
    stmt = select(Permission)
    res = await db.execute(stmt)
    all_perms = res.scalars().all()
    perm_map = {p.name: p for p in all_perms}

    roles = []
    for r_data in SYSTEM_ROLES:
        stmt = select(Role).where(Role.restaurant_id.is_(None), Role.name == r_data["name"])
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if not existing:
            role = Role(**r_data)
            # Assign relevant permissions to system role
            if r_data["name"] == "Owner":
                role.permissions = list(all_perms)
            elif r_data["name"] == "Manager":
                role.permissions = [p for p in all_perms if p.category != PermissionCategory.SETTINGS or p.action == PermissionAction.READ]
            elif r_data["name"] in ["Waiter", "Host"]:
                role.permissions = [p for p in all_perms if p.name in ["view_orders", "create_order", "edit_order", "view_tables", "view_menu"]]
            elif r_data["name"] == "Kitchen":
                role.permissions = [p for p in all_perms if p.name in ["view_orders", "edit_order", "view_menu"]]
            elif r_data["name"] == "Cashier":
                role.permissions = [p for p in all_perms if p.name in ["view_orders", "view_payments", "process_payment", "view_menu"]]
            elif r_data["name"] == "Stock Manager":
                role.permissions = [p for p in all_perms if p.category == PermissionCategory.MENU]
            elif r_data["name"] == "Observer":
                role.permissions = [p for p in all_perms if p.action == PermissionAction.READ]
            db.add(role)
            roles.append(role)
        else:
            roles.append(existing)
    await db.flush()
    logger.info(f"Seeded {len(roles)} system roles.")
    return roles

async def seed_default_roles(db: AsyncSession) -> List[Role]:
    """Seed template default roles per restaurant size (restaurant_id is None)."""
    stmt = select(Permission)
    res = await db.execute(stmt)
    all_perms = res.scalars().all()

    seeded_roles = []
    for size, role_list in SIZE_BASED_ROLES.items():
        for r_data in role_list:
            stmt = select(Role).where(
                Role.restaurant_id.is_(None),
                Role.name == r_data["name"],
                Role.restaurant_size == size
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            if not existing:
                role = Role(
                    name=r_data["name"],
                    description=r_data["description"],
                    level=r_data["level"],
                    is_system=False,
                    is_custom=False,
                    restaurant_size=size,
                    restaurant_id=None
                )
                role.permissions = list(all_perms)
                db.add(role)
                seeded_roles.append(role)
            else:
                seeded_roles.append(existing)
    await db.flush()
    logger.info(f"Seeded {len(seeded_roles)} size-based template roles.")
    return seeded_roles

async def seed_initial_data(db: AsyncSession) -> None:
    """Execute complete initial data seeding process."""
    await seed_default_permissions(db)
    await seed_system_roles(db)
    await seed_default_roles(db)
    await db.commit()
    logger.info("Successfully completed initial data seeding.")
