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
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_NOTIFICATION_DEFAULT,
    CONF_NOTIFICATION_DIAG,
    CONF_NOTIFICATION_WARNING,
    CONF_REFRESH_TOKEN,
    DOMAIN,
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
        # Store the entry data for later use
        self._reauth_entry_data = entry_data
        return await self.async_step_reauth_validate()

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
                # Update the existing entry with new tokens
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data=user_input
                )
            self._errors["base"] = "invalid_auth"
            return await self._show_config_form(user_input, "reauth_validate")
        return await self._show_config_form(self._reauth_entry_data, "reauth_validate")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Present the configuration options dialog."""
        return ElectroluxStatusOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input, step_id="user"):
        """Show the configuration form to edit location data."""
        defaults = user_input or {}

        data_schema = {
            vol.Required(
                CONF_API_KEY, default=defaults.get(CONF_API_KEY, "")
            ): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="api-key")
            ),
            vol.Required(
                CONF_ACCESS_TOKEN, default=defaults.get(CONF_ACCESS_TOKEN, "")
            ): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="access-token"
                )
            ),
            vol.Required(
                CONF_REFRESH_TOKEN, default=defaults.get(CONF_REFRESH_TOKEN, "")
            ): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="refresh-token"
                )
            ),
        }
        if self.show_advanced_options:
            data_schema = {
                **data_schema,
                vol.Optional(
                    CONF_NOTIFICATION_DEFAULT,
                    default=defaults.get(CONF_NOTIFICATION_DEFAULT, True),
                ): cv.boolean,
                vol.Optional(
                    CONF_NOTIFICATION_WARNING,
                    default=defaults.get(CONF_NOTIFICATION_WARNING, False),
                ): cv.boolean,
                vol.Optional(
                    CONF_NOTIFICATION_DIAG,
                    default=defaults.get(CONF_NOTIFICATION_DIAG, False),
                ): cv.boolean,
            }
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
            description_placeholders={"url": "https://developer.electrolux.one/"},
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
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_user()

    def _get_options_schema(self):
        """Get the options schema with current values."""
        # Get current values from config entry data and options
        current_api_key = self._config_entry.data.get(CONF_API_KEY, "")
        current_access_token = self._config_entry.data.get(CONF_ACCESS_TOKEN, "")
        current_refresh_token = self._config_entry.data.get(CONF_REFRESH_TOKEN, "")
        current_notify_default = self._config_entry.data.get(
            CONF_NOTIFICATION_DEFAULT, True
        )
        current_notify_warning = self._config_entry.data.get(
            CONF_NOTIFICATION_WARNING, False
        )
        current_notify_diag = self._config_entry.data.get(CONF_NOTIFICATION_DIAG, False)

        return vol.Schema(
            {
                vol.Optional(CONF_API_KEY, default=current_api_key): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.TEXT, autocomplete="api-key"
                    )
                ),
                vol.Optional(
                    CONF_ACCESS_TOKEN, default=current_access_token
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD, autocomplete="access-token"
                    )
                ),
                vol.Optional(
                    CONF_REFRESH_TOKEN, default=current_refresh_token
                ): TextSelector(
                    TextSelectorConfig(
                        type=TextSelectorType.PASSWORD, autocomplete="refresh-token"
                    )
                ),
                vol.Optional(
                    CONF_NOTIFICATION_DEFAULT, default=current_notify_default
                ): cv.boolean,
                vol.Optional(
                    CONF_NOTIFICATION_WARNING, default=current_notify_warning
                ): cv.boolean,
                vol.Optional(
                    CONF_NOTIFICATION_DIAG, default=current_notify_diag
                ): cv.boolean,
            }
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

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle the user step."""
        if user_input is not None:
            # Test credentials if any API credentials were provided
            if any(
                key in user_input
                for key in [CONF_API_KEY, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN]
            ):
                api_key = user_input.get(
                    CONF_API_KEY, self._config_entry.data.get(CONF_API_KEY)
                )
                access_token = user_input.get(
                    CONF_ACCESS_TOKEN, self._config_entry.data.get(CONF_ACCESS_TOKEN)
                )
                refresh_token = user_input.get(
                    CONF_REFRESH_TOKEN, self._config_entry.data.get(CONF_REFRESH_TOKEN)
                )

                if not await self._test_credentials(
                    api_key, access_token, refresh_token
                ):
                    return self.async_show_form(
                        step_id="user",
                        data_schema=self._get_options_schema(),
                        errors={"base": "invalid_auth"},
                    )

            # Update the config entry data with new options
            new_data = dict(self._config_entry.data)
            new_options = dict(self._config_entry.options)

            # API credentials and notifications go in data (require restart)
            if CONF_API_KEY in user_input:
                new_data[CONF_API_KEY] = user_input[CONF_API_KEY]
            if CONF_ACCESS_TOKEN in user_input:
                new_data[CONF_ACCESS_TOKEN] = user_input[CONF_ACCESS_TOKEN]
            if CONF_REFRESH_TOKEN in user_input:
                new_data[CONF_REFRESH_TOKEN] = user_input[CONF_REFRESH_TOKEN]
            if CONF_NOTIFICATION_DEFAULT in user_input:
                new_data[CONF_NOTIFICATION_DEFAULT] = user_input[
                    CONF_NOTIFICATION_DEFAULT
                ]
            if CONF_NOTIFICATION_WARNING in user_input:
                new_data[CONF_NOTIFICATION_WARNING] = user_input[
                    CONF_NOTIFICATION_WARNING
                ]
            if CONF_NOTIFICATION_DIAG in user_input:
                new_data[CONF_NOTIFICATION_DIAG] = user_input[CONF_NOTIFICATION_DIAG]

            self.hass.config_entries.async_update_entry(
                self._config_entry, data=new_data, options=new_options
            )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_options_schema(),
        )
