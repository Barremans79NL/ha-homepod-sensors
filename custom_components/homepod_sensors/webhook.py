"""Webhook handler for HomePod Sensors integration."""
from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.webhook import Request
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_SECRET
from .coordinator import HomePodCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_handle_webhook(
    coordinator: HomePodCoordinator,
    entry: ConfigEntry,
    hass: HomeAssistant,
    webhook_id: str,
    request: Request,
) -> web.Response:
    """Handle incoming webhook POST from the iOS Shortcut.

    `coordinator` and `entry` are bound via functools.partial at registration
    time; `single_instance_allowed` guarantees there is exactly one of each.
    """
    try:
        payload = await request.json()
    except Exception:
        _LOGGER.warning("HomePod Sensors: received non-JSON webhook payload")
        return web.Response(status=400, text="Expected JSON payload")

    devices = payload.get("devices") if isinstance(payload, dict) else None
    if not isinstance(devices, list):
        _LOGGER.warning("HomePod Sensors: 'devices' key missing or not a list")
        return web.Response(status=400, text="'devices' must be a list")

    expected_secret = entry.options.get(CONF_SECRET) or entry.data.get(CONF_SECRET)
    if expected_secret and payload.get("secret") != expected_secret:
        _LOGGER.warning("HomePod Sensors: rejected webhook with invalid secret")
        return web.Response(status=401, text="Invalid secret")

    coordinator.handle_webhook_payload(devices)
    _LOGGER.debug("HomePod Sensors: processed %d device(s) from webhook", len(devices))
    return web.Response(status=200, text="OK")
