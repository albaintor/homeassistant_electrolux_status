"""Adds config flow for Electrolux Status."""
import logging

import homeassistant.helpers.config_validation as cv
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import selector
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from typing import Mapping, Any

from .pyelectroluxconnect_util import pyelectroluxconnect_util
from .const import CONF_PASSWORD, CONF_RENEW_INTERVAL, DEFAULT_WEBSOCKET_RENEWAL_DELAY
from .const import CONF_LANGUAGE, DEFAULT_LANGUAGE
from .const import CONF_USERNAME
from .const import DOMAIN
from .const import languages

_LOGGER = logging.getLogger(__name__)


class ElectroluxStatusFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Electrolux Status."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            else:
                self._errors["base"] = "auth"

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """Handle configuration by re-auth."""
        return await self.async_step_reauth_validate(entry_data)

    async def async_step_reauth_validate(self, user_input=None):
        """Handle reauth and validation."""
        self._errors = {}
        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD]
            )
            if valid:
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME], data=user_input
                )
            else:
                self._errors["base"] = "auth"
            return await self._show_config_form(user_input)
        return await self._show_config_form(user_input)

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     return ElectroluxStatusOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        data_schema = {
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_LANGUAGE, default = DEFAULT_LANGUAGE): selector({
                "select": {
                    "options": list(languages.keys()),
                    "mode": "dropdown"}
            }),
        }
        if self.show_advanced_options:
            data_schema = {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_LANGUAGE, default = DEFAULT_LANGUAGE): selector({
                    "select": {
                        "options": list(languages.keys()),
                        "mode": "dropdown"}
                }),
            }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _test_credentials(self, username, password):
        """Return true if credentials is valid."""
        try:
            client = pyelectroluxconnect_util.get_session(username, password, _LOGGER)
            await self.hass.async_add_executor_job(client.get_appliances_list)
            return True
        except Exception as inst:  # pylint: disable=broad-except
            _LOGGER.exception(inst)
        return False


class ElectroluxStatusOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for Electrolux Status."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_RENEW_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_RENEW_INTERVAL, DEFAULT_WEBSOCKET_RENEWAL_DELAY
                        ),
                    ): cv.positive_int,
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )
