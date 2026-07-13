# PlateLink Backend

PlateLink is a robust dining and hospitality system. This repository houses the Python FastAPI backend engine that powers PlateLink's API, Celery task queue, databases, and third-party integrations (M-Pesa, Africa's Talking SMS, Brevo/SendGrid emails, and Cloudinary media storage).

## Features

- **FastAPI Core**: Async, high-performance API endpoints.
- **SQLAlchemy (Async)**: Modern PostgreSQL interface using alembic migrations.
- **Redis & Celery**: Background task runner and scheduled beat jobs (e.g., matching algorithms, notifications).
- **M-Pesa Integration**: Mobile payments using Safaricom's Daraja API.
- **AfricasTalking Integration**: Automated SMS notifications.
- **Brevo & SendGrid**: Transactional email services.
- **Cloudinary**: Cloud-based menu card and layout image storage.

---

## Prerequisites

Ensure you have the following installed locally:
- **Python**: `3.11+`
- **PostgreSQL**: `15+`
- **Redis**: For Celery tasks and session management

---

## Local Setup

### 1. Clone & Set Up Directory
Initialize and configure your local workspace. Ensure this directory is isolated from the frontend directory:
```bash
# Clone or open the repository root
cd platelink
```

### 2. Configure Environment Variables
Copy `.env.example` to a new `.env` file and update variables with your local settings (database passwords, API keys, etc.):
```bash
cp .env.example .env
```

### 3. Create a Virtual Environment
It is highly recommended to use a virtual environment:
```bash
# Create virtual environment
python -m venv .venv

# Activate on Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Activate on macOS/Linux:
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Initialize the Database
Prepare database migrations or run the setup scripts:
```bash
# Apply migrations
python migrate_db.py
```

### 6. Run the Application
Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
The interactive Swagger API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Running Background Tasks (Celery & Redis)

Start the Redis server on your local machine, and then run the Celery worker and beat scheduler in separate terminal sessions:

```bash
# Start Celery Worker
celery -A app.core.celery_app worker --loglevel=info

# Start Celery Beat
celery -A app.core.celery_app beat --loglevel=info
```

---

## Running Tests

Execute backend unit tests with `pytest`:
```bash
pytest
```

---

## Deployment (Docker)

The project includes a `docker-compose.yml` for multi-container production/development deployment:
```bash
docker-compose up --build
```
This runs PostgreSQL, Redis, the FastAPI application server, and the Celery worker/beat nodes together.
