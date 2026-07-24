"""API v1 router composition."""
from fastapi import APIRouter
from apps.api.app.api.v1.endpoints import auth, users, roles, permissions, staff, shifts, invitations, qr, branches

api_router = APIRouter(prefix="/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(staff.router)
api_router.include_router(shifts.router)
api_router.include_router(invitations.router)
api_router.include_router(qr.router)
api_router.include_router(branches.router, prefix="/branches", tags=["branches"])
