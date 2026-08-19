"""Entity platform for Electrolux Status."""

import logging
import re
from typing import Any, cast

from pyelectroluxocp import OneAppApi
from pyelectroluxocp.apiModels import ApplienceStatusResponse

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .model import ElectroluxDevice

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure entity platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [entity for entity in appliance.entities if entity.entity_type == "entity"]
            _LOGGER.debug(
                "Electrolux add %d entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)


class ElectroluxEntity(CoordinatorEntity):
    """Class for Electrolux devices."""

    _attr_has_entity_name = True

    appliance_status: ApplienceStatusResponse

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
        unit: str,
        device_class: str,
        entity_category: EntityCategory,
        icon: str,
        catalog_entry: ElectroluxDevice | None = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.root_attribute = ["properties", "reported"]
        self.data = None
        self.coordinator = coordinator
        self._cached_value = None
        self._name = name
        self._icon = icon
        self._device_class = device_class
        self._entity_category = entity_category
        self._catalog_entry = catalog_entry
        self.api: OneAppApi = coordinator.api
        self.entity_name = entity_name
        self.entity_attr = entity_attr
        self.entity_type = entity_type
        self.entity_source = entity_source
        self.config_entry = config_entry
        self.pnc_id = pnc_id
        self.unit = unit
        self.capability = capability
        _raw_entity_id = (
            f"{self.entity_domain}."
            f"{self.get_appliance.brand}_{self.get_appliance.name}_"
            f"{self.entity_source}_{self.entity_attr}"
        )
        # HA entity IDs must be lowercase [a-z0-9_.] with no consecutive underscores.
        # The appliance brand/name/attr values may contain uppercase, camelCase, spaces,
        # and hyphens. entity_source can also be empty, causing double underscores.
        _domain, _object = _raw_entity_id.split(".", 1)
        _object = re.sub(r"[^a-z0-9_]", "_", _object.lower())  # lowercase + replace invalid chars
        _object = re.sub(r"_+", "_", _object).strip("_")        # collapse consecutive underscores
        self.entity_id = f"{_domain}.{_object}"
        if catalog_entry:
            self.entity_registry_enabled_default = catalog_entry.entity_registry_enabled_default
        _LOGGER.debug("Electrolux new entity %s for appliance %s", name, pnc_id)

    def setup(self, data):
        """Initialiaze setup."""
        self.data = data

    @property
    def entity_domain(self) -> str:
        """Entity domain for the entry."""
        return "sensor"

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}-{self.entity_attr}-{self.entity_source or 'root'}-{self.pnc_id}"

    # Disabled this as this removes the value from display : there is no readonly property for entities
    # @property
    # def available(self) -> bool:
    #     if (self._entity_category == EntityCategory.DIAGNOSTIC
    #             or self.entity_attr in ALWAYS_ENABLED_ATTRIBUTES):
    #         return True
    #     connection_state = self.get_connection_state()
    #     if connection_state and connection_state != "disconnected":
    #         return True
    #     return False

    @property
    def should_poll(self) -> bool:
        """Confirm if device should be polled."""
        return False

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # _LOGGER.debug("Electrolux entity got data %s", self.coordinator.data)
        if self.coordinator.data is None:
            return
        appliances = self.coordinator.data.get("appliances", None)
        self.appliance_status = appliances.get_appliance(self.pnc_id).state
        self.async_write_ha_state()

    def get_connection_state(self) -> str | None:
        """Return connection state."""
        if self.appliance_status:
            return self.appliance_status.get("connectionState", None)
        return None

    def get_state_attr(self, path: str) -> str | None:
        """Return value of other appliance attributes.

        Used for the evaluation of state_mapping one property to another.
        """
        if "/" in path:
            if self.reported_state.get(path, None):
                return self.reported_state.get(path)
            source, attr = path.split("/")
            return self.reported_state.get(source, {}).get(attr, None)
        return self.reported_state.get(path, None)

    @property
    def reported_state(self):
        """Return reported state of the appliance."""
        return self.appliance_status.get("properties", {}).get("reported", {})

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if self.catalog_entry and self.catalog_entry.friendly_name:
            return self.catalog_entry.friendly_name.capitalize()
        return self._name

    @property
    def icon(self) -> str | None:
        """Return the icon of the entity."""
        return self._icon

    # @property
    # def get_entity(self) -> ApplianceEntity:
    #     return self.get_appliance.get_entity(self.entity_type, self.entity_attr, self.entity_source, None)

    @property
    def get_appliance(self):
        """Return the appliance device."""
        return self.coordinator.data["appliances"].get_appliance(self.pnc_id)

    @property
    def device_info(self):
        """Return identifiers of the device."""
        return {
            "identifiers": {(DOMAIN, self.pnc_id)},
            "name": self.get_appliance.name,
            "model": self.get_appliance.model,
            "manufacturer": self.get_appliance.brand,
        }

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return entity category."""
        return self._entity_category

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return self._device_class

    def extract_value(self):
        """Return the appliance attributes of the entity."""
        root_attribute = self.root_attribute
        attribute = self.entity_attr
        if self.appliance_status:
            root = cast(any, self.appliance_status)
            # Format returned by push is slightly different from format returned by API : fields are at root level
            # Let's check if we can find the fields at root first
            if (self.entity_source and root.get(self.entity_source, None) is not None) or root.get(attribute, None):
                root_attribute = None
            if root_attribute:
                for item in root_attribute:
                    if root:
                        root = root.get(item, None)
            if root:
                if self.entity_source:
                    category: dict[str, Any] | None = root.get(self.entity_source, None)
                    if category:
                        return category.get(attribute)
                else:
                    return root.get(attribute, None)
        return None

    def apply_value_mapping(self, value: Any) -> Any:
        """Translate a raw value through the catalog's value_mapping.

        Some capabilities are described with string values but reported as
        integers; the mapping converts them back. Shared by every platform that
        displays a catalog-mapped value.
        """
        if value is None or not self.catalog_entry or not self.catalog_entry.value_mapping:
            return value
        mapping = self.catalog_entry.value_mapping
        if value in mapping:
            _LOGGER.debug("Mapping %s: %s to %s", self.json_path, value, mapping)
            return mapping.get(value, value)
        return value

    def update(self, appliance_status: ApplienceStatusResponse):
        """Update the appliance status."""
        self.appliance_status = appliance_status
        # if self.hass:
        #     self.async_write_ha_state()

    @property
    def json_path(self) -> str | None:
        """Return the path to the entry."""
        if self.entity_source:
            return f"{self.entity_source}/{self.entity_attr}"
        return self.entity_attr

    @property
    def catalog_entry(self) -> ElectroluxDevice | None:
        """Return matched catalog entry."""
        return self._catalog_entry

    # @property
    # def extra_state_attributes(self) -> dict[str, Any]:
    #     """Return the state attributes of the sensor."""
    #     return {
    #         "Path": self.json_path,
    #         "entity_type": str(self.entity_type),
    #         "entity_category": str(self.entity_category),
    #         "device_class": str(self.device_class),
    #         "capability": str(self.capability),
    #     }
