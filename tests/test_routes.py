import pytest

from app.client.client import HealthTrackerAdapter

pytestmark = [pytest.mark.usefixtures("setup_tables")]


def test_health(client: HealthTrackerAdapter) -> None:
    pass
