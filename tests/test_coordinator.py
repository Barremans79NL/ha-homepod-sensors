"""Tests for the HomePod Sensors coordinator."""
from __future__ import annotations

from homeassistant.helpers.storage import Store

from custom_components.homepod_sensors.const import STORAGE_KEY, STORAGE_VERSION
from custom_components.homepod_sensors.coordinator import HomePodCoordinator

from .conftest import SAMPLE_PAYLOAD


async def test_restores_devices_from_store(hass):
    """A restart should recreate entities for previously-seen devices."""
    await Store(hass, STORAGE_VERSION, STORAGE_KEY).async_save(
        [{"serial": "HP000000000001", "name": "Living Room HomePod"}]
    )

    coordinator = HomePodCoordinator(hass, update_interval_minutes=5)
    await coordinator.async_load_stored_devices()

    assert "HP000000000001" in coordinator.data
    device = coordinator.data["HP000000000001"]
    assert device.name == "Living Room HomePod"
    # No readings persisted — value stays absent until the next push.
    assert device.temperature_c is None
    assert device.last_seen is None


async def test_load_stored_devices_without_store_is_noop(hass):
    """Missing store file should not raise and should leave data empty."""
    coordinator = HomePodCoordinator(hass, update_interval_minutes=5)
    await coordinator.async_load_stored_devices()
    assert coordinator.data == {}


async def test_non_numeric_reading_skips_only_that_device(hass):
    """A malformed reading must not abort processing of the rest of the payload."""
    coordinator = HomePodCoordinator(hass, update_interval_minutes=5)
    coordinator.handle_webhook_payload(
        [
            {
                "serial": "HP000000000001",
                "name": "Bad",
                "temperature_c": "not-a-number",
                "humidity_pct": 50.0,
            },
            {
                "serial": "HP000000000002",
                "name": "Good",
                "temperature_c": 20.0,
                "humidity_pct": 50.0,
            },
        ]
    )

    assert "HP000000000001" not in coordinator.data
    assert coordinator.data["HP000000000002"].temperature_c == 20.0


async def test_non_numeric_reading_does_not_leave_partial_device(hass):
    """A device that fails conversion on a later push keeps its previous value."""
    coordinator = HomePodCoordinator(hass, update_interval_minutes=5)
    coordinator.handle_webhook_payload(
        [{"serial": "HP1", "name": "Pod", "temperature_c": 21.0, "humidity_pct": 40.0}]
    )
    coordinator.handle_webhook_payload(
        [{"serial": "HP1", "name": "Pod", "temperature_c": "", "humidity_pct": 40.0}]
    )

    assert coordinator.data["HP1"].temperature_c == 21.0


async def test_new_devices_are_persisted(hass):
    """Handling a payload with new devices should write them to the store."""
    coordinator = HomePodCoordinator(hass, update_interval_minutes=5)
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])

    # Flush the debounced save.
    await coordinator._store.async_save(coordinator._devices_to_store())

    restored = HomePodCoordinator(hass, update_interval_minutes=5)
    await restored.async_load_stored_devices()
    assert set(restored.data) == {"HP000000000001", "HP000000000002"}
