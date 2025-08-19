import logging

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from app.app import HealthTrackerAPP
from app.client.client import HealthTrackerAdapter
from app.config import AppSettings, AsyncDatabaseDriver
from app.main import setup
from app.repository.models import Base

logger = logging.getLogger("conftest")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def settings() -> AppSettings:
    return AppSettings(
        APP_ENVIRONMENT="dev",
        DATABASE_DRIVER=AsyncDatabaseDriver.SQLITE,
        DATABASE_USER=SecretStr(""),
        DATABASE_PASSWORD=SecretStr(""),
        DATABASE_HOST=None,
        DATABASE_PORT=None,
        DATABASE_NAME=":memory:",
        LOG_DIR_CREATE=False,
        LOG_HANDLERS=["console"],
    )


@pytest.fixture
async def app(settings: AppSettings):
    app = setup(settings)
    async with LifespanManager(app):
        yield app


@pytest.fixture
def engine(app: HealthTrackerAPP) -> AsyncEngine:
    return app.state.engine


@pytest.fixture()
async def setup_tables(engine: AsyncEngine):
    try:
        async with engine.begin() as conn:

            def _run(conn: Connection):
                Base.metadata.create_all(conn, checkfirst=True)

            await conn.run_sync(_run)
        yield
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all, checkfirst=True)


# @pytest.fixture
# async def session(setup_tables: None, app: HealthTrackerAPP):
#     async with app.state.session_maker.begin() as session:
#         yield session


@pytest.fixture  # ??? rename to adapter
async def client(app: HealthTrackerAPP):
    async with AsyncClient(
        transport=ASGITransport(app), base_url="http://testserver"
    ) as session:
        yield HealthTrackerAdapter(session)
