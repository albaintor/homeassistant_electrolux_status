"""Binary sensor platform for Electrolux Status."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BINARY_SENSOR, DOMAIN
from .entity import ElectroluxEntity
from .util import string_to_boolean

_LOGGER: logging.Logger = logging.getLogger(__package__)


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
    def entity_domain(self):
        """Enitity domain for the entry. Used for consistent entity_id."""
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
        if isinstance(value, str):
            value = string_to_boolean(value, True)
        if value is not None:
            self._cached_value = value
        return not self._cached_value if self.invert else self._cached_value
