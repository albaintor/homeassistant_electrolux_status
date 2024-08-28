"""The electrolux Status constants."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTime, UnitOfTemperature, UnitOfPower
from homeassistant.helpers.entity import EntityCategory

# Base component constants
NAME = "Elettrolux status"
DOMAIN = "electrolux_status"
DOMAIN_DATA = f"{DOMAIN}_data"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
BUTTON = "button"
SELECT = "select"
SWITCH = "switch"
NUMBER = "number"
PLATFORMS = [BINARY_SENSOR, SENSOR, BUTTON, SELECT, SWITCH, NUMBER]

# Configuration and options
CONF_ENABLED = "enabled"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_LANGUAGE = "language"
CONF_RENEW_INTERVAL = "renew_interval"

# Defaults
DEFAULT_LANGUAGE = "English"
DEFAULT_WEBSOCKET_RENEWAL_DELAY = 43200 # 12 hours

# Common entities
COMMON_ATTRIBUTES = ["connectivityState", "networkInterface/linkQualityIndicator", "applianceMode"]

# capabilities model :
#
# key = "entry" or "category/entry"
# {
#   access = "read" or "readwrite" or "write" (other values ignored)
#   type = "boolean" or "string" or "number" (other values ignored including "int" type only used in maintenance section)
#   => problem to differentiate classic numbers to time : check after "time" string in key name ? or temperature
#   values (optional)= list of available values
#   min / max / step for type = number
# }

TIME_ENTITIES_TO_UPDATE = ["timeToEnd"]

Catalog: dict[str, [dict, str, str, str, str]] = {
        "timeToEnd": [{"access": "read","type": "number"}, None, None, UnitOfTime.SECONDS, None, "mdi:av-timer"],
        "runningTime": [{"access": "read","type": "number"}, None, None, UnitOfTime.SECONDS, None, "mdi:timelapse"],
        "cyclePhase": [{"access": "read","type": "string"}, None, None, None, None],
        "cycleSubPhase": [{"access": "read","type": "string"}, None, None, None, None],
        "applianceState": [{"access": "read","type": "string"}, None, None, None, None, "mdi:state-machine"],
        "displayTemperature": [{"access": "read","type": "string"}, None, SensorDeviceClass.TEMPERATURE, None, None, "mdi:thermometer"],
        "displayFoodProbeTemperature": [{"access": "read","type": "number"}, None, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, None, "mdi:thermometer"],
        "sensorTemperature": [{"access": "read","type": "number"}, None, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, None, "mdi:thermometer"],
        "defrostTemperature": [{"access": "read","type": "number"}, None, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, None, "mdi:snowflake-thermometer"],
        "targetMicrowavePower": [{"access": "read","type": "number"}, None, SensorDeviceClass.ENERGY, UnitOfPower.WATT, None, "mdi:microwave"],
        "ovenProcessIdentifier": [{"access": "read","type": "string"}, None, None, None, None],
        "remoteControl": [{"access": "read","type": "string"}, None, None, None, None, "mdi:remote"],
        "defaultExtraRinse": [{"access": "readwrite","type": "string", "values": {"EXTRA_RINSE_1": {},"EXTRA_RINSE_2": {},"EXTRA_RINSE_OFF": {}}}, None, None, None, None],
        "analogTemperature": [{"access": "readwrite","type": "string", "values": {"20_CELSIUS": {},"30_CELSIUS": {},"40_CELSIUS": {},"50_CELSIUS": {},"60_CELSIUS": {},"90_CELSIUS": {},"95_CELSIUS": {},"COLD": {}}}, "userSelections", None, None, None, "mdi:thermometer"],
        "targetTemperatureC" : [{"access": "readwrite","type": "number", "max": 300.0,"min": 0,"step": 5.0}, None, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, None, "mdi:thermometer"],
        # "targetTemperature": ["container", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS],
        "startTime": [{"access": "readwrite","type": "number","max": 72000,"min": 0,"step": 1800}, None, None, UnitOfTime.SECONDS, None, "mdi:clock-start"],
        "waterSoftenerMode": [{"access": "read","type": "string"}, None, None, None, None, "mdi:water-check"],
        "steamValue": [{"access": "read","type": "string","values": {"STEAM_MAX": {},"STEAM_MED": {},"STEAM_MIN": {},"STEAM_OFF": {}}}, "userSelections", None, None, None, "mdi:pot-steam"],
        "analogSpinSpeed": [{"access": "readwrite","type": "string","values": {"0_RPM": {},"1000_RPM": {},"1200_RPM": {},"1400_RPM": {},"1600_RPM": {},"400_RPM": {},"600_RPM": {},"800_RPM": {},"DISABLED": {"disabled": True}}}, "userSelections", None, None, None, "mdi:speedometer"],
        "programUID": [{"access": "read","type": "string"}, "userSelections", None, None, None, "mdi:application-settings-outline"],
        "doorState": [{"access": "read","type": "string"}, None, BinarySensorDeviceClass.DOOR, None, None, "mdi:door"],
        "doorLock": [{"access": "read","type": "string"}, None, BinarySensorDeviceClass.LOCK, None, None, "mdi:door-closed-lock"],
        "uiLockMode": [{"access": "readwrite","type": "boolean"}, None, None, None, None, "mdi:lock"],
        "endOfCycleSound": [{"access": "readwrite","type": "string","values": {"NO_SOUND": {},"SHORT_SOUND": {}}}, None, None, None, None, "mdi:cellphone-sound"],
        "preWashPhase": [{"access": "read","type": "boolean"}, None, None, None, None, "mdi:washing-machine"],
        # "eLUXTimeManagerLevel": ["valTransl", None, None],
        # "waterTankWarningMode": [None, None, None],
        # "dryingTime": [None, None, None],
        # "humidityTarget": ["valTransl", None, None],
        # "antiCreaseValue": [None, None, None],
        # "drynessValue": ["valTransl", None, None],
        # "programUID": ["valTransl", None, None],
        # "sensorHumidity": ["numberValue", SensorDeviceClass.HUMIDITY, PERCENTAGE, None],
        # "ambientTemperature": ["container", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, None],
        "ambientTemperatureC" : [{"access": "read","type": "number"}, None, SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, None, "mdi:thermometer"],
        "applianceTotalWorkingTime": [{"access": "read", "type": "number"}, None, None, UnitOfTime.SECONDS, EntityCategory.DIAGNOSTIC, "mdi:clock-time-eight-outline"],
        "totalCycleCounter": [{"access": "read", "type": "number"}, None, None, None, EntityCategory.DIAGNOSTIC, "mdi:counter"],
        "waterHardness": [{"access": "read", "type": "string"}, None, None, None, EntityCategory.DIAGNOSTIC, "mdi:water"],
        "applianceMode": [{"access": "read", "type": "string"}, None, None, None, EntityCategory.DIAGNOSTIC, "mdi:auto-mode"],
        "totalWashingTime": [{"access": "read", "type": "number"}, None, None, UnitOfTime.SECONDS, EntityCategory.DIAGNOSTIC, "mdi:washing-machine"],
        "linkQualityIndicator": [{"access": "read", "type": "string", "values": {"EXCELLENT": {},"GOOD": {},"POOR": {},"UNDEFINED": {},"VERY_GOOD": {},"VERY_POOR": {}}}, "networkInterface", None, None, EntityCategory.DIAGNOSTIC, "mdi:wifi-strength-2"],
        "executeCommand": [{"access": "write", "type": "string", "values": {"OFF": {},"ON": {},"PAUSE": {},"RESUME": {},"START": {},"STOPRESET": {}}}, None, None, None, None],
        # "rinseAidLevel": [None, None, None],
        # "fCTotalWashCyclesCount": [None, None, None],
        # "fCTotalWashingTime": [None, None, None],
        # "applianceMode": [None, None, None],
        "connectivityState": [{"access": "read","type": "string"}, None, None, None, EntityCategory.DIAGNOSTIC, "mdi:wifi"],
}

icon_mapping = {
    "OFF": "mdi:power-off",
    "ON": "mdi:power-on",
    "START": "mdi:play",
    "STOPRESET": "mdi:stop",
    "PAUSE": "mdi:pause",
    "RESUME": "mdi:play-pause",
}

# List of supported Mobile App languages (from https://emea-production.api.electrolux.net/masterdata-service/api/v1/languages)
languages = {
    "български": "bul",
    "český": "ces",
    "Dansk": "dan",
    "Deutsch": "deu",
    "ελληνικός": "ell",
    "English": "eng",
    "eesti": "est",
    "Soome": "fin",
    "Français": "fra",
    "Hrvatski": "hrv",
    "magyar": "hun",
    "Italiano": "ita",
    "lettone": "lav",
    "lituano": "lit",
    "Luxembourgish": "ltz",
    "nederlands": "nld",
    "Norsk": "nor",
    "Polski": "pol",
    "Português": "por",
    "Română": "ron",
    "rusesc": "rus",
    "slovenský": "slk",
    "slovinský": "slv",
    "Español": "spa",
    "Svenska": "swe",
    "Türk": "tur",
    "Ukrayna": "ukr",
}
