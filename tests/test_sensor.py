"""Tests for HomePod Sensors sensor entities."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from custom_components.homepod_sensors.const import DOMAIN

from .conftest import SAMPLE_PAYLOAD


@pytest.fixture
async def setup_integration(hass, mock_config_entry):
    """Set up integration with sensor platforms."""
    mock_config_entry.add_to_hass(hass)
    with patch("homeassistant.components.webhook.async_register"), patch(
        "homeassistant.components.webhook.async_unregister"
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    return hass.data[DOMAIN][mock_config_entry.entry_id]


async def test_temperature_sensor_state(hass, setup_integration):
    """Temperature sensor should reflect latest webhook data."""
    coordinator = setup_integration
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])
    await hass.async_block_till_done()

    state = hass.states.get("sensor.living_room_homepod_temperature")
    assert state is not None
    assert float(state.state) == 21.5
    assert state.attributes["unit_of_measurement"] == "°C"


async def test_humidity_sensor_state(hass, setup_integration):
    """Humidity sensor should reflect latest webhook data."""
    coordinator = setup_integration
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])
    await hass.async_block_till_done()

    state = hass.states.get("sensor.living_room_homepod_humidity")
    assert state is not None
    assert float(state.state) == 48.2
    assert state.attributes["unit_of_measurement"] == "%"


async def test_stale_binary_sensor_fresh(hass, setup_integration):
    """Stale sensor should be off immediately after a push."""
    coordinator = setup_integration
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.living_room_homepod_stale")
    assert state is not None
    assert state.state == "off"


async def test_stale_binary_sensor_when_no_data(hass, setup_integration):
    """Stale sensor should be on when no data has arrived yet."""
    coordinator = setup_integration
    # No webhook push — stale from the start (no last_seen)
    # Manually inject a device with no last_seen
    from custom_components.homepod_sensors.coordinator import HomePodDeviceData

    dev = HomePodDeviceData("HP000000000099", "Test Pod")
    coordinator.data["HP000000000099"] = dev
    coordinator.async_set_updated_data(coordinator.data)

    # Trigger new-device callbacks to create entities
    for cb in coordinator._new_device_callbacks:
        cb("HP000000000099", dev)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_pod_stale")
    assert state is not None
    assert state.state == "on"


async def test_multiple_devices_create_separate_entities(hass, setup_integration):
    """Each HomePod should have its own set of entities."""
    coordinator = setup_integration
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])
    await hass.async_block_till_done()

    assert hass.states.get("sensor.living_room_homepod_temperature") is not None
    assert hass.states.get("sensor.bedroom_homepod_mini_temperature") is not None
    assert hass.states.get("sensor.living_room_homepod_humidity") is not None
    assert hass.states.get("sensor.bedroom_homepod_mini_humidity") is not None
