import logging
import logging.config
import os

import click
import uvicorn

from app.app import HealthTrackerAPP
from app.config import AppSettings

logger = logging.getLogger("app.main")


def setup_logging(settings: AppSettings) -> None:
    if settings.LOG_DIR_CREATE and not settings.LOG_DIR.exists():
        settings.LOG_DIR.mkdir()
    logging.config.dictConfig(settings.LOGGING)


def setup(settings: AppSettings | None = None) -> HealthTrackerAPP:
    settings = settings or AppSettings()
    setup_logging(settings)
    logger.info("Run app worker [%s]", click.style(os.getpid(), fg="cyan"))
    return HealthTrackerAPP.startup(settings)


def main() -> None:
    settings = AppSettings()

    # NOTE: setup logging for main process;
    # later it will be initialized for each worker process as well;
    setup_logging(settings)
    logger.info("Run %s (%s)", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Settings: %s", settings)
    logger.debug("Unprocessed env variables: %s", settings.model_extra)

    # if settings.APP_WORKERS or settings.APP_RELOAD:
    uvicorn.run(
        "app.main:setup",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        workers=settings.APP_WORKERS,
        reload=settings.APP_RELOAD,
        factory=True,
    )


if __name__ == "__main__":
    main()
