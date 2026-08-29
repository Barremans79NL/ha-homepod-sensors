"""Sensor platform for HomePod Sensors integration."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
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
    """Set up HomePod sensor entities."""
    coordinator: HomePodCoordinator = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _add_sensors_for_device(serial: str, device: HomePodDeviceData) -> None:
        async_add_entities(
            [
                HomePodTemperatureSensor(coordinator, entry, serial),
                HomePodHumiditySensor(coordinator, entry, serial),
                HomePodLastUpdatedSensor(coordinator, entry, serial),
            ]
        )

    coordinator.register_new_device_callback(_add_sensors_for_device)

    # Add entities for devices already known (e.g. after HA restart).
    for serial in coordinator.data:
        _add_sensors_for_device(serial, coordinator.data[serial])


class HomePodBaseSensor(CoordinatorEntity[HomePodCoordinator], SensorEntity):
    """Base class for HomePod sensor entities."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: HomePodCoordinator, entry: ConfigEntry, serial: str
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._serial = serial

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
            model="HomePod Mini",
        )

    @property
    def available(self) -> bool:
        return self._device_data is not None and self._device_data.last_seen is not None


class HomePodMeasurementSensor(HomePodBaseSensor):
    """A reading that should stop presenting a value once it goes stale."""

    @property
    def available(self) -> bool:
        return super().available and not is_stale(self._device_data, self._entry)


class HomePodTemperatureSensor(HomePodMeasurementSensor):
    """Temperature sensor for a HomePod Mini."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_name = "Temperature"

    def __init__(
        self, coordinator: HomePodCoordinator, entry: ConfigEntry, serial: str
    ) -> None:
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_temperature"

    @property
    def native_value(self) -> float | None:
        device = self._device_data
        return device.temperature_c if device else None


class HomePodHumiditySensor(HomePodMeasurementSensor):
    """Humidity sensor for a HomePod Mini."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Humidity"

    def __init__(
        self, coordinator: HomePodCoordinator, entry: ConfigEntry, serial: str
    ) -> None:
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_humidity"

    @property
    def native_value(self) -> float | None:
        device = self._device_data
        return device.humidity_pct if device else None


class HomePodLastUpdatedSensor(HomePodBaseSensor):
    """Sensor showing the last time data was received from iOS.

    Deliberately extends the base (not the measurement) class: it must keep
    reporting the last-seen timestamp even when that timestamp is stale.
    """

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_name = "Last Updated"
    _attr_entity_registry_enabled_default = False  # diagnostic — off by default

    def __init__(
        self, coordinator: HomePodCoordinator, entry: ConfigEntry, serial: str
    ) -> None:
        super().__init__(coordinator, entry, serial)
        self._attr_unique_id = f"{serial}_last_updated"

    @property
    def native_value(self) -> datetime | None:
        device = self._device_data
        return device.last_seen if device else None
