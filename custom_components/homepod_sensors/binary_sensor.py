"""Binary sensor platform for HomePod Sensors integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HomePodCoordinator, HomePodDeviceData
from .staleness import is_stale


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HomePod binary sensor entities."""
    coordinator: HomePodCoordinator = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _add_binary_sensors_for_device(serial: str, device: HomePodDeviceData) -> None:
        async_add_entities([HomePodStaleSensor(coordinator, entry, serial)])

    coordinator.register_new_device_callback(_add_binary_sensors_for_device)

    for serial in coordinator.data:
        _add_binary_sensors_for_device(serial, coordinator.data[serial])


class HomePodStaleSensor(CoordinatorEntity[HomePodCoordinator], BinarySensorEntity):
    """Binary sensor that is ON when a HomePod has not reported recently."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_has_entity_name = True
    _attr_name = "Stale"

    def __init__(
        self,
        coordinator: HomePodCoordinator,
        entry: ConfigEntry,
        serial: str,
    ) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._entry = entry
        self._attr_unique_id = f"{serial}_stale"

    @property
    def _device_data(self) -> HomePodDeviceData | None:
        return self.coordinator.data.get(self._serial)

    @property
    def device_info(self) -> DeviceInfo:
        device = self._device_data
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial)},
            name=device.name if device else f"HomePod {self._serial[:6]}",
            manufacturer="Apple",
            model="HomePod mini",
        )

    @property
    def is_on(self) -> bool:
        return is_stale(self._device_data, self._entry)

    @property
    def available(self) -> bool:
        return self._device_data is not None
