"""API for Electrolux Status."""

from dataclasses import replace
import logging
import re
from typing import Any

from pyelectroluxocp.apiModels import ApplianceInfoResponse, ApplienceStatusResponse

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.button import ButtonDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import Platform, UnitOfTemperature

from .binary_sensor import ElectroluxBinarySensor
from .button import ElectroluxButton
from .catalog_core import CATALOG_APPLIANCE_TYPE, CATALOG_BASE, CATALOG_MODEL
from .const import (
    ATTRIBUTES_BLACKLIST,
    ATTRIBUTES_WHITELIST,
    BINARY_SENSOR,
    BUTTON,
    NUMBER,
    PLATFORMS,
    RENAME_RULES,
    SELECT,
    SENSOR,
    STATIC_ATTRIBUTES,
    SWITCH,
)
from .entity import ElectroluxEntity
from .model import ElectroluxDevice
from .number import ElectroluxNumber
from .select import ElectroluxSelect
from .sensor import ElectroluxSensor
from .switch import ElectroluxSwitch

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


def deep_merge_dicts(dict1, dict2):
    """Recursively merge two dictionaries."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


# Matches the numeric suffix of a capability container, e.g. the "1" of
# "hobZone1/runningTime". Appliances that report a variable number of identical
# containers (hob zones, heating modules) can then be described once in a
# catalog as "hobZone*/runningTime" instead of per index.
CONTAINER_INDEX_RE = re.compile(r"^([A-Za-z]+?)(\d+)/")

# Catalog keys using the wildcard above are patterns, never real capabilities.
CATALOG_WILDCARD = "*"


def catalog_wildcard_key(capability: str) -> tuple[str, str] | None:
    """Return the wildcard form of a nested capability path and its index.

    "hobZone12/runningTime" -> ("hobZone*/runningTime", "12")
    "userSelections/analogTemperature" -> None (no numeric container suffix)
    """
    match = CONTAINER_INDEX_RE.match(capability)
    if not match:
        return None
    container, index = match.groups()
    return f"{container}{CATALOG_WILDCARD}/{capability[match.end() :]}", index


def is_catalog_pattern(key: str) -> bool:
    """Return whether a catalog key is a pattern rather than a capability."""
    return CATALOG_WILDCARD in key


class ElectroluxLibraryEntity:
    """Electrolux Library Entity."""

    def __init__(
        self,
        name,
        status: str,
        state: ApplienceStatusResponse,
        appliance_info: ApplianceInfoResponse,
        capabilities: dict[str, Any],
    ) -> None:
        """Initialize the entity."""
        self.name = name
        self.status = status
        self.state = state
        self.appliance_info = appliance_info
        self.capabilities = capabilities

    @property
    def reported_state(self) -> dict[str, Any]:
        """Return the reported state of the appliance."""
        return self.state.get("properties", {}).get("reported")

    def get_name(self):
        """Get entity name."""
        return self.name

    def get_value(self, attr_name) -> Any:
        """Return value by attribute."""
        if "/" in attr_name:
            source, attr = attr_name.split("/")
            return self.reported_state.get(source, {}).get(attr, None)
        return self.reported_state.get(attr_name, None)

    def get_sensor_name(self, attr_name: str) -> str:
        """Get the name of the sensor."""
        sensor = attr_name
        for truncate_rule in RENAME_RULES:
            sensor = re.sub(truncate_rule, "", sensor)
        sensor = sensor[0].upper() + sensor[1:]
        sensor = sensor.replace("_", " ")
        sensor = sensor.replace("/", " ")
        group = ""
        words = []
        for i, char in enumerate(sensor):
            if group == "":
                group = char
            else:
                if char == " " and len(group) > 0:
                    words.append(group)
                    group = ""
                    continue

                if (
                    (char.isupper() or char.isdigit())
                    and (sensor[i - 1].isupper() or sensor[i - 1].isdigit())
                    and ((i == len(sensor) - 1) or (sensor[i + 1].isupper() or sensor[i + 1].isdigit()))
                ):
                    group += char
                elif (char.isupper() or char.isdigit()) and sensor[i - 1].islower():
                    if re.match("^[A-Z0-9]+$", group):
                        words.append(group)
                    else:
                        words.append(group.lower())
                    group = char
                else:
                    group += char
        if len(group) > 0:
            if re.match("^[A-Z0-9]+$", group):
                words.append(group)
            else:
                words.append(group.lower())
        return " ".join(words).lower().capitalize()

    # def get_sensor_name_old(self, attr_name: str, container: str | None = None):
    #     """Convert sensor format.

    #     ex: "fCMiscellaneousState/detergentExtradosage" to "Detergent extradosage".
    #     """
    #     attr_name = attr_name.rpartition("/")[-1] or attr_name
    #     attr_name = attr_name[0].upper() + attr_name[1:]
    #     attr_name = " ".join(re.findall("[A-Z][^A-Z]*", attr_name))
    #     return attr_name.capitalize()

    def get_entity_name(self, attr_name: str) -> str:
        """Extract Entity Name.

        ex: Convert format "fCMiscellaneousState/EWX1493A_detergentExtradosage" to "XdetergentExtradosage"
        """
        for truncate_rule in RENAME_RULES:
            attr_name = re.sub(truncate_rule, "", attr_name)

        return attr_name.rpartition("/")[-1] or attr_name

    def get_entity_attr(self, attr_name: str) -> str:
        """Extract Entity attr in raw format.

        ex: Convert format "fCMiscellaneousState/EWX1493A_detergentExtradosage" to "EWX1493A_detergentExtradosage"
        """
        return attr_name.rpartition("/")[-1] or attr_name

    def get_category(self, attr_name: str) -> str:
        """Extract category.

        ex: "fCMiscellaneousState/detergentExtradosage" to "fCMiscellaneousState".
        or "" if none
        """
        return attr_name.rpartition("/")[0]

    def get_capability(self, attr_name: str) -> dict[str, Any] | None:
        """Retrieve the capability from self.capabilities using the attribute name.

        May contain slashes for nested keys.
        """
        if self.capabilities.get(attr_name, None):
            return self.capabilities.get(attr_name)

        keys = attr_name.split("/")
        result = self.capabilities

        for key in keys:
            result = result.get(key)
            if result is None:
                return None

        return result

    def get_entity_unit(self, attr_name: str):
        """Get entity unit type."""
        capability_def: dict[str, Any] | None = self.get_capability(attr_name)
        if not capability_def:
            return None
        # Type : string, int, number, boolean (other values ignored)
        type_units = capability_def.get("type", None)
        if not type_units:
            return None
        if type_units == "temperature":
            return UnitOfTemperature.CELSIUS
        return None

    def get_entity_device_class(self, attr_name: str):
        """Get entity device class."""
        capability_def: dict[str, Any] | None = self.get_capability(attr_name)
        if not capability_def:
            return None
        # Type : string, int, number, boolean (other values ignored)
        type_class = capability_def.get("type", None)
        if not type_class:
            return None
        if type_class == "temperature":
            if capability_def.get("access", None) == "readwrite":
                return NumberDeviceClass.TEMPERATURE
            return SensorDeviceClass.TEMPERATURE
        return None

    def get_entity_type(self, attr_name: str) -> Platform | None:
        """Get entity type."""

        capability_def: dict[str, Any] | None = self.get_capability(attr_name)
        if not capability_def:
            return None

        # Type : string, int, number, boolean (other values ignored)
        type_object = capability_def.get("type", None)
        if not type_object:
            return None

        # Access : read, readwrite (other values ignored)
        access = capability_def.get("access", None)
        if not access:
            return None

        # Exception (Electrolux bug)
        if type_object == "boolean" and access == "readwrite" and capability_def.get("values", None) is not None:
            return SWITCH

        # List of values ? if values is defined and has at least 1 entry
        values: dict[str, Any] | None = capability_def.get("values", None)
        if values and access == "readwrite" and isinstance(values, dict) and len(values) > 0:
            if type_object == "string":
                upper_values = {str(k).upper() for k in values}
                if upper_values == {"ON", "OFF"}:
                    return SWITCH
            if type_object not in ["number", "temperature"] or capability_def.get("min", None) is None:
                return SELECT

        match type_object:
            case "boolean":
                if access == "read":
                    return BINARY_SENSOR
                if access == "readwrite":
                    return SWITCH
            case "temperature":
                if access == "read":
                    return SENSOR
                if access == "readwrite":
                    return NUMBER
            case "alert":
                return SENSOR
            case _:
                if (
                    self.get_entity_name(attr_name) == "executeCommand" and access == "read"
                ):  # FIX for https://github.com/albaintor/homeassistant_electrolux_status/issues/74
                    return BUTTON
                if access == "write":
                    return BUTTON
                if access == "constant":
                    return SENSOR
                if access == "read" and type_object in [
                    "number",
                    "int",
                    "boolean",
                    "string",
                ]:
                    return SENSOR
                if type_object in ("int", "number"):
                    return NUMBER
        _LOGGER.debug(
            "Electrolux unable to determine type for %s. Type: %s Access: %s",
            attr_name,
            type_object,
            access,
        )
        return None

    def sources_list(self) -> list[str] | None:
        """List the capability types."""
        if self.capabilities is None:
            _LOGGER.warning("Electrolux capabilities list is empty")
            return None

        # dont load these entities by as they are not useful
        # we do load some of these directly via STATIC_ATTRIBUTES as
        # one or another are useful, but not all child values are

        def keep_source(source: str) -> bool:
            for ignored_pattern in ATTRIBUTES_BLACKLIST:
                if re.match(ignored_pattern, source):
                    for whitelist_pattern in ATTRIBUTES_WHITELIST:
                        if re.match(whitelist_pattern, source):
                            return True
                    _LOGGER.debug("Exclude source %s from list", source)
                    return False
            return True

        sources = [key for key in list(self.capabilities.keys()) if keep_source(key)]

        for key, value in self.capabilities.items():
            if not keep_source(key):
                continue

            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict) and "access" in sub_value and "type" in sub_value:
                        sources.append(f"{key}/{sub_key}")
            elif "access" in value and "type" in value:
                sources.append(key)

        return sources

    # def sources_list_old(self):
    #     _LOGGER.warning(self.capabilities)
    #     return [
    #         key
    #         for key in list(self.capabilities.keys())
    #         if not key.startswith("applianceCareAndMaintenance")
    #     ]


