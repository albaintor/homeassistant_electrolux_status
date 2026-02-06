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
from .util import ElectroluxApiClient, string_to_boolean

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
        """Enitity domain for the entry. Used for consistent entity_id."""
        return SWITCH

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        value = self.extract_value()

        if value is None:
            if self.catalog_entry and self.catalog_entry.state_mapping:
                mapping = self.catalog_entry.state_mapping
                value = self.get_state_attr(mapping)
        # Electrolux returns strings for some true/false states
        if value is not None and isinstance(value, str):
            value = string_to_boolean(value, False)

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
        # Check if remote control is enabled
        remote_control = (
            self.appliance_status.get("properties", {})
            .get("reported", {})
            .get("remoteControl")
        )
        if remote_control not in ["ENABLED", "NOT_SAFETY_RELEVANT_ENABLED"]:
            _LOGGER.warning(
                "Cannot control %s for appliance %s: remote control is %s",
                self.entity_attr,
                self.pnc_id,
                remote_control,
            )
            raise HomeAssistantError(
                f"Remote control disabled (status: {remote_control})"
            )

        client: ElectroluxApiClient = self.api
        # Electrolux bug - needs string not bool
        command_value = "ON" if value else "OFF"
        if "values" in self.capability:
            command_value = "ON" if value else "OFF"

        command: dict[str, Any]
        if self.entity_source:
            if self.entity_source == "userSelections":
                command = {
                    self.entity_source: {
                        "programUID": self.appliance_status["properties"]["reported"][
                            "userSelections"
                        ]["programUID"],
                        self.entity_attr: command_value,
                    },
                }
            else:
                command = {self.entity_source: {self.entity_attr: command_value}}
        else:
            command = {self.entity_attr: command_value}
        _LOGGER.debug("Electrolux set value %s", command_value)
        try:
            result = await client.execute_appliance_command(self.pnc_id, command)
        except Exception as ex:
            error_msg = str(ex).lower()
            if "disconnected" in error_msg or "command_validation_error" in error_msg:
                raise HomeAssistantError("Appliance is disconnected or not available")
            raise
        _LOGGER.debug("Electrolux set value result %s", result)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.switch(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.switch(False)
