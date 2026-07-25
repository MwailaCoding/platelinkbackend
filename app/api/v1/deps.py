"""Pre-configured API v1 RBAC dependencies."""
from app.core.dependencies import require_permission, require_owner
from app.core.deps import get_current_user

# Re-export current user
CurrentActiveUser = get_current_user

# Staff permissions
ViewStaff = require_permission("view_staff")
AddStaff = require_permission("add_staff")
EditStaff = require_permission("edit_staff")
DeleteStaff = require_permission("delete_staff")

# Order permissions
ViewOrders = require_permission("view_orders")
CreateOrder = require_permission("create_orders")
UpdateOrder = require_permission("update_orders")
CancelOrder = require_permission("cancel_orders")

# Menu permissions
ViewMenu = require_permission("view_menu")
ManageMenu = require_permission("manage_menu")

# Table permissions
ViewTables = require_permission("view_tables")
ManageTables = require_permission("manage_tables")

# Shift permissions
ViewShifts = require_permission("view_shifts")
ManageShifts = require_permission("manage_shifts")

# Payment permissions
ProcessPayments = require_permission("process_payments")

# Report permissions
ViewReports = require_permission("view_reports")
ExportReports = require_permission("export_reports")

# Role permissions
ManageRoles = require_permission("manage_roles")
ManagePermissions = require_permission("manage_permissions")

# Settings permissions
ManageSettings = require_permission("manage_settings")

# Owner check
RequireOwner = require_owner()
