FROM python:3.13-slim

WORKDIR /

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /
RUN pip install uv
RUN uv sync --locked

COPY . .

ENV HEALTH_TRACKER_APP_HOST=0.0.0.0
ENV HEALTH_TRACKER_APP_PORT=8000
ENV HEALTH_TRACKER_DATABASE_HOST=db
ENV HEALTH_TRACKER_DATABASE_PORT=5432
ENV HEALTH_TRACKER_DATABASE_NAME=health_tracker_db
ENV HEALTH_TRACKER_DATABASE_DRIVER=postgresql+asyncpg

CMD ["uv", "run", "python", "-m", "app.main"]
