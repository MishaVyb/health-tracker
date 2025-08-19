from __future__ import annotations

import logging.config
from contextlib import asynccontextmanager
from typing import Type

import fastapi.datastructures
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .api import routes
from .config import AppSettings
from .dependencies.logging import LoggerMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: HealthTrackerAPP):
    engine = app.state.engine = create_async_engine(
        app.state.settings.DATABASE_URL,
        echo=app.state.settings.DATABASE_ECHO,
    )
    app.state.session_maker = async_sessionmaker(engine)

    try:
        yield
    finally:
        await engine.dispose()


class HealthTrackerAPP(FastAPI):
    class State(fastapi.datastructures.State):
        settings: AppSettings
        engine: AsyncEngine
        session_maker: async_sessionmaker[AsyncSession]

    state: State

    @classmethod
    def startup(cls: Type[HealthTrackerAPP], settings: AppSettings):
        app = cls(
            title=settings.APP_NAME,
            description=settings.APP_DESCRIPTION,
            version=settings.APP_VERSION,
            openapi_url=str(settings.API_OPENAPI_URL),
            docs_url=str(settings.API_DOCS_URL),
            generate_unique_id_function=lambda route: route.name,
            lifespan=lifespan,
            redirect_slashes=False,
        )
        app.state.settings = settings

        app.add_middleware(LoggerMiddleware, name=__name__)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.APP_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.include_router(routes.patients)
        app.include_router(routes.observations)
        app.include_router(routes.concepts)

        return app
