"""Climate platform for Electrolux Status: one entity per air conditioner."""

import logging
import re
from typing import Any

from homeassistant.components.climate import ATTR_HVAC_MODE, ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .catalog_air_conditioner import (
    AC_AIRFLOW_LOCKS,
    AC_FAN_MODES,
    AC_HVAC_MODES,
    AC_PRESETS,
    AC_SELF_DRYING,
    AC_SWING_OSCILLATE,
    AC_SWING_STOPPED,
    AC_TEMPERATURE_LOCKS,
)
from .const import CLIMATE, DOMAIN
from .entity import ElectroluxEntity

_LOGGER: logging.Logger = logging.getLogger(__package__)

PRESET_NONE = "none"

# flapPosition values the climate can offer as fixed positions: POSITION_0, POSITION_1, ...
_POSITION = re.compile(r"^POSITION_(\d+)$")


def absorbed_unique_ids(entry_id: str, pnc_id: str, capability: dict[str, dict]) -> set[str]:
    """Return the unique ids the absorbed capabilities had as separate entities.

    Buttons carry the command in their unique id, so executeCommand had one per value.
    """
    ids: set[str] = set()
    for attr, definition in capability.items():
        if attr == "executeCommand":
            ids.update(f"{entry_id}-{value}-{attr}-root-{pnc_id}" for value in (definition or {}).get("values", {}))
        else:
            ids.add(f"{entry_id}-{attr}-root-{pnc_id}")
    return ids


def _migration_issue_id(entry: ConfigEntry, climate: "ElectroluxClimate") -> str:
    # Per entry and appliance: two accounts sharing one AC keep their own issue.
    return f"climate_migration_{entry.entry_id}_{climate.pnc_id}"


