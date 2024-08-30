"""Defined catalog of entities for refridgerator type devices."""

from homeassistant.components.switch import SwitchDeviceClass

from .model import ElectroluxDevice

EHE6899SA = {
    "uiLockMode": ElectroluxDevice(
        capability_info={
            "access": "readwrite",
            "type": "boolean",
            "values": {"OFF": {}, "ON": {}},
        },
        device_class=SwitchDeviceClass.SWITCH,
        unit=None,
        entity_category=None,
        entity_icon="mdi:lock",
        friendly_name="Child Lock Internal",
    ),
    "ui2LockMode": ElectroluxDevice(
        capability_info={
            "access": "readwrite",
            "type": "boolean",
            "values": {"OFF": {}, "ON": {}},
        },
        device_class=SwitchDeviceClass.SWITCH,
        unit=None,
        entity_category=None,
        entity_icon="mdi:lock",
        friendly_name="Child Lock External",
    ),
}
