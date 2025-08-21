from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import sqlalchemy
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AsyncDatabaseDriver(StrEnum):
    SQLITE = "sqlite+aiosqlite"
    POSTGRES = "postgresql+asyncpg"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="HEALTH_TRACKER_",
        env_file_encoding="utf-8",
        arbitrary_types_allowed=True,
        validate_default=True,
        validate_return=True,
        frozen=True,
        extra="allow",
    )

    SERVICE_DIR: Path = Path(__file__).resolve().parent.parent

    APP_ENVIRONMENT: Literal["dev", "staging", "production"]

    APP_NAME: str = "Health Tracker"
    APP_DESCRIPTION: str = "Health Tracker API"
    APP_VERSION: str = "1.0.0.0"

    APP_PORT: int = 8000
    APP_HOST: str = "0.0.0.0"
    APP_WORKERS: int | None = None
    APP_RELOAD: bool = False

    APP_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    API_PREFIX: str = "/api"

    @property
    def API_OPENAPI_URL(self) -> str:
        return f"{self.API_PREFIX}/openapi.json"

    @property
    def API_DOCS_URL(self) -> str:
        return f"{self.API_PREFIX}/docs"

    SERVICE_SCORE_COVERAGE_WEIGHT: float = 0.25
    SERVICE_SCORE_COVERAGE_FACTOR: float = 0.25
    SERVICE_SCORE_VALUE_QUALITY_WEIGHT: float = 0.35
    SERVICE_SCORE_Z_SCALING_FACTOR: float = 20.0

    HTTP_SESSION_TIMEOUT: float = 59.0  # seconds

    DATABASE_DRIVER: AsyncDatabaseDriver
    DATABASE_USER: SecretStr
    DATABASE_PASSWORD: SecretStr
    DATABASE_HOST: str | None
    DATABASE_PORT: int | None
    DATABASE_NAME: str

    @property
    def DATABASE_URL(self) -> sqlalchemy.URL:
        return sqlalchemy.URL.create(
            drivername=self.DATABASE_DRIVER,
            username=(
                self.DATABASE_USER.get_secret_value() if self.DATABASE_USER else None
            ),
            password=(
                self.DATABASE_PASSWORD.get_secret_value()
                if self.DATABASE_PASSWORD
                else None
            ),
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            database=self.DATABASE_NAME,
        )

    @property
    def DATABASE_URL_STR(self) -> str:
        return self.DATABASE_URL.render_as_string(hide_password=False)

    DATABASE_ECHO: bool = False

    @property
    def ALEMBIC_INI_PATH(self) -> Path:
        return self.SERVICE_DIR / "alembic.ini"

    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_HANDLERS: list[str] = ["console", "file"]

    LOG_LEVEL_DOTENV: LogLevel = LogLevel.ERROR
    LOG_LEVEL_ALEMBIC: LogLevel = LogLevel.INFO
    LOG_LEVEL_SQLALCHEMY: LogLevel = LogLevel.WARNING
    LOG_LEVEL_PYTEST: LogLevel = LogLevel.DEBUG
    LOG_LEVEL_HTTPX: LogLevel = LogLevel.DEBUG

    LOG_FILE: str = "health_tracker.log"
    LOG_JSON_FILE: str = "health_tracker.json"
    LOG_MAX_BYTE_WHEN_ROTATION: int = 100 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 10

    LOG_DIR_CREATE: bool = True

    @property
    def LOG_DIR(self) -> Path:
        return self.SERVICE_DIR / "log"

    @property
    def LOGGING(self) -> dict[str, Any]:
        default_handlers = {
            "console": {
                "level": self.LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "console",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "level": self.LOG_LEVEL,
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "file",
                "filename": self.LOG_DIR / self.LOG_FILE,
                "maxBytes": self.LOG_MAX_BYTE_WHEN_ROTATION,
                "backupCount": self.LOG_BACKUP_COUNT,
            },
        }
        handlers = {k: v for k, v in default_handlers.items() if k in self.LOG_HANDLERS}
        config = {
            "version": 1,
            "formatters": {
                "file": {
                    "()": "uvicorn.logging.ColourizedFormatter",
                    "format": "[-] %(asctime)s [%(levelname)s] - %(message)s",
                },
                "console": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": None,
                },
            },
            "handlers": handlers,
            "loggers": {
                "app": {
                    "level": self.LOG_LEVEL,
                    "handlers": self.LOG_HANDLERS,
                },
                "dotenv": {
                    "level": self.LOG_LEVEL_DOTENV,
                    "handlers": self.LOG_HANDLERS,
                },
                "uvicorn": {
                    "handlers": self.LOG_HANDLERS,
                    "level": self.LOG_LEVEL,
                },
                "alembic": {
                    "level": self.LOG_LEVEL_ALEMBIC,
                    "handlers": self.LOG_HANDLERS,
                },
                "sqlalchemy": {
                    "level": self.LOG_LEVEL_SQLALCHEMY,
                    "handlers": self.LOG_HANDLERS,
                },
                "conftest": {
                    "level": self.LOG_LEVEL_PYTEST,
                    "handlers": self.LOG_HANDLERS,
                },
                "httpx": {
                    "level": self.LOG_LEVEL_HTTPX,
                    "handlers": self.LOG_HANDLERS,
                },
            },
        }
        return config

    def __repr_args__(self):
        for k, v in super().__repr_args__():
            if (
                k in self.model_fields_set
                and k in self.model_fields
                and self.model_fields[k].repr
            ):
                yield (k, v)

    def __str__(self) -> str:
        return repr(self)


class IntegrationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="INTEGRATION_",
        env_file_encoding="utf-8",
        arbitrary_types_allowed=True,
        validate_default=True,
        validate_return=True,
        frozen=True,
        extra="allow",
    )

    HEALTH_TRACKER_BASE_URL: str
    HEALTH_TRACKER_TOKEN: str | None = None

    EXTERNAL_FHIR_PATIENTS_FILE: Path = Path("data/patients.json")
    EXTERNAL_FHIR_OBSERVATIONS_FILE: Path = Path("data/observations.json")
