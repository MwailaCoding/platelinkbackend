# app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, restaurant, staff, tables, menu, customer, orders, kitchen, kitchen_admin, waiter, analytics, public, expediter
)
from app.api.v1.routes import payments, webhooks, menu_ai, floor_plan, settings, reservations, branches

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(restaurant.router, prefix="/restaurants", tags=["restaurants"])
api_router.include_router(branches.router) # Prefix is defined in router itself
api_router.include_router(staff.router, prefix="/staff", tags=["staff"])
api_router.include_router(tables.router, prefix="/tables", tags=["tables"])
api_router.include_router(menu.router, prefix="/menu", tags=["menu"])
api_router.include_router(menu_ai.router, prefix="/menu", tags=["menu"])
api_router.include_router(customer.router, prefix="/customer", tags=["customer"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(kitchen.router, prefix="/kitchen", tags=["kitchen"])
api_router.include_router(kitchen_admin.router, prefix="/kitchen/admin", tags=["kitchen_admin"])
api_router.include_router(expediter.router, prefix="/expediter", tags=["expediter"])
api_router.include_router(waiter.router, prefix="/waiter", tags=["waiter"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(public.router, prefix="/public", tags=["public"])
api_router.include_router(floor_plan.router, tags=["floor_plan"])
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(reservations.router, tags=["reservations"])


