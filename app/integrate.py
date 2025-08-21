import asyncio
import logging

import httpx

from app.adapter.adapter import HealthTrackerAdapter
from app.adapter.external import ExternalFHIRAdapter, ExternalFHIRSourceJSONFiles
from app.config import IntegrationSettings
from app.services.integration import HealthTrackerIntegration

logger = logging.getLogger("app.integrate")


async def run() -> None:
    """Run external FHIR data integration."""

    settings = IntegrationSettings()  # type: ignore[call-arg]
    logger.info("Run integration. Settings: %s", settings)

    async with httpx.AsyncClient(
        base_url=settings.HEALTH_TRACKER_BASE_URL,
        headers=(
            {"Authorization": f"Bearer {settings.HEALTH_TRACKER_TOKEN}"}
            if settings.HEALTH_TRACKER_TOKEN
            else None
        ),
        timeout=settings.HTTP_SESSION_TIMEOUT,
    ) as client:
        service = HealthTrackerIntegration(
            client=HealthTrackerAdapter(client),
            external=ExternalFHIRAdapter(
                source=ExternalFHIRSourceJSONFiles(
                    patients=settings.EXTERNAL_FHIR_PATIENTS_FILE,
                    observations=settings.EXTERNAL_FHIR_OBSERVATIONS_FILE,
                ),
            ),
            logger=logger,
        )
        await service.integrate()


if __name__ == "__main__":
    asyncio.run(run())
