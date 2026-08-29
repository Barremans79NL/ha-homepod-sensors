"""Constants for HomePod Sensors integration."""
from __future__ import annotations

DOMAIN = "homepod_sensors"
NAME = "HomePod Sensors"

CONF_UPDATE_INTERVAL = "update_interval"
CONF_WEBHOOK_ID = "webhook_id"

DEFAULT_UPDATE_INTERVAL = 5  # minutes
DEFAULT_STALENESS_MULTIPLIER = 3  # stale after 3x the update interval

# Plausibility bounds for incoming readings. Anything outside is dropped so a
# stray value can't pollute the recorder's long-term statistics.
MIN_TEMPERATURE_C = -40.0
MAX_TEMPERATURE_C = 80.0
MIN_HUMIDITY_PCT = 0.0
MAX_HUMIDITY_PCT = 100.0

# Persisted store of last-known devices, so entities survive a restart.
STORAGE_VERSION = 1
STORAGE_KEY = DOMAIN

PLATFORMS = ["sensor", "binary_sensor"]
