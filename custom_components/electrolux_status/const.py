"""The electrolux Status constants."""

from homeassistant.const import Platform

# Base component constants
NAME = "Electrolux"
DOMAIN = "electrolux_status"

# Platforms
BINARY_SENSOR = Platform.BINARY_SENSOR
BUTTON = Platform.BUTTON
NUMBER = Platform.NUMBER
SELECT = Platform.SELECT
SENSOR = Platform.SENSOR
SWITCH = Platform.SWITCH
TEXT = Platform.TEXT
PLATFORMS = [BINARY_SENSOR, BUTTON, NUMBER, SELECT, SENSOR, SWITCH, TEXT]

# Configuration and options
CONF_NOTIFICATION_DEFAULT = "notifications"
CONF_NOTIFICATION_DIAG = "notifications_diagnostic"
CONF_NOTIFICATION_WARNING = "notifications_warning"
CONF_API_KEY = "api_key"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"

# Defaults
DEFAULT_WEBSOCKET_RENEWAL_DELAY = (
    7200  # 2 hours - balance between connection stability and rate limiting
)

# these are attributes that appear in the state file but not in the capabilities.
# defining them here and in the catalog will allow these devices to be added dynamically
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

# List of attributes to ignore and that won't be added as entities (regex format)
ATTRIBUTES_BLACKLIST: list[str] = [
    "^fCMiscellaneous.+",
    "fcOptisenseLoadWeight.*",
    "applianceCareAndMaintenance.*",
    "applianceMainBoardSwVersion",
    "coolingValveState",
    "networkInterface",
    "temperatureRepresentation",
]

ATTRIBUTES_WHITELIST: list[str] = [".*waterUsage", ".*tankAReserve", ".*tankBReserve"]

# Rules to simplify the naming of entities
RENAME_RULES: list[str] = [
    r"^userSelections\/[^_]+_",
    r"^userSelections\/",
    r"^fCMiscellaneousState\/[^_]+_",
    r"^fCMiscellaneousState\/",
]

# List of entity names that need to be updated to 0 manually when they are close to 0
TIME_ENTITIES_TO_UPDATE = ["timeToEnd"]
