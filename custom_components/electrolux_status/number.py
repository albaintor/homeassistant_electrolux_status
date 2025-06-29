"""Number platform for Electrolux Status."""

import logging

from pyelectroluxocp import OneAppApi

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NUMBER
from .entity import ElectroluxEntity
from .util import time_minutes_to_seconds, time_seconds_to_minutes

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [
                entity for entity in appliance.entities if entity.entity_type == NUMBER
            ]
            _LOGGER.debug(
                "Electrolux add %d NUMBER entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)


class ElectroluxNumber(ElectroluxEntity, NumberEntity):
    """Electrolux Status number class."""

    @property
    def entity_domain(self):
        """Enitity domain for the entry. Used for consistent entity_id."""
        return NUMBER

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        if self.unit == UnitOfTime.SECONDS:
            value = time_seconds_to_minutes(self.extract_value())
        else:
            value = self.extract_value()

        if not value:
            value = self.capability.get("default", None)
            if value == "INVALID_OR_NOT_SET_TIME":
                value = self.capability.get("min", None)
        if not value:
            return self._cached_value
        if isinstance(self.unit, UnitOfTemperature):
            value = round(value, 2)
        elif isinstance(self.unit, UnitOfTime):
            # Electrolux bug - prevent negative/disabled timers
            value = max(value, 0)
        self._cached_value = value
        return value

    @property
    def native_max_value(self) -> float:
        """Return the max value."""
        if self.unit == UnitOfTime.SECONDS:
            return time_seconds_to_minutes(self.capability.get("max", 100))
        if self.unit == UnitOfTemperature.CELSIUS:
            return self.capability.get("max", 300)
        return self.capability.get("max", 100)

    @property
    def native_min_value(self) -> float:
        """Return the max value."""
        if self.unit == UnitOfTime.SECONDS:
            return time_seconds_to_minutes(self.capability.get("min", 0))
        return self.capability.get("min", 0)

    @property
    def native_step(self) -> float:
        """Return the max value."""
        if self.unit == UnitOfTime.SECONDS:
            return time_seconds_to_minutes(self.capability.get("step", 1))
        if self.unit == UnitOfTemperature.CELSIUS:
            return self.capability.get("max", 5)
        return self.capability.get("step", 1)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if self.unit == UnitOfTime.SECONDS:
            value = time_minutes_to_seconds(value)
        if self.capability.get("step", 1) == 1:
            value = int(value)
        client: OneAppApi = self.api
        
        # --- START OF OUR FIX ---
        command = {}
        if self.entity_source == "latamUserSelections":
            _LOGGER.debug("Electrolux: Detected latamUserSelections, building full command.")
            # Get the current state of all latam selections
            current_selections = self.appliance_status.get("properties", {}).get("reported", {}).get("latamUserSelections", {})
            if not current_selections:
                _LOGGER.error("Could not retrieve current latamUserSelections to build command.")
                return

            # Create a copy to modify
            new_selections = current_selections.copy()
            # Update only the value we want to change
            new_selections[self.entity_attr] = value
            # Assemble the final command with the entire block
            command = {"latamUserSelections": new_selections}
        # --- END OF OUR FIX ---

        # Original logic as a fallback for other entities
        elif self.entity_source == "userSelections":
            command = {
                self.entity_source: {
                    "programUID": self.appliance_status["properties"]['reported']["userSelections"]['programUID'],
                    self.entity_attr: value
                },
            }
        elif self.entity_source:
            command = {self.entity_source: {self.entity_attr: value}}
        else:
            command = {self.entity_attr: value}

        _LOGGER.debug("Electrolux set value %s", command)
        result = await client.execute_appliance_command(self.pnc_id, command)
        _LOGGER.debug("Electrolux set value result %s", result)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self.unit == UnitOfTime.SECONDS:
            return UnitOfTime.MINUTES
        return self.unit
