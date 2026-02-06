"""Defined catalog of entities for purifier type devices."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_BILLION,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from .model import ElectroluxDevice

A9 = {
    "Temp": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        entity_category=None,
        friendly_name="Temperature",
    ),
    "Humidity": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.HUMIDITY,
        unit=PERCENTAGE,
        entity_category=None,
        friendly_name="Humidity",
    ),
    "PM1": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.PM1,
        unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        entity_category=None,
        friendly_name="PM1",
    ),
    "PM2_5": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.PM25,
        unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        entity_category=None,
        friendly_name="PM2.5",
    ),
    "PM10": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.PM10,
        unit=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        entity_category=None,
        friendly_name="PM10",
    ),
    "TVOC": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        unit=CONCENTRATION_PARTS_PER_BILLION,
        entity_category=None,
        friendly_name="TVOC",
    ),
    "ECO2": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.CO2,
        unit=CONCENTRATION_PARTS_PER_MILLION,
        entity_category=None,
        friendly_name="eCO2",
    ),
    "DoorOpen": ElectroluxDevice(
        capability_info={"access": "read", "type": "boolean"},
        device_class=BinarySensorDeviceClass.DOOR,
        unit=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        # entity_icon="mdi:cup-outline",
        friendly_name="Door Open",
    ),
    "FilterType": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=SensorDeviceClass.ENUM,
        unit=None,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:air-filter",
        value_mapping={
            48: "BREEZE Complete air filter",
            49: "CLEAN Ultrafine particle filter",
            51: "CARE Ultimate protect filter",
            64: "Breeze 360 filter",
            65: "Clean 360 Ultrafine particle filter",
            66: "Protect 360 filter",
            67: "Breathe 360 filter",
            68: "Fresh 360 filter",
            96: "Breeze 360 filter",
            99: "Breeze 360 filter",
            100: "Fresh 360 filter",
            192: "FRESH Odour protect filter",
            0: "Filter",
        },
    ),
    "FilterLife": ElectroluxDevice(
        capability_info={"access": "read", "type": "number"},
        device_class=None,
        unit=PERCENTAGE,
        entity_category=None,
        entity_icon="mdi:air-filter",
        friendly_name="Filter Life",
    ),
}
