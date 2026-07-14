# ============================================================
# PlateLink Africa — Production Dockerfile
# Target: Render Web Service (Free Tier)
# ============================================================
FROM python:3.11-slim AS base

# Environment hygiene
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies
# - libpq-dev: PostgreSQL client library (asyncpg needs it)
# - build-essential: C compiler for some pip packages
# - tesseract-ocr: for pytesseract AI menu extraction
# - poppler-utils: for pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create a non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Render injects PORT dynamically — gunicorn_conf.py reads it
EXPOSE 8000

# Health check so Render knows the container is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health')" || exit 1

# Start with gunicorn + uvicorn workers
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
