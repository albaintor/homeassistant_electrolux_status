"""Defined catalog of entities for hob (HB) type devices.

Every entry here only supplies presentation metadata (friendly name, device
class, unit, icon, category) or a deliberate platform override. Whether a
capability exists at all, its access mode, its enum values and its numeric
bounds all remain owned by the capability document returned by the API.

Keys may use a ``*`` wildcard in place of the numeric suffix of a container,
e.g. ``hobZone*/runningTime``. Such an entry describes every container of its
kind, so its ``friendly_name`` must carry the ``{index}`` placeholder - it is
replaced with the container's number, otherwise every zone would present the
same name to the UI, to search and to voice assistants. Hobs report a variable and non-contiguous set of
zones (the AEG CCE84779CB reports hobZone1-4 plus hobZone7-8 for its bridged
zones), so entries must never be written against a fixed zone count.
"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import Platform, UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from .model import ElectroluxDevice

HB: dict[str, ElectroluxDevice] = {
    #
    # Appliance level
    #
    "applianceState": ElectroluxDevice(
        capability_info={"access": "read", "type": "string"},
        entity_icon="mdi:stove",
        # Unlike a washer/dryer cycle state, the hob state is the primary
        # thing a user wants on a dashboard, so enable it by default.
        entity_registry_enabled_default=True,
    ),
    "childLock": ElectroluxDevice(
        friendly_name="Child lock",
        capability_info={"access": "read", "type": "boolean"},
        device_class=BinarySensorDeviceClass.LOCK,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:account-lock",
        # BinarySensorDeviceClass.LOCK is "on == unlocked", the appliance
        # reports "true == locked".
        state_invert=True,
        entity_platform=Platform.BINARY_SENSOR,
    ),
    "uiLockMode": ElectroluxDevice(
        friendly_name="Control panel lock",
        # The HB capability document reports uiLockMode as access "read".
        # CATALOG_BASE models it as a writable switch for other appliance
        # types; override it back to a read-only binary sensor here so the
        # integration never offers an action the hob will not honour.
        capability_info={"access": "read", "type": "boolean"},
        device_class=BinarySensorDeviceClass.LOCK,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:lock",
        state_invert=True,
        entity_platform=Platform.BINARY_SENSOR,
    ),
    "keySoundTone": ElectroluxDevice(
        friendly_name="Key sound tone",
        entity_category=EntityCategory.CONFIG,
        entity_icon="mdi:volume-high",
    ),
    "keyModel": ElectroluxDevice(
        friendly_name="Key model",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:identifier",
        entity_registry_enabled_default=False,
    ),
    #
    # Integrated extractor / hood
    #
    "hobHood/hobToHoodFanSpeed": ElectroluxDevice(
        friendly_name="Extractor fan speed",
        entity_icon="mdi:fan",
    ),
    "hobHood/hobToHoodState": ElectroluxDevice(
        friendly_name="Extractor mode",
        entity_icon="mdi:auto-mode",
    ),
    "hobHood/hobToHoodMode": ElectroluxDevice(
        friendly_name="Extractor hob-to-hood level",
        entity_category=EntityCategory.CONFIG,
        entity_icon="mdi:tune-variant",
    ),
    "hobHood/targetDuration": ElectroluxDevice(
        friendly_name="Extractor run-on duration",
        device_class=NumberDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        entity_icon="mdi:timer-cog",
    ),
    "hobHood/timeToEnd": ElectroluxDevice(
        friendly_name="Extractor time to end",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        entity_icon="mdi:timer-sand",
    ),
    "hobHood/windowNotification": ElectroluxDevice(
        friendly_name="Window notification",
        entity_icon="mdi:window-open-variant",
    ),
    "hobHood/hoodFilterCharcIndication": ElectroluxDevice(
        friendly_name="Charcoal filter",
        # Reported as access "readwrite" (the appliance allows resetting the
        # indication), but a switch would imply that saturation itself can be
        # turned on. Expose the state only; a reset button can follow later.
        capability_info={"access": "read", "type": "boolean"},
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:air-filter",
        entity_platform=Platform.BINARY_SENSOR,
    ),
    "hobHood/hoodFilterGreaseIndication": ElectroluxDevice(
        friendly_name="Grease filter",
        capability_info={"access": "read", "type": "boolean"},
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:air-filter",
        entity_platform=Platform.BINARY_SENSOR,
    ),
    #
    # Cooking zones. Wildcard keys, one entity per zone the device reports.
    #
    "hobZone*/heatingQualitativeLevel": ElectroluxDevice(
        friendly_name="Zone {index} power level",
        # Deliberately read-only. See MODULE NOTE at the bottom of this file.
        entity_icon="mdi:stove",
        entity_platform=Platform.SENSOR,
    ),
    "hobZone*/hobPotDetected": ElectroluxDevice(
        friendly_name="Zone {index} pot detection",
        # Kept as a four-state enum sensor rather than a binary sensor:
        # NO_POT_IDLE / NO_POT_RUNNING / POT_IDLE / POT_RUNNING carries both
        # pot presence and whether the zone is running, which a binary sensor
        # would throw away.
        entity_icon="mdi:pot-steam",
    ),
    "hobZone*/residualHeatState": ElectroluxDevice(
        friendly_name="Zone {index} residual heat",
        entity_icon="mdi:heat-wave",
    ),
    "hobZone*/runningTime": ElectroluxDevice(
        friendly_name="Zone {index} running time",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        entity_icon="mdi:timelapse",
    ),
    "hobZone*/timeToEnd": ElectroluxDevice(
        friendly_name="Zone {index} time to end",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        entity_icon="mdi:timer-sand",
    ),
    "hobZone*/targetDuration": ElectroluxDevice(
        friendly_name="Zone {index} target duration",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        entity_icon="mdi:timer-cog",
        # Read-only: see MODULE NOTE.
        entity_platform=Platform.SENSOR,
    ),
    "hobZone*/reminderTime": ElectroluxDevice(
        friendly_name="Zone {index} reminder time",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:timer-alert",
        entity_platform=Platform.SENSOR,
    ),
    "hobZone*/hobMaxPowerLevel": ElectroluxDevice(
        friendly_name="Zone {index} max power level",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:speedometer",
        entity_registry_enabled_default=False,
    ),
    "hobZone*/hobCoil": ElectroluxDevice(
        friendly_name="Zone {index} coil",
        # Declared as a number by the capability document but reported as an
        # empty object by the appliance, so it has no displayable value.
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:coil",
        entity_registry_enabled_default=False,
    ),
    #
    # Heating modules (flexible/bridge zones)
    #
    "hobModule*/heatingModuleType": ElectroluxDevice(
        friendly_name="Module {index} heating module type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:chip",
        entity_registry_enabled_default=False,
    ),
    "hobModule*/hobFrontZone": ElectroluxDevice(
        friendly_name="Module {index} front zone",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:square-rounded",
    ),
    "hobModule*/hobMiddleZone": ElectroluxDevice(
        friendly_name="Module {index} middle zone",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:square-rounded",
    ),
    "hobModule*/hobRearZone": ElectroluxDevice(
        friendly_name="Module {index} rear zone",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon="mdi:square-rounded",
    ),
    "hobModule*/procookLevelFront": ElectroluxDevice(
        friendly_name="Module {index} Procook level front",
        # Read-only: see MODULE NOTE.
        entity_icon="mdi:stove",
        entity_platform=Platform.SENSOR,
    ),
    "hobModule*/procookLevelRear": ElectroluxDevice(
        friendly_name="Module {index} Procook level rear",
        entity_icon="mdi:stove",
        entity_platform=Platform.SENSOR,
    ),
}

# MODULE NOTE — why cooking power is exposed read-only
#
# The CCE84779CB capability document reports a handful of cooking controls as
# writable: hobZone1/heatingQualitativeLevel (0-9), hobZone3/targetDuration and
# hobModule1-2/procookLevelFront|Rear. The equivalent properties on every other
# zone are read-only, which makes the writable set look like an inconsistency in
# the appliance's capability document rather than a supported feature.
#
# Turning a burner on remotely is also safety-relevant: the appliance reports
# remoteControl = NOT_SAFETY_RELEVANT_ENABLED, meaning it only accepts remote
# commands that are not safety-relevant. These entities are therefore pinned to
# read-only sensors until Electrolux documents remote cooking control and the
# maintainers decide they want it. Removing the entity_platform override on the
# entries above is all that is needed to revisit that decision.
