"""Select platform for Electrolux Status."""

import contextlib
import logging
from typing import Any

from pyelectroluxocp.oneAppApi import OneAppApi

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
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
            entities = [entity for entity in appliance.entities if entity.entity_type == SELECT]
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
        entity_name,
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
            entity_name=entity_name,
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
        # Values the appliance can report but refuses to be set to. They are
        # kept out of the selectable options while still being displayable,
        # e.g. a hob hood reports hobToHoodState AUTO_SUSPEND but marks it
        # disabled in its capability document.
        self.readonly_options: set[str] = set()
        # Reverse index, so resolving the reported value to its label is a dict
        # lookup rather than a scan of every option on each state write.
        self.label_by_value: dict[Any, str] = {}
        for value in values_dict:
            entry: dict[str, Any] = values_dict[value]
            label = self.format_label(value)
            self.options_list[label] = value
            self.label_by_value[value] = label
            if "disabled" in entry:
                self.readonly_options.add(label)

    @property
    def entity_domain(self):
        """Entity domain for the entry. Used for consistent entity_id."""
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

    def reported_value(self) -> Any:
        """Return the reported value with any catalog mapping applied.

        Shared by current_option and options so the two cannot disagree about
        which option the appliance is currently reporting.
        """
        return self.apply_value_mapping(self.extract_value())

    @property
    def current_option(self) -> str:
        """Return the current option."""
        value = self.reported_value()

        if value is None:
            return self._cached_value

        label = self.label_by_value.get(value)
        # Electrolux capability documents omit values that appliances really
        # do report, which is why this fallback exists. Learn the value and
        # leave it selectable - only values the document explicitly flags as
        # disabled are withheld.
        if label is None:
            _LOGGER.info(
                "Electrolux %s reported %s, which its capabilities do not list; adding it",
                self.json_path,
                value,
            )
            label = self.format_label(value)
            self.options_list[label] = value
            self.label_by_value[value] = label
        self._cached_value = label
        return label

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option in self.readonly_options:
            # Reachable from a script: the value is in options while the
            # appliance reports it, so HA's own validation lets it through.
            raise ServiceValidationError(
                f"{self.name} cannot be set to {option}: the appliance reports that value as disabled"
            )
        value = self.options_list.get(option, None)
        if (
            isinstance(self.unit, UnitOfTemperature)
            or self.entity_attr.startswith("targetTemperature")
            or self.entity_name.startswith("targetTemperature")
        ):
            # Attempt to convert the option to a float
            with contextlib.suppress(ValueError):
                value = float(value)

        if value is None:
            return

        _LOGGER.debug(
            "Electrolux select option before reported status %s", self.appliance_status["properties"]["reported"]
        )

        client: OneAppApi = self.api
        command: dict[str, Any] = {}
        if self.entity_source:
            if self.entity_source == "userSelections":
                command = {
                    self.entity_source: {
                        "programUID": self.appliance_status["properties"]["reported"]["userSelections"]["programUID"],
                        self.entity_attr: value,
                    },
                }
            else:
                command = {self.entity_source: {self.entity_attr: value}}
        else:
            command = {self.entity_attr: value}

        _LOGGER.debug("Electrolux select option %s", command)
        result = await client.execute_appliance_command(self.pnc_id, command)
        _LOGGER.debug("Electrolux select option result %s", result)

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options.

        Values the capability document marks as disabled are not offered.

        Home Assistant renders no state at all for a select whose current
        option is absent from this list, so a disabled value is kept in the
        list while the appliance is actually reporting it - otherwise a hob
        sitting in AUTO_SUSPEND would show as "unknown". Sending it is still
        refused by async_select_option, so it can be seen but never chosen.
        """
        if not self.readonly_options:
            return list(self.options_list)
        # Compare against current_option rather than the reported value, so the
        # two cannot disagree. current_option falls back to the last known
        # label when a payload omits the attribute, and a disabled value has to
        # survive that fallback too - otherwise the entity renders as unknown
        # the first time an update arrives without it.
        current = self.current_option
        return [label for label in self.options_list if label not in self.readonly_options or label == current]
