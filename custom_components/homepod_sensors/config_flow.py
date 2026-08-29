"""Config flow for HomePod Sensors integration."""
from __future__ import annotations

import secrets
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.network import get_url

from .const import CONF_UPDATE_INTERVAL, CONF_WEBHOOK_ID, DEFAULT_UPDATE_INTERVAL, DOMAIN, NAME


class HomePodSensorsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HomePod Sensors."""

    VERSION = 1

    def __init__(self) -> None:
        self._webhook_id: str = secrets.token_hex(16)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show webhook URL and update interval configuration."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(
                title=NAME,
                data={
                    CONF_WEBHOOK_ID: self._webhook_id,
                    CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                },
            )

        try:
            base_url = get_url(self.hass, allow_internal=True, allow_ip=True)
        except Exception:
            base_url = "http://<your-ha-ip>:8123"

        webhook_url = f"{base_url}/api/webhook/{self._webhook_id}"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): vol.All(int, vol.Range(min=1, max=60)),
                }
            ),
            description_placeholders={
                "webhook_url": webhook_url,
                "update_interval": str(DEFAULT_UPDATE_INTERVAL),
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HomePodSensorsOptionsFlow:
        return HomePodSensorsOptionsFlow(config_entry)


class HomePodSensorsOptionsFlow(config_entries.OptionsFlow):
    """Handle options for HomePod Sensors."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self._config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self._config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): vol.All(
                        int, vol.Range(min=1, max=60)
                    ),
                }
            ),
        )
