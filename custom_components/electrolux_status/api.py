"""API for Electrolux Status."""

from __future__ import annotations

import logging
import re
from typing import Any, TypedDict

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import Platform, UnitOfTemperature

from .const import (
    ATTRIBUTES_BLACKLIST,
    ATTRIBUTES_WHITELIST,
    BINARY_SENSOR,
    BUTTON,
    NUMBER,
    RENAME_RULES,
    SENSOR,
    SWITCH,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class UserInput(TypedDict, total=False):
    """TypedDict for config flow user input."""

    api_key: str
    access_token: str
    refresh_token: str
    notification_default: bool
    notification_diag: bool
    notification_warning: bool


def deep_merge_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge two dictionaries.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


class ElectroluxLibraryEntity:
    """Electrolux Library Entity."""

    name: str
    status: str
    state: dict[str, Any]
    appliance_info: dict[str, Any]
    capabilities: dict[str, Any] | None

    def __init__(
        self,
        name,
        status: str,
        state: dict[str, Any],
        appliance_info: dict[str, Any],
        capabilities: dict[str, Any] | None,
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

    def get_name(self) -> str:
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
                    and (
                        (i == len(sensor) - 1)
                        or (sensor[i + 1].isupper() or sensor[i + 1].isdigit())
                    )
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
        if not self.capabilities:
            return None

        if self.capabilities.get(attr_name, None):
            return self.capabilities.get(attr_name)

        keys = attr_name.split("/")
        result: dict[str, Any] | None = self.capabilities

        for key in keys:
            if not isinstance(result, dict):
                return None
            result = result.get(key)
            if result is None:
                return None

        return result if isinstance(result, dict) else None

    def get_entity_unit(self, attr_name: str) -> str | None:
        """Get entity unit type."""
        capability_def = self.get_capability(attr_name)
        if not capability_def:
            return None
        # Type : string, int, number, boolean (other values ignored)
        type_units = capability_def.get("type", None)
        if not type_units:
            return None
        if type_units == "temperature":
            return UnitOfTemperature.CELSIUS
        return None

    def get_entity_device_class(self, attr_name: str) -> Any:
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
        if (
            type_object == "boolean"
            and access == "readwrite"
            and capability_def.get("values", None) is not None
        ):
            return SWITCH

        # List of values ? if values is defined and has at least 1 entry
        values: dict[str, Any] | None = capability_def.get("values", None)
        if (
            values
            and access == "readwrite"
            and isinstance(values, dict)
            and len(values) > 0
        ):
            if type_object == "string":
                upper_values = {str(k).upper() for k in values}
                if upper_values == {"ON", "OFF"}:
                    return SWITCH
            if (
                type_object not in ["number", "temperature"]
                or capability_def.get("min", None) is None
            ):
                return Platform.SELECT

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
                    self.get_entity_name(attr_name) == "executeCommand"
                    and access == "read"
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
                    if (
                        isinstance(sub_value, dict)
                        and "access" in sub_value
                        and "type" in sub_value
                    ):
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
