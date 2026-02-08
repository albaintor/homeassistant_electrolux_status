"""Switch platform for Electrolux Status."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SWITCH
from .entity import ElectroluxEntity
from .util import (
    AuthenticationError,
    ElectroluxApiClient,
    format_command_for_appliance,
    map_command_error_to_home_assistant_error,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [
                entity for entity in appliance.entities if entity.entity_type == SWITCH
            ]
            _LOGGER.debug(
                "Electrolux add %d SENSOR entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)


class ElectroluxSwitch(ElectroluxEntity, SwitchEntity):
    """Electrolux Status switch class."""

    @property
    def entity_domain(self):
        """Entity domain for the entry. Used for consistent entity_id."""
        return SWITCH

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        value = self.extract_value()

        if value is None:
            if self.catalog_entry and self.catalog_entry.state_mapping:
                mapping = self.catalog_entry.state_mapping
                value = self.get_state_attr(mapping)

        if value is None:
            return self._cached_value if self._cached_value is not None else False
        # Ensure value is boolean
        if isinstance(value, bool):
            self._cached_value = value
            return value
        else:
            # If it's not a boolean, try to convert it
            bool_value = bool(value)
            self._cached_value = bool_value
            return bool_value

    async def switch(self, value: bool) -> None:
        """Control switch state."""
        # Check if remote control is enabled before sending command
        if not self.is_remote_control_enabled():
            _LOGGER.warning(
                "Remote control is disabled for appliance %s, cannot execute command for %s",
                self.pnc_id,
                self.entity_attr,
            )
            raise HomeAssistantError(
                "Remote control is disabled for this appliance. Please check the appliance settings."
            )

        client: ElectroluxApiClient = self.api
        # Use dynamic capability-based value formatting
        command_value = format_command_for_appliance(
            self.capability, self.entity_attr, value
        )

        command: dict[str, Any]
        if self.entity_source:
            if self.entity_source == "userSelections":
                # Safer access to avoid KeyError if userSelections is missing
                reported = self.appliance_status.get("properties", {}).get(
                    "reported", {}
                )
                program_uid = reported.get("userSelections", {}).get("programUID")
                command = {
                    self.entity_source: {
                        "programUID": program_uid,
                        self.entity_attr: command_value,
                    },
                }
            else:
                command = {self.entity_source: {self.entity_attr: command_value}}
        else:
            command = {self.entity_attr: command_value}
        _LOGGER.debug("Electrolux set value")
        try:
            await client.execute_appliance_command(self.pnc_id, command)
        except AuthenticationError as auth_ex:
            # Handle authentication errors by triggering reauthentication
            await self.coordinator.handle_authentication_error(auth_ex)
        except Exception as ex:
            # Use shared error mapping for all errors
            raise map_command_error_to_home_assistant_error(
                ex, self.entity_attr, _LOGGER, self.capability
            ) from ex
        _LOGGER.debug("Electrolux set value completed")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.switch(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.switch(False)
