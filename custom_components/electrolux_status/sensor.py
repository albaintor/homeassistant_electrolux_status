"""Switch platform for Electrolux Status."""

import contextlib
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SENSOR
from .entity import ElectroluxEntity
from .util import create_notification

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [
                entity for entity in appliance.entities if entity.entity_type == SENSOR
            ]
            _LOGGER.debug(
                "Electrolux add %d SENSOR entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)


class ElectroluxSensor(ElectroluxEntity, SensorEntity):
    """Electrolux Status Sensor class."""

    @property
    def entity_domain(self):
        """Enitity domain for the entry. Used for consistent entity_id."""
        return SENSOR

    @property
    def suggested_display_precision(self) -> int | None:
        """Get the display precision."""
        if self.unit == UnitOfTemperature.CELSIUS:
            return 2
        if self.unit == UnitOfTemperature.FAHRENHEIT:
            return 2
        if self.unit == UnitOfVolume.LITERS:
            return 0
        if self.unit == UnitOfTime.SECONDS:
            return 0
        return None

    @property
    def native_value(self) -> str | int | float:
        """Return the state of the sensor."""
        value = self.extract_value()
        if self.capability.get("access") == "constant":
            value = self.capability.get("default")
        elif self.entity_attr == "alerts":
            value = len(value) if value is not None else 0
        elif value is not None and isinstance(self.unit, UnitOfTime):
            # Electrolux bug - prevent negative/disabled timers
            value = max(value, 0)
        if self.catalog_entry and self.catalog_entry.value_mapping:
            # Electrolux presents as string but returns an int
            # the mapping entry allows us to correctly display this to the frontend
            mapping = self.catalog_entry.value_mapping
            _LOGGER.debug("Mapping %s: %s to %s", self.json_path, value, mapping)
            if value in mapping:
                value = mapping.get(value, value)
        if isinstance(value, str):
            if "_" in value:
                value = value.replace("_", " ")
            value = value.title()
        if value is not None:
            self._cached_value = value
        else:
            value = self._cached_value
        return value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return unit of measurement."""
        # store the value of the sensor in the native format
        return self.unit

    @property
    def suggested_unit_of_measurement(self) -> str | None:
        """Return suggested unit of measurement."""
        # change the display unit in the HA frontend
        if self.unit == UnitOfTime.SECONDS:
            return UnitOfTime.MINUTES
        with contextlib.suppress(ValueError):
            if self._is_valid_suggested_unit(self.unit):
                return self.unit
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sensor."""
        if self.entity_attr == "alerts":
            alert_types = self.capability.get("values", {})
            # default is nullable - set a value for display to user
            alert_types = {key: "OFF" for key in alert_types}
            if current_alerts := self.extract_value():
                for alert in current_alerts:
                    severity = alert.get("severity", "Alert")
                    code = alert.get("code", "Unknown")
                    status = alert.get("acknowledgeStatus", "")
                    alert_types[code] = f"{severity}-{status}"
                    create_notification(
                        self.hass,
                        self.config_entry,
                        message=f"Alert: {code}</br>Severity: {severity}</br>Status: {status}",
                        title=self.name,
                    )
            return alert_types
