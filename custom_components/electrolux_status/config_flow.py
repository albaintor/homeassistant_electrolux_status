"""Adds config flow for Electrolux Status."""

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_CLOUD_PUSH,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_COUNTRY_CODE, CONF_PASSWORD
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
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_LANGUAGE,
    CONF_NOTIFICATION_DEFAULT,
    CONF_NOTIFICATION_DIAG,
    CONF_NOTIFICATION_WARNING,
    CONF_REFRESH_TOKEN,
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
                if user_input[CONF_API_KEY] == entry.data.get("api_key", None):
                    return self.async_abort(reason="already_configured_account")

            valid = await self._test_credentials(
                user_input[CONF_API_KEY],
                user_input[CONF_ACCESS_TOKEN],
                user_input[CONF_REFRESH_TOKEN],
            )
            if valid:
                return self.async_create_entry(title="Electrolux", data=user_input)
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
                user_input[CONF_API_KEY],
                user_input[CONF_ACCESS_TOKEN],
                user_input[CONF_REFRESH_TOKEN],
            )
            if valid:
                return self.async_create_entry(title="Electrolux", data=user_input)
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
            vol.Required(CONF_API_KEY): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="api-key")
            ),
            vol.Required(CONF_ACCESS_TOKEN): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="access-token"
                )
            ),
            vol.Required(CONF_REFRESH_TOKEN): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="refresh-token"
                )
            ),
        }
        if self.show_advanced_options:
            data_schema = {
                **data_schema,
                vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): selector(
                    {
                        "select": {
                            "options": list(languages.keys()),
                            "mode": "dropdown",
                        }
                    }
                ),
                vol.Optional(CONF_NOTIFICATION_DEFAULT, default=True): cv.boolean,
                vol.Optional(CONF_NOTIFICATION_WARNING, default=False): cv.boolean,
                vol.Optional(CONF_NOTIFICATION_DIAG, default=False): cv.boolean,
            }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _test_credentials(self, api_key, access_token, refresh_token):
        """Return true if credentials is valid."""
        try:
            client = get_electrolux_session(
                api_key, access_token, refresh_token, async_get_clientsession(self.hass)
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
        self._config_entry = config_entry
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
        current_country_code = self.config_entry.data.get(CONF_COUNTRY_CODE, None)
        notify_alert = self.config_entry.data.get(CONF_NOTIFICATION_DEFAULT, True)
        notify_warning = self.config_entry.data.get(CONF_NOTIFICATION_WARNING, False)
        notify_diagnostic = self.config_entry.data.get(CONF_NOTIFICATION_DIAG, False)
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
                    vol.Required(
                        CONF_COUNTRY_CODE, default=current_country_code
                    ): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.TEXT, autocomplete="country-code"
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
                        CONF_NOTIFICATION_DEFAULT, default=notify_alert
                    ): cv.boolean,
                    vol.Optional(
                        CONF_NOTIFICATION_WARNING, default=notify_warning
                    ): cv.boolean,
                    vol.Optional(
                        CONF_NOTIFICATION_DIAG, default=notify_diagnostic
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
            CONF_COUNTRY_CODE: self.options[CONF_COUNTRY_CODE],
            CONF_LANGUAGE: self.options[CONF_LANGUAGE],
            CONF_NOTIFICATION_DEFAULT: self.options[CONF_NOTIFICATION_DEFAULT],
            CONF_NOTIFICATION_WARNING: self.options[CONF_NOTIFICATION_WARNING],
            CONF_NOTIFICATION_DIAG: self.options[CONF_NOTIFICATION_DIAG],
        }
        self.hass.config_entries.async_update_entry(self.config_entry, data=data)
        return self.async_create_entry(
            title="Electrolux",
            data=data,
        )
