"""Tests for the HomePod Sensors coordinator."""
from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import Store

from custom_components.homepod_sensors.const import DOMAIN, STORAGE_KEY, STORAGE_VERSION
from custom_components.homepod_sensors.coordinator import HomePodCoordinator

from .conftest import SAMPLE_PAYLOAD


def _reading(serial, name=None, temp=20.0, humidity=40.0):
    device = {"serial": serial, "temperature_c": temp, "humidity_pct": humidity}
    if name is not None:
        device["name"] = name
    return device


async def test_restores_devices_from_store(hass):
    """A restart should recreate entities for previously-seen devices."""
    await Store(hass, STORAGE_VERSION, STORAGE_KEY).async_save(
        [{"serial": "HP000000000001", "name": "Living Room HomePod"}]
    )

    coordinator = HomePodCoordinator(hass)
    await coordinator.async_load_stored_devices()

    assert "HP000000000001" in coordinator.data
    device = coordinator.data["HP000000000001"]
    assert device.name == "Living Room HomePod"
    # No readings persisted — value stays absent until the next push.
    assert device.temperature_c is None
    assert device.last_seen is None


async def test_load_stored_devices_without_store_is_noop(hass):
    """Missing store file should not raise and should leave data empty."""
    coordinator = HomePodCoordinator(hass)
    await coordinator.async_load_stored_devices()
    assert coordinator.data == {}


async def test_non_numeric_reading_skips_only_that_device(hass):
    """A malformed reading must not abort processing of the rest of the payload."""
    coordinator = HomePodCoordinator(hass)
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
    coordinator = HomePodCoordinator(hass)
    coordinator.handle_webhook_payload(
        [{"serial": "HP1", "name": "Pod", "temperature_c": 21.0, "humidity_pct": 40.0}]
    )
    coordinator.handle_webhook_payload(
        [{"serial": "HP1", "name": "Pod", "temperature_c": "", "humidity_pct": 40.0}]
    )

    assert coordinator.data["HP1"].temperature_c == 21.0


async def test_out_of_range_reading_is_dropped(hass):
    """Implausible values must not reach the sensor (they pollute LTS forever)."""
    coordinator = HomePodCoordinator(hass)
    coordinator.handle_webhook_payload(
        [
            {"serial": "HP1", "name": "Cold", "temperature_c": -999.0, "humidity_pct": 50.0},
            {"serial": "HP2", "name": "Wet", "temperature_c": 20.0, "humidity_pct": 1e9},
            {"serial": "HP3", "name": "OK", "temperature_c": 20.0, "humidity_pct": 50.0},
        ]
    )

    assert "HP1" not in coordinator.data
    assert "HP2" not in coordinator.data
    assert coordinator.data["HP3"].temperature_c == 20.0


async def test_range_bounds_are_inclusive(hass):
    """Values exactly on the boundary are accepted."""
    coordinator = HomePodCoordinator(hass)
    coordinator.handle_webhook_payload(
        [{"serial": "HP1", "name": "Edge", "temperature_c": 80.0, "humidity_pct": 0.0}]
    )

    assert coordinator.data["HP1"].temperature_c == 80.0
    assert coordinator.data["HP1"].humidity_pct == 0.0


async def test_device_name_follows_rename(hass):
    """Renaming the HomePod in the Home app should update the stored name."""
    coordinator = HomePodCoordinator(hass)
    coordinator.handle_webhook_payload([_reading("HP1", name="Kitchen")])
    coordinator.handle_webhook_payload([_reading("HP1", name="Dining Room")])

    assert coordinator.data["HP1"].name == "Dining Room"


async def test_missing_name_does_not_override_existing(hass):
    """A payload without a name must not reset the device to the default name."""
    coordinator = HomePodCoordinator(hass)
    coordinator.handle_webhook_payload([_reading("HP1", name="Kitchen")])
    coordinator.handle_webhook_payload([_reading("HP1")])

    assert coordinator.data["HP1"].name == "Kitchen"


async def test_rename_propagates_to_device_registry(hass, mock_config_entry):
    """A rename should reach the device registry entry (unless user-overridden)."""
    mock_config_entry.add_to_hass(hass)
    registry = dr.async_get(hass)
    registry.async_get_or_create(
        config_entry_id=mock_config_entry.entry_id,
        identifiers={(DOMAIN, "HP1")},
        name="Kitchen",
    )

    coordinator = HomePodCoordinator(hass)
    coordinator.handle_webhook_payload([_reading("HP1", name="Kitchen")])
    coordinator.handle_webhook_payload([_reading("HP1", name="Dining Room")])

    device = registry.async_get_device(identifiers={(DOMAIN, "HP1")})
    assert device.name == "Dining Room"


async def test_new_devices_are_persisted(hass):
    """Handling a payload with new devices should write them to the store."""
    coordinator = HomePodCoordinator(hass)
    coordinator.handle_webhook_payload(SAMPLE_PAYLOAD["devices"])

    # Flush the debounced save.
    await coordinator._store.async_save(coordinator._devices_to_store())

    restored = HomePodCoordinator(hass)
    await restored.async_load_stored_devices()
    assert set(restored.data) == {"HP000000000001", "HP000000000002"}
