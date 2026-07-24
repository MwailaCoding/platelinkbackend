"""Core package initialization."""
from apps.api.app.core.database import get_db, engine, async_session_local
from apps.api.app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    authenticate_user,
    authenticate_user_pin,
    authenticate_user_qr,
    get_current_user,
    get_current_active_user,
    get_current_restaurant,
)
from apps.api.app.core.permissions import (
    has_permission,
    require_permission,
    has_resource_permission,
    has_restaurant_access,
    has_branch_access,
)

__all__ = [
    "get_db",
    "engine",
    "async_session_local",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "authenticate_user",
    "authenticate_user_pin",
    "authenticate_user_qr",
    "get_current_user",
    "get_current_active_user",
    "get_current_restaurant",
    "has_permission",
    "require_permission",
    "has_resource_permission",
    "has_restaurant_access",
    "has_branch_access",
]