def _update_migration_issue(hass: HomeAssistant, entry: ConfigEntry, climate: "ElectroluxClimate") -> None:
    """Tell the user which old entities the climate replaced, until they are removed."""
    issue_id = _migration_issue_id(entry, climate)
    registry = er.async_get(hass)
    old_ids = absorbed_unique_ids(entry.entry_id, climate.pnc_id, climate.capability)
    leftovers = sorted(
        registered.entity_id
        for registered in er.async_entries_for_config_entry(registry, entry.entry_id)
        if registered.unique_id in old_ids
    )
    if not leftovers:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return
    # The registry has the id the user sees, renamed or not.
    climate_id = registry.async_get_entity_id(CLIMATE, DOMAIN, climate.unique_id) or climate.entity_id
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="climate_migration",
        translation_placeholders={
            "appliance": climate.get_appliance.name,
            "climate": climate_id,
            "entities": ", ".join(leftovers),
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    climates: list[ElectroluxClimate] = []
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [entity for entity in appliance.entities if entity.entity_type == CLIMATE]
            _LOGGER.debug(
                "Electrolux add %d CLIMATE entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)
            climates.extend(entities)
    if not climates:
        return
    for climate in climates:
        _update_migration_issue(hass, entry, climate)
        # Setup creates it again when the entry comes back; an unloaded entry should not leave it.
        issue_id = _migration_issue_id(entry, climate)
        entry.async_on_unload(lambda issue_id=issue_id: ir.async_delete_issue(hass, DOMAIN, issue_id))

    @callback
    def _registry_updated(event: Event[er.EventEntityRegistryUpdatedData]) -> None:
        # The issue lists the old entities still in the registry and names the climate: refresh it
        # when the user removes one of them or renames an entity, instead of at the next restart.
        if event.data["action"] == "remove" or "old_entity_id" in event.data:
            for climate in climates:
                _update_migration_issue(hass, entry, climate)

    entry.async_on_unload(hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _registry_updated))


class ElectroluxClimate(ElectroluxEntity, ClimateEntity):
    """One climate entity for an Electrolux air conditioner.

    self.capability holds the definition of every capability the entity absorbed, keyed by name.
    """

    _attr_translation_key = "air_conditioner"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, drying_capability: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize the climate entity, named after the appliance.

        drying_capability is the appliance's definition of the AC_SELF_DRYING attribute. It is
        not absorbed: the attribute keeps its own sensor.
        """
        super().__init__(**kwargs)
        self._drying_capability = drying_capability or {}
        self._attr_name = None
        base = f"{self.get_appliance.brand}_{self.get_appliance.name}".lower()
        base = re.sub(r"_+", "_", re.sub(r"[^a-z0-9_]", "_", base)).strip("_")
        self.entity_id = f"{CLIMATE}.{base}"

    @property
    def entity_domain(self) -> str:
        """Entity domain for the entry. Used for consistent entity_id."""
        return CLIMATE

    @property
    def unique_id(self) -> str:
        """Return a unique ID to use for this entity."""
        return f"{self.config_entry.entry_id}-climate-{self.pnc_id}"

    def _reported(self) -> dict[str, Any]:
        """Return the reported state, or nothing before the first status arrives."""
        if getattr(self, "appliance_status", None) is None:
            return {}
        return self.reported_state

    def _values(self, capability: str) -> list[str]:
        """Return the values the appliance lists for one absorbed capability, minus disabled ones."""
        values = (self.capability.get(capability) or {}).get("values", {})
        return [raw for raw, definition in values.items() if not (definition or {}).get("disabled")]

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return off plus the modes the appliance offers."""
        offered = self._values("mode")
        return [HVACMode.OFF, *(mode for raw, mode in AC_HVAC_MODES.items() if raw in offered)]

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return off while the appliance is off, its mode otherwise."""
        reported = self._reported()
        if not reported:
            return None
        if not self._is_on(reported):
            return HVACMode.OFF
        return AC_HVAC_MODES.get(reported.get("mode"))

    def _self_drying(self, reported: dict[str, Any]) -> bool:
        # Only where the appliance drives the attribute (read only, like the YI12F): a model that
        # lets the user switch it on must keep reading its real mode.
        attr, value = AC_SELF_DRYING
        return self._drying_capability.get("access") == "read" and reported.get(attr) == value

    def _is_on(self, reported: dict[str, Any]) -> bool:
        return bool(reported) and reported.get("applianceState") != "OFF" and not self._self_drying(reported)

    def _temperature_locked(self, reported: dict[str, Any]) -> bool:
        return self._is_on(reported) and any(reported.get(attr) == value for attr, value in AC_TEMPERATURE_LOCKS.items())

    def _airflow_locked(self, reported: dict[str, Any]) -> bool:
        return self._is_on(reported) and any(reported.get(attr) == "ON" for attr in AC_AIRFLOW_LOCKS)

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return drying while the appliance dries itself after being switched off."""
        return HVACAction.DRYING if self._self_drying(self._reported()) else None

    @property
    def current_temperature(self) -> float | None:
        """Return the room temperature."""
        return self._reported().get("ambientTemperatureC")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature, or None while the running mode ignores it."""
        reported = self._reported()
        if self._temperature_locked(reported):
            return None
        return reported.get("targetTemperatureC")

    def _temperature_limit(self, key: str, default: float) -> float:
        return float((self.capability.get("targetTemperatureC") or {}).get(key, default))

    @property
    def min_temp(self) -> float:
        """Return the lowest target the appliance accepts."""
        return self._temperature_limit("min", 16)

    @property
    def max_temp(self) -> float:
        """Return the highest target the appliance accepts."""
        return self._temperature_limit("max", 30)

    @property
    def target_temperature_step(self) -> float:
        """Return the target temperature step."""
        return self._temperature_limit("step", 1)

    @property
    def fan_modes(self) -> list[str] | None:
        """Return the fan speeds the appliance offers."""
        offered = self._values("fanSpeedSetting")
        return [fan for raw, fan in AC_FAN_MODES.items() if raw in offered] or None

    @property
    def fan_mode(self) -> str | None:
        """Return the fan speed, or None while a preset drives the airflow."""
        reported = self._reported()
        if self._airflow_locked(reported):
            return None
        return AC_FAN_MODES.get(reported.get("fanSpeedSetting"))

    @property
    def swing_modes(self) -> list[str] | None:
        """Return oscillate plus one fixed position per flapPosition value, or off without them."""
        positions = [f"position_{match.group(1)}" for raw in self._values("flapPosition") if (match := _POSITION.match(raw))]
        modes = []
        if "flapOscillate" in self.capability:
            modes.append(AC_SWING_OSCILLATE)
            if not positions:
                modes.append(AC_SWING_STOPPED)
        return [*modes, *positions] or None

    @property
    def swing_mode(self) -> str | None:
        """Return on while oscillating, the fixed position otherwise, None while a preset drives it."""
        reported = self._reported()
        if self._airflow_locked(reported):
            return None
        if reported.get("flapOscillate") == "ON":
            return AC_SWING_OSCILLATE
        if AC_SWING_STOPPED in (self.swing_modes or []):
            return AC_SWING_STOPPED if reported.get("flapOscillate") == "OFF" else None
        position = reported.get("flapPosition")
        # Reported as an integer on the YI12F, as POSITION_N in the capability.
        if isinstance(position, int) or (isinstance(position, str) and position.isdigit()):
            mode = f"position_{int(position)}"
        elif isinstance(position, str) and (match := _POSITION.match(position)):
            mode = f"position_{match.group(1)}"
        else:
            return None
        return mode if mode in (self.swing_modes or []) else None

    @property
    def preset_modes(self) -> list[str] | None:
        """Return none plus the presets the appliance has."""
        presets = [preset for preset, attr in AC_PRESETS.items() if attr in self.capability]
        return [PRESET_NONE, *presets] if presets else None

    @property
    def preset_mode(self) -> str | None:
        """Return the first preset that is ON, or none."""
        reported = self._reported()
        if not self.preset_modes or not reported:
            return None
        for preset, attr in AC_PRESETS.items():
            if attr in self.capability and reported.get(attr) == "ON":
                return preset
        return PRESET_NONE

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Offer what the appliance has.

        The features follow the capabilities, not the state: Home Assistant refuses a call whose
        feature is missing, and a scene that sets cool and then a temperature would otherwise be
        refused while the AC still reports fan only. A locked setting reads None instead.
        """
        features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if "targetTemperatureC" in self.capability:
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self.fan_modes:
            features |= ClimateEntityFeature.FAN_MODE
        if self.swing_modes:
            features |= ClimateEntityFeature.SWING_MODE
        if self.preset_modes:
            features |= ClimateEntityFeature.PRESET_MODE
        return features

    async def _send(self, command: dict[str, Any]) -> None:
        """Send one root level command to the appliance."""
        _LOGGER.debug("Electrolux climate command %s", command)
        result = await self.api.execute_appliance_command(self.pnc_id, command)
        _LOGGER.debug("Electrolux climate command result %s", result)

    async def async_turn_on(self) -> None:
        """Turn the appliance on in its last mode."""
        await self._send({"executeCommand": "ON"})

    async def async_turn_off(self) -> None:
        """Turn the appliance off."""
        await self._send({"executeCommand": "OFF"})

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Turn off, or switch mode, turning the appliance on first when it is off."""
        if hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
            return
        # Home Assistant checks the mode for climate.set_hvac_mode but not when it rides along with
        # climate.set_temperature.
        if hvac_mode not in self.hvac_modes:
            raise ServiceValidationError(
                translation_domain="climate",
                translation_key="not_valid_hvac_mode",
                translation_placeholders={"mode": hvac_mode, "modes": ", ".join(self.hvac_modes)},
            )
        raw = next(raw for raw, mode in AC_HVAC_MODES.items() if mode == hvac_mode)
        if self.hvac_mode == HVACMode.OFF:
            await self.async_turn_on()
        await self._send({"mode": raw})

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature, and the mode when the call carries one."""
        if (hvac_mode := kwargs.get(ATTR_HVAC_MODE)) is not None:
            await self.async_set_hvac_mode(hvac_mode)
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._send({"targetTemperatureC": float(temperature)})

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan speed."""
        raw = next(raw for raw, fan in AC_FAN_MODES.items() if fan == fan_mode)
        await self._send({"fanSpeedSetting": raw})

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Oscillate, or stop the flap at a fixed position."""
        if swing_mode == AC_SWING_OSCILLATE:
            await self._send({"flapOscillate": "ON"})
            return
        if swing_mode == AC_SWING_STOPPED:
            await self._send({"flapOscillate": "OFF"})
            return
        command: dict[str, Any] = {"flapOscillate": "OFF"} if "flapOscillate" in self.capability else {}
        command["flapPosition"] = int(swing_mode.rsplit("_", 1)[1])
        await self._send(command)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Turn the chosen preset on and the others off, or all off for none."""
        await self._send(
            {attr: "ON" if preset == preset_mode else "OFF" for preset, attr in AC_PRESETS.items() if attr in self.capability}
        )
