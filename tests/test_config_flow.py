"""Tests for HomePod Sensors config flow."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries

from custom_components.homepod_sensors.const import (
    CONF_UPDATE_INTERVAL,
    CONF_WEBHOOK_ID,
    DOMAIN,
)


async def test_config_flow_creates_entry(hass):
    """Config flow should create a config entry with webhook ID and interval."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    with patch("homeassistant.components.webhook.async_register"), patch(
        "homeassistant.components.webhook.async_unregister"
    ), patch(
        "custom_components.homepod_sensors.config_flow.get_url",
        return_value="http://homeassistant.local:8123",
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_UPDATE_INTERVAL: 5},
        )

    assert result["type"] == "create_entry"
    assert result["title"] == "HomePod Sensors"
    assert CONF_WEBHOOK_ID in result["data"]
    assert result["data"][CONF_UPDATE_INTERVAL] == 5


async def test_config_flow_form_provides_all_description_placeholders(hass):
    """The initial form must supply every placeholder used in the translation string.

    translations/en.json references both {webhook_url} and {update_interval}; a
    missing key breaks the setup dialog rendering.
    """
    with patch(
        "custom_components.homepod_sensors.config_flow.get_url",
        return_value="http://homeassistant.local:8123",
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] == "form"
    placeholders = result["description_placeholders"]
    assert "webhook_url" in placeholders
    assert "update_interval" in placeholders


async def test_config_flow_single_instance(hass, mock_config_entry):
    """Only one instance of the integration is allowed."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "abort"
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_updates_interval(hass, mock_config_entry):
    """Options flow should update the update interval."""
    mock_config_entry.add_to_hass(hass)
    with patch("homeassistant.components.webhook.async_register"), patch(
        "homeassistant.components.webhook.async_unregister"
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == "form"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_UPDATE_INTERVAL: 10},
    )
    assert result["type"] == "create_entry"
    assert mock_config_entry.options[CONF_UPDATE_INTERVAL] == 10
