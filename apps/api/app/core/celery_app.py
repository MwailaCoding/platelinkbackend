from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "platelink",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.worker", "app.tasks.kitchen_metrics", "app.tasks.kitchen_tasks"]
)

celery_app.conf.beat_schedule = {
    "daily-sales-report": {
        "task": "app.tasks.worker.generate_daily_sales_report",
        "schedule": crontab(hour=21, minute=0),
    },
    "cleanup-expired-sessions": {
        "task": "app.tasks.worker.cleanup_expired_sessions",
        "schedule": crontab(minute=0), # Every hour
    },
    "update-kitchen-performance-metrics": {
        "task": "app.tasks.kitchen_metrics.update_kitchen_performance_metrics",
        "schedule": crontab(minute="*/5"), # Every 5 minutes
    },
    "send-slow-order-alert": {
        "task": "app.tasks.kitchen_metrics.send_slow_order_alert",
        "schedule": crontab(minute="*"), # Every minute
    },
    "auto-clear-ready-orders": {
        "task": "app.tasks.kitchen_tasks.auto_clear_ready_orders",
        "schedule": crontab(minute="*"), # Every minute
    },
}

celery_app.conf.timezone = "Africa/Nairobi"

