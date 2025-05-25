"""Electrolux air conditioner specific catalog."""

from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.components.select import SelectDeviceClass
from homeassistant.const import UnitOfTemperature

from .model import ElectroluxDevice

# Catalog specific to air conditioners
CATALOG_AIR_CONDITIONER = {
    "targetTemperatureC": ElectroluxDevice(
        capability_info={
            "access": "readwrite",
            "type": "temperature",
            "default": 15.56,
            "max": 32.22,
            "min": 15.56,
            "step": 1,
        },
        device_class=NumberDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        entity_category=None,
        entity_icon="mdi:thermometer",
    ),
    "targetTemperatureF": ElectroluxDevice(
        capability_info={
            "access": "readwrite", 
            "type": "temperature",
            "default": 60,
            "max": 90,
            "min": 60,
            "step": 1,
        },
        device_class=NumberDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.FAHRENHEIT,
        entity_category=None,
        entity_icon="mdi:thermometer",
    ),
    "ambientTemperatureC": ElectroluxDevice(
        capability_info={"access": "read", "type": "temperature"},
        device_class=SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        entity_category=None,
        entity_icon="mdi:thermometer",
    ),
    "ambientTemperatureF": ElectroluxDevice(
        capability_info={"access": "read", "type": "temperature"},
        device_class=SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.FAHRENHEIT,
        entity_category=None,
        entity_icon="mdi:thermometer",
    ),
    "mode": ElectroluxDevice(
        capability_info={
            "access": "readwrite",
            "type": "string",
            "values": {
                "COOL": {},
                "ECO": {},
                "FANONLY": {},
                "OFF": {"disabled": True}
            },
        },
        device_class=None,
        unit=None,
        entity_category=None,
        entity_icon="mdi:air-conditioner",
    ),
    "fanSpeedSetting": ElectroluxDevice(
        capability_info={
            "access": "readwrite",
            "type": "string",
            "values": {
                "AUTO": {},
                "HIGH": {},
                "LOW": {},
                "MIDDLE": {},
            },
        },
        device_class=None,
        unit=None,
        entity_category=None,
        entity_icon="mdi:fan",
    ),
    "fanSpeedState": ElectroluxDevice(
        capability_info={
            "access": "read",
            "type": "string",
            "values": {
                "HIGH": {},
                "LOW": {},
                "MIDDLE": {},
            },
        },
        device_class=SensorDeviceClass.ENUM,
        unit=None,
        entity_category=None,
        entity_icon="mdi:fan",
    ),
    "sleepMode": ElectroluxDevice(
        capability_info={
            "access": "readwrite",
            "type": "string",
            "values": {"OFF": {}, "ON": {}},
        },
        device_class=SwitchDeviceClass.SWITCH,
        unit=None,
        entity_category=None,
        entity_icon="mdi:sleep",
    ),
    "executeCommand": ElectroluxDevice(
        capability_info={
            "access": "write",
            "type": "string",
            "values": {
                "OFF": {},
                "ON": {},
            },
        },
        device_class=SwitchDeviceClass.SWITCH,
        unit=None,
        entity_category=None,
        entity_icon="mdi:power",
        entity_icons_value_map={
            "OFF": "mdi:power-off",
            "ON": "mdi:power-on",
        },
        entity_value_named=True,
    ),
    "temperatureRepresentation": ElectroluxDevice(
        capability_info={
            "access": "readwrite",
            "type": "string",
            "values": {
                "CELSIUS": {},
                "FAHRENHEIT": {},
            },
        },
        device_class=None,
        unit=None,
        entity_category=None,
        entity_icon="mdi:temperature-celsius",
    ),
}
