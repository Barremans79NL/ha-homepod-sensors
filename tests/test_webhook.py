"""Tests for the HomePod Sensors webhook handler."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from custom_components.homepod_sensors.const import DOMAIN
from custom_components.homepod_sensors.coordinator import HomePodCoordinator

from .conftest import SAMPLE_PAYLOAD


@pytest.fixture
async def setup_integration(hass, mock_config_entry):
    """Set up integration and return coordinator."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.webhook.async_register"
    ), patch(
        "homeassistant.components.webhook.async_unregister"
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    return hass.data[DOMAIN][mock_config_entry.entry_id]


async def test_webhook_creates_devices(setup_integration):
    """Webhook payload should populate coordinator data."""
    coordinator: HomePodCoordinator = setup_integration
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])

    assert "HP000000000001" in coordinator.data
    assert "HP000000000002" in coordinator.data

    dev1 = coordinator.data["HP000000000001"]
    assert dev1.name == "Living Room HomePod"
    assert dev1.temperature_c == 21.5
    assert dev1.humidity_pct == 48.2
    assert dev1.last_seen is not None


async def test_webhook_updates_existing_device(setup_integration):
    """Subsequent pushes should update existing devices, not duplicate."""
    coordinator: HomePodCoordinator = setup_integration
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])
    first_seen = coordinator.data["HP000000000001"].last_seen

    coordinator.handle_webhook_payload(
        [
            {
                "serial": "HP000000000001",
                "name": "Living Room HomePod",
                "temperature_c": 22.0,
                "humidity_pct": 45.0,
            }
        ]
    )

    assert coordinator.data["HP000000000001"].temperature_c == 22.0
    assert coordinator.data["HP000000000001"].last_seen >= first_seen
    assert len(coordinator.data) == 2  # second device not removed


async def test_webhook_skips_malformed_device(setup_integration):
    """Devices missing required fields should be skipped."""
    coordinator: HomePodCoordinator = setup_integration
    coordinator.handle_webhook_payload(
        [
            {"serial": "HP000000000003", "name": "Missing temp"},  # no temp/humidity
            {
                "serial": "HP000000000004",
                "name": "Valid",
                "temperature_c": 20.0,
                "humidity_pct": 50.0,
            },
        ]
    )

    assert "HP000000000003" not in coordinator.data
    assert "HP000000000004" in coordinator.data


async def test_new_device_callback_invoked(setup_integration):
    """New device callback should fire once per new serial."""
    coordinator: HomePodCoordinator = setup_integration
    discovered: list[str] = []

    coordinator.register_new_device_callback(lambda serial, _data: discovered.append(serial))
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])

    assert set(discovered) == {"HP000000000001", "HP000000000002"}

    # Second push with same serials — callback should NOT fire again.
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])
    assert len(discovered) == 2  # still 2, not 4
