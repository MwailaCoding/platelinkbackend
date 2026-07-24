"""Endpoints package initialization."""
from apps.api.app.api.v1.endpoints import auth, users, roles, permissions, staff, shifts, invitations, qr

__all__ = ["auth", "users", "roles", "permissions", "staff", "shifts", "invitations", "qr"]
