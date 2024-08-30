"""Adds config flow for Electrolux Status."""

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    CONN_CLASS_CLOUD_PUSH,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
    selector,
)

from .const import (
    CONF_LANGUAGE,
    CONF_NOTIFICATIONS,
    DEFAULT_LANGUAGE,
    DOMAIN,
    languages,
)
from .util import get_electrolux_session

_LOGGER = logging.getLogger(__name__)


class ElectroluxStatusFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Electrolux Status."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_CLOUD_PUSH

    def __init__(self) -> None:
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            # check if the specified account is configured already
            # to prevent them from being added twice
            for entry in self._async_current_entries():
                if user_input[CONF_USERNAME] == entry.data.get("username", None):
                    return self.async_abort(reason="already_configured_account")

            valid = await self._test_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            self._errors["base"] = "invalid_auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle configuration by re-auth."""
        return await self.async_step_reauth_validate(entry_data)

    async def async_step_reauth_validate(self, user_input=None) -> ConfigFlowResult:
        """Handle reauth and validation."""
        self._errors = {}
        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            self._errors["base"] = "invalid_auth"
            return await self._show_config_form(user_input)
        return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Present the configuration options dialog."""
        return ElectroluxStatusOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        data_schema = {
            vol.Required(CONF_USERNAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username")
            ),
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
        }
        if self.show_advanced_options:
            data_schema.update(
                {
                    vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): selector(
                        {
                            "select": {
                                "options": list(languages.keys()),
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Optional(CONF_NOTIFICATIONS, default=True): cv.boolean,
                }
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _test_credentials(self, username, password):
        """Return true if credentials is valid."""
        try:
            client = get_electrolux_session(
                username, password, async_get_clientsession(self.hass)
            )
            await client.get_appliances_list()
        except Exception as inst:  # pylint: disable=broad-except  # noqa: BLE001
            _LOGGER.error("Authentication to electrolux failed: %s", inst)
            return False
        return True


class ElectroluxStatusOptionsFlowHandler(OptionsFlow):
    """Config flow options handler for Electrolux Status."""

    def __init__(self, config_entry) -> None:
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        selected_language = self.config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        current_password = self.config_entry.data.get(CONF_PASSWORD, None)
        send_notifications = self.config_entry.data.get(CONF_NOTIFICATIONS, True)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD, default=current_password): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD,
                            autocomplete="current-password",
                        )
                    ),
                    vol.Required(CONF_LANGUAGE, default=selected_language): selector(
                        {
                            "select": {
                                "options": list(languages.keys()),
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Optional(
                        CONF_NOTIFICATIONS, default=send_notifications
                    ): cv.boolean,
                    # vol.Optional(
                    #     CONF_RENEW_INTERVAL,
                    #     default=self.config_entry.options.get(
                    #         CONF_RENEW_INTERVAL, DEFAULT_WEBSOCKET_RENEWAL_DELAY
                    #     ),
                    # ): cv.positive_int,
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        _LOGGER.debug("Electrolux updating configuration")
        data = {
            **self.config_entry.data,
            CONF_PASSWORD: self.options[CONF_PASSWORD],
            CONF_LANGUAGE: self.options[CONF_LANGUAGE],
            CONF_NOTIFICATIONS: self.options[CONF_NOTIFICATIONS],
        }
        self.hass.config_entries.async_update_entry(self.config_entry, data=data)
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME),
            data=data,
        )
