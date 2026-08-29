"""Data coordinator for HomePod Sensors integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    MAX_HUMIDITY_PCT,
    MAX_TEMPERATURE_C,
    MIN_HUMIDITY_PCT,
    MIN_TEMPERATURE_C,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

# Debounce disk writes; the device list changes rarely (only on first contact).
_SAVE_DELAY = 10


class HomePodDeviceData:
    """Holds the latest data for a single HomePod Mini."""

    def __init__(self, serial: str, name: str) -> None:
        self.serial = serial
        self.name = name
        self.temperature_c: float | None = None
        self.humidity_pct: float | None = None
        self.last_seen: datetime | None = None

    def update(self, temperature_c: float, humidity_pct: float) -> None:
        self.temperature_c = temperature_c
        self.humidity_pct = humidity_pct
        self.last_seen = datetime.now(UTC)


class HomePodCoordinator(DataUpdateCoordinator[dict[str, HomePodDeviceData]]):
    """Coordinator that receives push data from iOS Shortcuts webhook."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # No polling — we are purely push-driven, so no update_interval.
        )
        self.data: dict[str, HomePodDeviceData] = {}
        self._new_device_callbacks: list[Callable[[str, HomePodDeviceData], None]] = []
        self._store: Store[list[dict[str, str]]] = Store(
            hass, STORAGE_VERSION, STORAGE_KEY
        )

    async def async_load_stored_devices(self) -> None:
        """Restore the last-known device list from disk.

        Readings are push-only and not persisted, so restored devices start
        without a value until the next webhook arrives. Restoring them here
        means their entities are created immediately on startup instead of
        vanishing until the iOS Shortcut next reports in.
        """
        stored = await self._store.async_load()
        if not stored:
            return
        for item in stored:
            serial = (item.get("serial") or "").strip()
            if not serial or serial in self.data:
                continue
            name = (item.get("name") or "").strip() or f"HomePod {serial[:6]}"
            self.data[serial] = HomePodDeviceData(serial=serial, name=name)

    @callback
    def _devices_to_store(self) -> list[dict[str, str]]:
        """Serialise the current device list for persistence."""
        return [
            {"serial": device.serial, "name": device.name}
            for device in self.data.values()
        ]

    @callback
    def _persist_devices(self) -> None:
        """Schedule a debounced write of the current device list."""
        self._store.async_delay_save(self._devices_to_store, _SAVE_DELAY)

    @callback
    def register_new_device_callback(
        self, cb: Callable[[str, HomePodDeviceData], None]
    ) -> None:
        """Register a callback invoked when a previously-unseen device reports in."""
        self._new_device_callbacks.append(cb)

    def handle_webhook_payload(self, devices: list[dict]) -> None:
        """Process incoming payload from the iOS Shortcut."""
        new_serials: list[str] = []
        device_list_changed = False

        for device in devices:
            serial = device.get("serial", "").strip()
            reported_name = (device.get("name") or "").strip()
            name = reported_name or f"HomePod {serial[:6]}"
            temp = device.get("temperature_c")
            humidity = device.get("humidity_pct")

            if not serial or temp is None or humidity is None:
                _LOGGER.warning("Skipping malformed device payload: %s", device)
                continue

            try:
                temperature_c = float(temp)
                humidity_pct = float(humidity)
            except (TypeError, ValueError):
                _LOGGER.warning(
                    "Skipping device %s: non-numeric temperature/humidity in %s",
                    serial,
                    device,
                )
                continue

            if not (
                MIN_TEMPERATURE_C <= temperature_c <= MAX_TEMPERATURE_C
            ) or not (MIN_HUMIDITY_PCT <= humidity_pct <= MAX_HUMIDITY_PCT):
                _LOGGER.warning(
                    "Skipping device %s: reading out of range (%s C, %s %%)",
                    serial,
                    temperature_c,
                    humidity_pct,
                )
                continue

            if serial not in self.data:
                self.data[serial] = HomePodDeviceData(serial=serial, name=name)
                new_serials.append(serial)
                device_list_changed = True
            elif reported_name and self.data[serial].name != reported_name:
                # HomePod was renamed in the Home app — follow it.
                self.data[serial].name = reported_name
                self._rename_registry_device(serial, reported_name)
                device_list_changed = True

            self.data[serial].update(temperature_c, humidity_pct)

        # Notify coordinator listeners (existing entities) of updated data.
        self.async_set_updated_data(self.data)

        # Notify platform callbacks about brand-new devices.
        for serial in new_serials:
            for cb in self._new_device_callbacks:
                cb(serial, self.data[serial])

        # Persist the device list so entities survive a restart.
        if device_list_changed:
            self._persist_devices()

    @callback
    def _rename_registry_device(self, serial: str, name: str) -> None:
        """Push a renamed HomePod through to the device registry entry."""
        registry = dr.async_get(self.hass)
        device = registry.async_get_device(identifiers={(DOMAIN, serial)})
        if device is not None and device.name_by_user is None:
            registry.async_update_device(device.id, name=name)

    async def _async_update_data(self) -> dict[str, HomePodDeviceData]:
        """Not used — data arrives via webhook push only."""
        return self.data