class Appliance:
    """Define the Appliance Class."""

    brand: str
    device: str
    entities: list[ElectroluxEntity]
    coordinator: Any

    def __init__(
        self,
        coordinator: Any,
        name: str,
        pnc_id: str,
        brand: str,
        model: str,
        state: ApplienceStatusResponse,
    ) -> None:
        """Initiate the appliance."""
        self.own_capabilties = False
        self.data = None
        self._catalog: dict[str, ElectroluxDevice] | None = None
        self.coordinator = coordinator
        self.model = model
        self.pnc_id = pnc_id
        self.name = name
        self.brand = brand
        self.state: ApplienceStatusResponse = state

    @property
    def reported_state(self) -> dict[str, Any]:
        """Return the reported state of the appliance."""
        return self.state.get("properties", {}).get("reported", {})

    @property
    def appliance_type(self) -> dict[str, Any]:
        """Return the reported type of the appliance.

        CR: Refridgerator
        WM: Washing Machine
        """
        return self.reported_state.get("applianceInfo", {}).get("applianceType") or self.state.get(
            "applianceData", {}
        ).get("modelName")

    @property
    def catalog(self) -> dict[str, ElectroluxDevice]:
        """Return the defined catalog for the appliance.

        Applied from most generic to most specific, so the base catalog is
        overridden by the reported appliance type, which is in turn overridden
        by the exact model. Prefer adding to the appliance-type catalog: it
        covers every model of that type.
        """
        # Cached for the appliance's lifetime. The appliance type does not
        # change, and caching also means a later state push that happens to
        # omit applianceInfo cannot silently switch the catalog out from
        # under entities that were already built from it.
        if self._catalog is None:
            overrides = [
                override
                for override in (
                    CATALOG_APPLIANCE_TYPE.get(self.appliance_type),
                    CATALOG_MODEL.get(self.model),
                )
                if override
            ]
            if not overrides:
                self._catalog = CATALOG_BASE
            else:
                _LOGGER.debug(
                    "Extending catalog for appliance type %s / model %s",
                    self.appliance_type,
                    self.model,
                )
                # Shallow copy: overrides replace whole entries, they never
                # mutate one, so the base entries can safely be shared.
                self._catalog = dict(CATALOG_BASE)
                for override in overrides:
                    self._catalog.update(override)

        return self._catalog

    def get_catalog_entry(self, capability: str) -> ElectroluxDevice | None:
        """Return the catalog entry describing a capability path.

        Falls back to the wildcard form of the path so a catalog can describe
        repeated containers without assuming how many of them an appliance
        reports, or that they are numbered contiguously.
        """
        catalog = self.catalog
        if entry := catalog.get(capability):
            return entry
        if not (wildcard := catalog_wildcard_key(capability)):
            return None
        key, index = wildcard
        if not (entry := catalog.get(key)):
            return None
        # A wildcard entry describes every container of its kind, so its name
        # has to carry the index or every zone ends up with the same name. If
        # an entry forgets the placeholder, drop back to the generated name -
        # that already contains the container, so names stay distinct.
        if not entry.friendly_name:
            return entry
        if "{index}" not in entry.friendly_name:
            _LOGGER.debug("Catalog pattern %s has no {index} in its name, using the generated one", key)
            return replace(entry, friendly_name=None)
        return replace(entry, friendly_name=entry.friendly_name.format(index=index))

    def update_missing_entities(self) -> None:
        """Add missing entities when no capabilities returned by the API.

        This is done dynamically but only when the reported state contains the attributes.
        """
        if not self.own_capabilties or not self.reported_state:
            return

        for key, catalog_item in self.catalog.items():
            if is_catalog_pattern(key):
                # Pattern entry, not a capability an appliance can report.
                continue
            category = self.data.get_category(key)
            if (
                category
                and self.reported_state.get(category, None)
                and self.reported_state.get(category, None).get(key)
            ) or (not category and self.reported_state.get(key, None)):
                found: bool = False
                for entity in self.entities:
                    if entity.entity_attr == key and entity.entity_source == category:
                        found = True
                        keys = key.split("/")
                        capabilities = self.data.capabilities
                        for key in keys[:-1]:
                            capabilities = capabilities.setdefault(key, {})
                        capabilities[keys[-1]] = catalog_item.capability_info
                        break
                if not found:
                    _LOGGER.debug(
                        "Electrolux discovered new entity from extracted data. Key: %s",
                        key,
                    )
                    if entity := self.get_entity(key):
                        self.entities.extend(entity)

    def get_state(self, attr_name: str) -> dict[str, Any] | None:
        """Retrieve the start from self.reported_state using the attribute name.

        May contain slashes for nested keys.
        """

        keys = attr_name.split("/")
        result = self.reported_state

        for key in keys:
            result = result.get(key)
            if result is None:
                return None

        return result

    def get_entity(self, capability: str) -> list[ElectroluxEntity] | None:
        """Return the entity."""
        entity_type = self.data.get_entity_type(capability)
        entity_name = self.data.get_entity_name(capability)
        entity_attr = self.data.get_entity_attr(capability)
        category = self.data.get_category(capability)
        capability_info = self.data.get_capability(capability)
        device_class = self.data.get_entity_device_class(capability)
        entity_category = None
        entity_icon = None
        unit = self.data.get_entity_unit(capability)
        display_name = self.data.get_sensor_name(capability)

        # get the item definition from the catalog
        catalog_item = self.get_catalog_entry(capability)
        if catalog_item:
            if capability_info is None:
                capability_info = catalog_item.capability_info
            elif "values" not in capability_info and "values" in catalog_item.capability_info:
                capability_info["values"] = catalog_item.capability_info["values"]

            device_class = catalog_item.device_class
            unit = catalog_item.unit
            entity_category = catalog_item.entity_category
            entity_icon = catalog_item.entity_icon

        # override the api determined type by the catalog entity_type
        if isinstance(device_class, BinarySensorDeviceClass):
            entity_type = BINARY_SENSOR
        if isinstance(device_class, ButtonDeviceClass):
            entity_type = BUTTON
        if isinstance(device_class, NumberDeviceClass):
            entity_type = NUMBER
        if isinstance(device_class, SensorDeviceClass):
            entity_type = SENSOR
        if isinstance(device_class, SwitchDeviceClass):
            entity_type = SWITCH

        # override the api determined type by the catalog entity_platform
        if catalog_item and isinstance(catalog_item.entity_platform, Platform):
            entity_type = catalog_item.entity_platform

        _LOGGER.debug(
            "Electrolux get_entity. entity_type: %s entity_name: %s entity_attr: %s entity_source: %s capability: %s device_class: %s unit: %s, catalog: %s",
            entity_type,
            entity_name,
            entity_attr,
            category,
            capability_info,
            device_class,
            unit,
            catalog_item,
        )

        def electrolux_entity_factory(
            name: str,
            entity_type: Platform | None,
            entity_name: str,
            entity_attr: str,
            entity_source: str,
            capability: str,
            unit: str,
            entity_category: str,
            device_class: str,
            icon: str,
            catalog_entry: ElectroluxDevice | None,
            commands: Any | None = None,
        ):
            entity_classes = {
                BINARY_SENSOR: ElectroluxBinarySensor,
                BUTTON: ElectroluxButton,
                NUMBER: ElectroluxNumber,
                SELECT: ElectroluxSelect,
                SENSOR: ElectroluxSensor,
                SWITCH: ElectroluxSwitch,
            }

            entity_class = entity_classes.get(entity_type)

            if entity_class is None:
                _LOGGER.debug("Unknown entity type %s for %s", entity_type, name)
                raise ValueError(f"Unknown entity type: {entity_type}")

            entity_params = {
                "coordinator": self.coordinator,
                "config_entry": self.coordinator.config_entry,
                "pnc_id": self.pnc_id,
                "name": name,
                "entity_type": entity_type,
                "entity_name": entity_name,
                "entity_attr": entity_attr,
                "entity_source": entity_source,
                "capability": capability,
                "unit": unit,
                "entity_category": entity_category,
                "device_class": device_class,
                "icon": icon,
                "catalog_entry": catalog_entry,
            }

            if commands is None:
                return [entity_class(**entity_params)]

            entities: list[
                ElectroluxBinarySensor
                | ElectroluxNumber
                | ElectroluxSensor
                | ElectroluxSwitch
                | ElectroluxButton
                | ElectroluxSelect
            ] = []
            # Replace entity name and icons for multi-entities attribute (one value = one entity)
            for command in commands:
                entity = {**entity_params, "val_to_send": command}
                if catalog_item:
                    if catalog_item.entity_value_named:
                        entity["name"] = command
                    if catalog_item.entity_icons_value_map and catalog_item.entity_icons_value_map.get(command, None):
                        entity["icon"] = catalog_item.entity_icons_value_map.get(command)
                # Instanciate the new entity and append it
                entities.append(entity_class(**entity))
            return entities

        if entity_type in PLATFORMS:
            commands = capability_info.get("values", {}) if entity_type == BUTTON else None
            return electrolux_entity_factory(
                name=display_name,
                entity_type=entity_type,
                entity_name=entity_name,
                entity_attr=entity_attr,
                entity_source=category,
                capability=capability_info,
                unit=unit,
                entity_category=entity_category,
                device_class=device_class,
                icon=entity_icon,
                catalog_entry=catalog_item,
                commands=commands,
            )

        return []

    def setup(self, data: ElectroluxLibraryEntity):
        """Configure the entity."""
        self.data: ElectroluxLibraryEntity = data
        self.entities: list[ElectroluxEntity] = []
        entities: list[ElectroluxEntity] = []
        # Extraction of the appliance capabilities & mapping to the known entities of the component
        # [ "applianceState", "autoDosing",..., "userSelections/analogTemperature",...]
        capabilities_names = self.data.sources_list()

        if capabilities_names is None and self.state:
            # No capabilities returned (unstable API)
            # We could rebuild them from catalog but this creates entities that are
            # not required by each device type (fridge, dryer, vacumn etc are all different)
            _LOGGER.warning("Electrolux API returned no capability definition")

        # For each capability src
        if capabilities_names:
            for capability in capabilities_names:
                if entity := self.get_entity(capability):
                    entities.extend(entity)
                else:
                    _LOGGER.debug("Could not create entity for capability %s", capability)

        # Add static attributes: attributes the API reports but does not
        # advertise as capabilities.
        #
        # Done after the capability pass and keyed on what that pass actually
        # produced, not on whether the name appears in the capability document.
        # An attribute can be advertised and still yield no entity - when the
        # walker cannot classify its type - and it would then be lost if this
        # skipped on the name alone. Where the capability pass did build one,
        # skipping is required: the two would share a unique id.
        built = {(entity.entity_attr, entity.entity_source) for entity in entities}
        for static_attribute in STATIC_ATTRIBUTES:
            _LOGGER.debug("Electrolux static_attribute %s", static_attribute)
            # attr not found in state, next attr
            if self.get_state(static_attribute) is None:
                continue
            if (
                self.data.get_entity_attr(static_attribute),
                self.data.get_category(static_attribute),
            ) in built:
                _LOGGER.debug(
                    "Electrolux static_attribute %s already built from the capability document",
                    static_attribute,
                )
                continue
            if catalog_item := self.get_catalog_entry(static_attribute):
                if (entity := self.get_entity(static_attribute)) is None:
                    # catalog definition and automatic checks fail to determine type
                    _LOGGER.debug("Electrolux static_attribute undefined %s", static_attribute)
                    continue
                # add to the capability dict
                keys = static_attribute.split("/")
                capabilities = self.data.capabilities
                for key in keys[:-1]:
                    capabilities = capabilities.setdefault(key, {})
                capabilities[keys[-1]] = catalog_item.capability_info
                _LOGGER.debug("Electrolux adding static_attribute %s", static_attribute)
                entities.extend(entity)

        # Setup each found entity
        self.entities = entities
        for entity in entities:
            entity.setup(data)

    def update_reported_data(self, reported_data: dict[str, Any]):
        """Update the reported data."""
        _LOGGER.debug("Electrolux update reported data %s", reported_data)
        try:
            self.reported_state.update(deep_merge_dicts(self.reported_state, reported_data))
            _LOGGER.debug("Electrolux updated reported data %s", self.state)
            self.update_missing_entities()
            for entity in self.entities:
                entity.update(self.state)

        except Exception as ex:  # noqa: BLE001
            _LOGGER.debug(
                "Electrolux status could not update reported data with %s. %s",
                reported_data,
                ex,
            )

    def update(self, appliance_status: ApplienceStatusResponse):
        """Update appliance status."""
        self.state = appliance_status
        self.update_missing_entities()
        for entity in self.entities:
            entity.update(self.state)


class Appliances:
    """Appliance class definition."""

    def __init__(self, appliances: dict[str, Appliance]) -> None:
        """Initialize the class."""
        self.appliances = appliances

    def get_appliance(self, pnc_id) -> Appliance:
        """Return the appliance."""
        return self.appliances.get(pnc_id, None)

    def get_appliances(self) -> dict[str, Appliance]:
        """Return all appliances."""
        return self.appliances

    def get_appliance_ids(self) -> list[str]:
        """Return all appliance ids."""
        return list(self.appliances)
