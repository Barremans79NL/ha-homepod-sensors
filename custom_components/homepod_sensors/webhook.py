"""Webhook handler for HomePod Sensors integration."""
from __future__ import annotations

import logging

from aiohttp import web
from homeassistant.components.webhook import Request
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_handle_webhook(
    hass: HomeAssistant, webhook_id: str, request: Request
) -> web.Response:
    """Handle incoming webhook POST from the iOS Shortcut."""
    try:
        payload = await request.json()
    except Exception:
        _LOGGER.warning("HomePod Sensors: received non-JSON webhook payload")
        return web.Response(status=400, text="Expected JSON payload")

    devices = payload.get("devices")
    if not isinstance(devices, list):
        _LOGGER.warning("HomePod Sensors: 'devices' key missing or not a list")
        return web.Response(status=400, text="'devices' must be a list")

    # Find the coordinator for this webhook_id across all config entries.
    for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
        if _entry_webhook_id(hass, entry_id) == webhook_id:
            coordinator.handle_webhook_payload(devices)
            _LOGGER.debug(
                "HomePod Sensors: processed %d device(s) from webhook", len(devices)
            )
            return web.Response(status=200, text="OK")

    _LOGGER.error("HomePod Sensors: no coordinator found for webhook_id %s", webhook_id)
    return web.Response(status=404, text="Integration not found")


def _entry_webhook_id(hass: HomeAssistant, entry_id: str) -> str | None:
    """Return the webhook_id for the given config entry id."""
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        return None
    return entry.data.get("webhook_id")
