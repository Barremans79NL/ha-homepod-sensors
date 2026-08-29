"""HomePod Sensors integration for Home Assistant."""
from __future__ import annotations

import logging

# Aliased: importing the local `.webhook` submodule below binds the name
# `webhook` on this package, which would otherwise shadow this import and
# turn `webhook.async_register` into an AttributeError at setup time.
from homeassistant.components import webhook as ha_webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_WEBHOOK_ID, DOMAIN, PLATFORMS
from .coordinator import HomePodCoordinator
from .webhook import async_handle_webhook

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HomePod Sensors from a config entry."""
    coordinator = HomePodCoordinator(hass)
    await coordinator.async_load_stored_devices()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    webhook_id = entry.data[CONF_WEBHOOK_ID]
    ha_webhook.async_register(
        hass,
        DOMAIN,
        "HomePod Sensors",
        webhook_id,
        async_handle_webhook,
        # The iOS Shortcut pushes from the home network (or via VPN); reject
        # requests that reach the endpoint from the internet.
        local_only=True,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry so a changed update interval / secret takes effect."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ha_webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
