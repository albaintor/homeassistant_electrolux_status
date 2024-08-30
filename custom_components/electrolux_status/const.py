"""The electrolux Status constants."""

from homeassistant.const import Platform

# Base component constants
NAME = "Electrolux status"
DOMAIN = "electrolux_status"
DOMAIN_DATA = f"{DOMAIN}_data"

# Platforms
BINARY_SENSOR = Platform.BINARY_SENSOR
BUTTON = Platform.BUTTON
NUMBER = Platform.NUMBER
SELECT = Platform.SELECT
SENSOR = Platform.SENSOR
SWITCH = Platform.SWITCH
PLATFORMS = [BINARY_SENSOR, BUTTON, NUMBER, SELECT, SENSOR, SWITCH]

# Configuration and options
CONF_LANGUAGE = "language"
CONF_RENEW_INTERVAL = "renew_interval"
CONF_NOTIFICATIONS = "notifications"

# Defaults
DEFAULT_LANGUAGE = "English"
DEFAULT_WEBSOCKET_RENEWAL_DELAY = 43200  # 12 hours

# these are attributes that appear in the state file but not in the capabilities.
# defining them here and in the catalog will allow these devices to be added dynamicaly
STATIC_ATTRIBUTES = [
    "connectivityState",
    "networkInterface/linkQualityIndicator",
    "applianceMode",
]

# Icon mappings for default executeCommands
icon_mapping = {
    "OFF": "mdi:power-off",
    "ON": "mdi:power-on",
    "START": "mdi:play",
    "STOPRESET": "mdi:stop",
    "PAUSE": "mdi:pause",
    "RESUME": "mdi:play-pause",
}

# List of supported Mobile App languages
# refer to https://emea-production.api.electrolux.net/masterdata-service/api/v1/languages
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
