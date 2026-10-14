"""Defined catalog for air conditioners, which become one climate entity.

Verified against a YI12F (12 kBTU combi air conditioner, applianceType CA) in Brazil. Other
models join by adding their appliance type and values here.
"""

from homeassistant.components.climate import HVACMode

# Appliance types (applianceInfo.applianceType) that get a climate entity.
AC_APPLIANCE_TYPES = frozenset({"CA"})

# Capabilities the climate entity drives. When the appliance reports them, they stop being
# separate entities.
AC_ABSORBED_CAPABILITIES = (
    "executeCommand",
    "mode",
    "targetTemperatureC",
    "targetTemperatureF",
    "fanSpeedSetting",
    "flapOscillate",
    "flapPosition",
    "sleepMode",
    "comfortAir",
    "autoSenseMode",
)

# Appliance mode to Home Assistant mode. Off is not a mode on the appliance: it is
# applianceState OFF, switched with executeCommand.
AC_HVAC_MODES = {
    "AUTO": HVACMode.AUTO,
    "COOL": HVACMode.COOL,
    "HEAT": HVACMode.HEAT,
    "DRY": HVACMode.DRY,
    "FANONLY": HVACMode.FAN_ONLY,
}

# fanSpeedSetting to fan_mode, in the order the card lists them.
AC_FAN_MODES = {
    "AUTO": "auto",
    "LOW": "low",
    "MIDDLE": "medium",
    "HIGH": "high",
    "TURBO": "turbo",
}

# Preset to the ON/OFF capability behind it, in priority order when more than one is ON.
AC_PRESETS = {
    "sleep": "sleepMode",
    "comfort": "comfortAir",
    "auto_sense": "autoSenseMode",
}

# Swing mode for flapOscillate ON. Fixed flap positions are position_0 to position_N, from the
# POSITION_N values of flapPosition. A model that oscillates but has no positions gets
# AC_SWING_STOPPED for flapOscillate OFF instead.
AC_SWING_OSCILLATE = "on"
AC_SWING_STOPPED = "off"

# From the capability triggers: the appliance ignores the target temperature while one of
# these holds, and ignores fan speed and flap position while one of the airflow locks is ON.
AC_TEMPERATURE_LOCKS = {"mode": "FANONLY", "sleepMode": "ON"}
AC_AIRFLOW_LOCKS = ("comfortAir", "autoSenseMode")

# After being switched off from cooling, the YI12F dries its coil for about five minutes ("secagem
# automática" in the app). It reports RUNNING and FANONLY with this attribute ON, then turns itself
# off. The user already switched it off, so the climate reads off while it dries.
AC_SELF_DRYING = ("cleanAirMode", "ON")
