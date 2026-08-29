"""Shared staleness calculation for HomePod entities.

Both the temperature/humidity sensors (for `available`) and the stale
binary sensor (for `is_on`) key off the same threshold: data older than
`DEFAULT_STALENESS_MULTIPLIER` times the configured update interval.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_STALENESS_MULTIPLIER,
    DEFAULT_UPDATE_INTERVAL,
)
from .coordinator import HomePodDeviceData


def staleness_threshold(entry: ConfigEntry) -> timedelta:
    """Return the age at which a device's data is considered stale."""
    interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
    )
    return timedelta(minutes=interval * DEFAULT_STALENESS_MULTIPLIER)


def is_stale(device: HomePodDeviceData | None, entry: ConfigEntry) -> bool:
    """Return True when there is no sufficiently recent reading for this device."""
    if device is None or device.last_seen is None:
        return True
    return datetime.now(UTC) - device.last_seen > staleness_threshold(entry)
