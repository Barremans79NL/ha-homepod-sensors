"""Constants for HomePod Sensors integration."""
from __future__ import annotations

DOMAIN = "homepod_sensors"
NAME = "HomePod Sensors"

CONF_UPDATE_INTERVAL = "update_interval"
CONF_WEBHOOK_ID = "webhook_id"

DEFAULT_UPDATE_INTERVAL = 5  # minutes
DEFAULT_STALENESS_MULTIPLIER = 3  # stale after 3x the update interval

# Persisted store of last-known devices, so entities survive a restart.
STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN

PLATFORMS = ["sensor", "binary_sensor"]
