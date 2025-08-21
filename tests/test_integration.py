import logging
from pathlib import Path

from app.adapter.adapter import HealthTrackerAdapter
from app.adapter.external import ExternalFHIRAdapter, ExternalFHIRSourceJSONFiles
from app.services.integration import HealthTrackerIntegration

logger = logging.getLogger("conftest")


async def test_integration(client: HealthTrackerAdapter) -> None:
    service = HealthTrackerIntegration(
        client=client,
        external=ExternalFHIRAdapter(
            source=ExternalFHIRSourceJSONFiles(
                patients=Path("data/patients.json"),
                observations=Path("data/observations.json"),
            ),
        ),
        logger=logger,
        strict=True,
    )

    await service.integrate()

    assert len((await client.get_patients()).items) == 10
    assert len((await client.get_codeable_concepts()).items) == 5
    assert len((await client.get_observations()).items) == 50
