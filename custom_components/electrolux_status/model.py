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


class ElectroluxTokenStore(TypedDict):
    """Serialized exposed entities storage storage collection."""

    accounts: dict[str, UserToken]
