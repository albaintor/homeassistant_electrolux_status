"""Define Electrolux Status data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict

from pyelectroluxocp.oneAppApiClient import UserToken

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.button import ButtonDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import EntityCategory, Platform


@dataclass
class ElectroluxDevice:
    """Define class for main domain information."""

    # use to override the internal naming logic
    # with a name defined in the catalog
    friendly_name: str | None = None

    # dictionary of the device capability
    # override and replace bad api data
    capability_info: dict[str, Any] = field(default_factory=dict)

    # type used here will override internal definitions / guesstimates
    # entity_platform will override the device_class specified
    device_class: (
        BinarySensorDeviceClass
        | ButtonDeviceClass
        | NumberDeviceClass
        | SensorDeviceClass
        | SwitchDeviceClass
        | None
    ) = None

    # suggested unit of measurement
    unit: str | None = None

    # Map the item to a HA category
    entity_category: EntityCategory | None = None

    # Define a custom icon for the entity
    entity_icon: str | None = None

    # invert the true / false state of the entity
    state_invert: bool = False

    # some entities return a string dict in capabilities but
    # an int in the api values. A defined dictionary can convert
    # those values from integer back to dictionary
    value_mapping: dict[int, str] = field(default_factory=dict)

    # a select normally writes back the token it displays. Some appliances
    # only accept the integer they report, so this applies value_mapping
    # in reverse before the value is sent
    value_mapping_on_write: bool = False

    # some on/off entiites derive their state from different api values
    # for instance, the state of the iceMaker is derived from
    # "iceMaker/applianceState" and controlled via "iceMaker/executeCommand"
    # by applying a state_mapping to "iceMaker/executeCommand" one entity can
    # display both and the button can be converted to a switch
    state_mapping: str | None = None

    # enable the entity by default but can be disabled in the catalog
    # some entities are not useful for most users and clog the logbook
    entity_registry_enabled_default: bool = True

    # there is no device class type for Select entities
    # other entities can derive their type via device_class
    # once Select entities have a device_class this is not needed
    entity_platform: Platform | None = None

    # Custom icons map according to values : useful for execute commands buttons
    entity_icons_value_map: dict[str, str] | None = None

    entity_value_named: bool = False

    # name and select options come from translations/<language>.json under
    # entity.<platform>.<translation_key>, so Home Assistant shows them in
    # each user's language. Select options become the lowercase tokens
    translation_key: str | None = None

    # when one of these raw values is written, the listed sibling attributes
    # of the same container are written with it. Mirrors what the
    # manufacturer app does, for example a program's default options
    write_defaults: dict[Any, dict[str, Any]] = field(default_factory=dict)

    # write_defaults only apply while another attribute ("source/attr") holds
    # one of these raw values, for example while no wash cycle is under way
    write_defaults_when: tuple[str, frozenset] | None = None

    # the entity is only available while another attribute ("source/attr")
    # holds one of these raw values. For options the appliance ignores
    # under some programs
    available_when: tuple[str, frozenset] | None = None


class ElectroluxTokenStore(TypedDict):
    """Serialized exposed entities storage storage collection."""

    accounts: dict[str, UserToken]
