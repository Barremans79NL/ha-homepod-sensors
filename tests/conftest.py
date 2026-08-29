"""Test configuration for homepod_sensors."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.homepod_sensors.const import (
    CONF_UPDATE_INTERVAL,
    CONF_WEBHOOK_ID,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

TEST_WEBHOOK_ID = "test-webhook-id-abc123"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in every test."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_WEBHOOK_ID: TEST_WEBHOOK_ID,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
        },
        title="HomePod Sensors",
    )


SAMPLE_PAYLOAD = {
    "devices": [
        {
            "serial": "HP000000000001",
            "name": "Living Room HomePod",
            "temperature_c": 21.5,
            "humidity_pct": 48.2,
        },
        {
            "serial": "HP000000000002",
            "name": "Bedroom HomePod mini",
            "temperature_c": 20.1,
            "humidity_pct": 52.0,
        },
    ]
}
