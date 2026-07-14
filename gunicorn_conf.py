import multiprocessing
import os

# Render injects $PORT dynamically. Fall back to 8000 for local dev.
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Free tier: 1 vCPU. Cap at 2 workers to stay within memory limits.
workers = min(multiprocessing.cpu_count() * 2 + 1, 2)

# Use uvicorn workers so FastAPI's async works correctly
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts — Render health checks require a response within 30s
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging to stdout (Render captures this)
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'
