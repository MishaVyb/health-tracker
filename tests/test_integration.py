import logging

from app.adapter.adapter import HealthTrackerAdapter
from app.adapter.external import ExternalFHIRAdapter
from app.services.integration import HealthTrackerIntegration
from tests.conftest import TEST_EXTERNAL_FHIR_SOURCE

logger = logging.getLogger("conftest")


async def test_integration(client: HealthTrackerAdapter) -> None:
    service = HealthTrackerIntegration(
        client=client,
        external=ExternalFHIRAdapter(source=TEST_EXTERNAL_FHIR_SOURCE),
        logger=logger,
        strict=True,
    )

    await service.integrate()

    assert len((await client.get_patients()).items) == 10
    assert len((await client.get_codeable_concepts()).items) == 5
    assert len((await client.get_observations()).items) == 50
