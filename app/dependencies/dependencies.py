import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated, AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.config import AsyncDatabaseDriver

if TYPE_CHECKING:
    from app.app import HealthTrackerAPP
    from app.config import AppSettings
else:
    HealthTrackerAPP = object
    AppSettings = object

logger = logging.getLogger(__name__)


def get_app(request: Request) -> HealthTrackerAPP:
    return request.app


AppDepends = Annotated[HealthTrackerAPP, Depends(get_app)]


def get_app_settings(app: AppDepends) -> AppSettings:
    return app.state.settings


AppSettingsDepends = Annotated[AppSettings, Depends(get_app_settings)]


async def get_database_session(app: AppDepends) -> AsyncGenerator[AsyncSession, None]:
    """Begin database transaction with autocommit / rollback."""
    async with app.state.session_maker.begin() as session:
        if app.state.settings.DATABASE_DRIVER == AsyncDatabaseDriver.SQLITE:
            await session.execute(text("PRAGMA foreign_keys = ON"))
        yield session


SessionDepends = Annotated[AsyncSession, Depends(get_database_session)]
"""Common database session dependency. """

SessionContext = asynccontextmanager(get_database_session)
"""Common database session context. """
