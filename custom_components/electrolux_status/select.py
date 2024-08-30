"""Select platform for Electrolux Status."""

import contextlib
import logging
from typing import Any

from pyelectroluxocp.oneAppApi import OneAppApi

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SELECT
from .entity import ElectroluxEntity
from .model import ElectroluxDevice

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure select platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [
                entity for entity in appliance.entities if entity.entity_type == SELECT
            ]
            _LOGGER.debug(
                "Electrolux add %d SELECT entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)


class ElectroluxSelect(ElectroluxEntity, SelectEntity):
    """Electrolux Status Select class."""

    def __init__(
        self,
        coordinator: Any,
        name: str,
        config_entry,
        pnc_id: str,
        entity_type: Platform,
        entity_attr,
        entity_source,
        capability: dict[str, Any],
        unit,
        device_class: str,
        entity_category: EntityCategory,
        icon: str,
        catalog_entry: ElectroluxDevice | None = None,
    ) -> None:
        """Initialize the Select entity."""
        super().__init__(
            coordinator=coordinator,
            capability=capability,
            name=name,
            config_entry=config_entry,
            pnc_id=pnc_id,
            entity_type=entity_type,
            entity_attr=entity_attr,
            entity_source=entity_source,
            unit=unit,
            device_class=device_class,
            entity_category=entity_category,
            icon=icon,
            catalog_entry=catalog_entry,
        )
        values_dict: dict[str, Any] | None = self.capability.get("values", None)
        self.options_list: dict[str, str] = {}
        for value in values_dict:
            entry: dict[str, Any] = values_dict[value]
            if "disabled" in entry:
                continue

            label = self.format_label(value)
            self.options_list[label] = value

    @property
    def entity_domain(self):
        """Enitity domain for the entry. Used for consistent entity_id."""
        return SELECT

    def format_label(self, value: str | None) -> str | None:
        """Convert input to label string value."""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("_", " ").title()
        if self.unit == UnitOfTemperature.CELSIUS:
            value = f"{value} °C"
        elif self.unit == UnitOfTemperature.FAHRENHEIT:
            value = f"{value} °F"
        return str(value)

    # @property
    # def icon(self) -> str:
    #     """Return a representative icon."""
    #     if not self.available or self.current_option == "TODO":
    #         return "mdi:XXX"
    #     return "mdi:YYY"

    @property
    def current_option(self) -> str:
        """Return the current option."""
        value = self.extract_value()

        if value is None:
            return self._cached_value

        if self.catalog_entry and self.catalog_entry.value_mapping:
            mapping = self.catalog_entry.value_mapping
            _LOGGER.debug("Mapping %s: %s to %s", self.json_path, value, mapping)
            if value in mapping:
                value = mapping.get(value, value)

        label = None
        try:
            label = list(self.options_list.keys())[
                list(self.options_list.values()).index(value)
            ]
        except Exception as ex:  # noqa: BLE001
            _LOGGER.info(
                "Electrolux error value %s does not exist in the list %s. %s",
                value,
                self.options_list.values(),
                ex,
            )
        # When value not in the catalog -> add the value to the list then
        if label is None:
            label = self.format_label(value)
            self.options_list[label] = value
        if label is not None:
            self._cached_value = label
        else:
            label = self._cached_value
        return label

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        value = self.options_list.get(option, None)
        if isinstance(self.unit, UnitOfTemperature) or self.entity_attr.startswith(
            "targetTemperature"
        ):
            # Attempt to convert the option to a float
            with contextlib.suppress(ValueError):
                value = float(value)

        if value is None:
            return

        client: OneAppApi = self.api
        command: dict[str, Any] = {}
        if self.entity_source:
            command = {self.entity_source: {self.entity_attr: value}}
        else:
            command = {self.entity_attr: value}

        _LOGGER.debug("Electrolux select option %s", command)
        result = await client.execute_appliance_command(self.pnc_id, command)
        _LOGGER.debug("Electrolux select option result %s", result)

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return list(self.options_list.keys())
