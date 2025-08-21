# Health Tracker

[![CI](https://github.com/MishaVyb/health-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/MishaVyb/health-tracker/actions/workflows/ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

![](https://img.shields.io/badge/python-3.13-blue)
![](https://img.shields.io/badge/fastapi-0.116.1-blue)
![](https://img.shields.io/badge/SQLAlchemy-2.0.43-blue)

A FastAPI-based health tracking application that manages patient data and medical observations with FHIR integration capabilities.

**API Documentation**: http://localhost:8000/api/docs

## Core Functionality

### Patients Management
- Create, read, update, and delete patient records
- Store patient demographics and medical information
- UUID-based patient identification

### Observations Management
- Track medical observations with timestamps
- Filter observations by patient, observation type, and date ranges
- Support for various observation codes and types

### FHIR Integration
- Import patient data from external FHIR servers
- Synchronize observations and codeable concepts
- Handle data validation and transformation

## How to Run the App

### Prerequisites
- Python 3.13+
- PostgreSQL 15+
- [uv](https://github.com/astral-sh/uv) package manager

### Option 1: Run with Python Directly

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Set up environment variables** (create `.env` file):
   ```bash
   HEALTH_TRACKER_APP_ENVIRONMENT=dev
   HEALTH_TRACKER_DATABASE_DRIVER=postgresql+asyncpg
   HEALTH_TRACKER_DATABASE_USER=postgres
   HEALTH_TRACKER_DATABASE_PASSWORD=password
   HEALTH_TRACKER_DATABASE_HOST=localhost
   HEALTH_TRACKER_DATABASE_PORT=5432
   HEALTH_TRACKER_DATABASE_NAME=health_tracker_db
   ```

3. **Run database migrations**:
   ```bash
   uv run alembic upgrade head
   ```

4. **Start the application**:
   ```bash
   uv run python -m app.main
   ```

### Option 2: Run with Docker Compose

```bash
docker-compose up -d
```

This will:
- Start PostgreSQL database
- Run database migrations automatically
- Start the FastAPI application

## FHIR Integration

Health Tracker has build in integration with external FHIR sources. To run integration follow these steps:

1. **Set up environment variables** (create `.env` file):
   ```bash
   HEALTH_TRACKER_APP_BASE_URL=http://localhost:8000
   ```

3. **Run integration script**:
    ```bash
    uv run python -m app.integrate
    ```
