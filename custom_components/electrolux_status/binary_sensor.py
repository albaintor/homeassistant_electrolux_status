"""Binary sensor platform for Electrolux Status."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BINARY_SENSOR, DOMAIN
from .entity import ElectroluxEntity
from .util import get_capability, string_to_boolean

_LOGGER: logging.Logger = logging.getLogger(__package__)

FRIENDLY_NAMES = {
    "ovwater_tank_empty": "Water Tank Status",
    "foodProbeSupported": "Food Probe Support",
    "foodProbeInsertionState": "Food Probe",
    "ovcleaning_ended": "Cleaning Status",
    "ovfood_probe_end_of_cooking": "Probe End of Cooking",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [
                entity
                for entity in appliance.entities
                if entity.entity_type == BINARY_SENSOR
            ]
            _LOGGER.debug(
                "Electrolux add %d BINARY_SENSOR entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)


class ElectroluxBinarySensor(ElectroluxEntity, BinarySensorEntity):
    """Electrolux Status binary_sensor class."""

    @property
    def name(self) -> str:
        """Return the name of the binary sensor."""
        # Check for friendly name first using entity_key
        friendly_name = FRIENDLY_NAMES.get(self.entity_key)
        if friendly_name:
            return friendly_name
        # Fall back to catalog entry friendly name
        if self.catalog_entry and self.catalog_entry.friendly_name:
            return self.catalog_entry.friendly_name.capitalize()
        return self._name

    @property
    def entity_domain(self):
        """Entity domain for the entry. Used for consistent entity_id."""
        return BINARY_SENSOR

    @property
    def invert(self) -> bool:
        """Determine if the value returned for the entity needs to be reversed."""
        if self.catalog_entry:
            return self.catalog_entry.state_invert
        return False

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        value = self.extract_value()

        # Special handling for food probe insertion state
        if self.entity_key == "foodProbeInsertionState":
            live_value = self.reported_state.get("foodProbeInsertionState")
            if live_value is not None:
                # Show 'On' when inserted
                value = live_value == "INSERTED"
        # Special handling for cleaning and probe end sensors
        elif self.entity_key in ["ovcleaning_ended", "ovfood_probe_end_of_cooking"]:
            # Check processPhase - return On if STOPPED (process completed)
            process_phase = self.reported_state.get("processPhase")
            if process_phase == "STOPPED":
                value = True  # On when process has stopped/completed
            else:
                value = False  # Off otherwise

        if get_capability(self.capability, "access") == "constant":
            value = get_capability(self.capability, "default")
        if isinstance(value, str):
            value = string_to_boolean(value, True)
        if value is None:
            if self.catalog_entry and self.catalog_entry.state_mapping:
                mapping = self.catalog_entry.state_mapping
                value = self.get_state_attr(mapping)
        if value is not None:
            self._cached_value = value
        return bool(not self._cached_value if self.invert else self._cached_value)
