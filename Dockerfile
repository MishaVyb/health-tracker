# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock /

# Install dependencies
RUN uv sync --locked

# Copy application code
COPY . .

# Expose port
# EXPOSE 8000

# Set environment variables
# ENV PYTHONPATH=.
ENV HEALTH_TRACKER_APP_HOST=0.0.0.0
ENV HEALTH_TRACKER_APP_PORT=8000
ENV HEALTH_TRACKER_DATABASE_HOST=db
ENV HEALTH_TRACKER_DATABASE_PORT=5432
ENV HEALTH_TRACKER_DATABASE_NAME=health_tracker_db
ENV HEALTH_TRACKER_DATABASE_DRIVER=postgresql+asyncpg

# Run the application
CMD ["uv", "run", "python", "-m", "app.main"]
