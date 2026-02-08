"""Number platform for Electrolux Status."""

import logging
from typing import cast

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NUMBER
from .entity import ElectroluxEntity
from .util import (
    ElectroluxApiClient,
    format_command_for_appliance,
    map_command_error_to_home_assistant_error,
    time_minutes_to_seconds,
    time_seconds_to_minutes,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    if appliances := coordinator.data.get("appliances", None):
        for appliance_id, appliance in appliances.appliances.items():
            entities = [
                entity for entity in appliance.entities if entity.entity_type == NUMBER
            ]
            _LOGGER.debug(
                "Electrolux add %d NUMBER entities to registry for appliance %s",
                len(entities),
                appliance_id,
            )
            async_add_entities(entities)


class ElectroluxNumber(ElectroluxEntity, NumberEntity):
    """Electrolux Status number class."""

    @property
    def entity_domain(self) -> str:
        """Entity domain for the entry. Used for consistent entity_id."""
        return NUMBER

    @property
    def mode(self) -> str:
        """Return the mode for the number entity (slider for better UX)."""
        return "slider"

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        if self.unit == UnitOfTime.SECONDS:
            value = time_seconds_to_minutes(self.extract_value())
        else:
            value = self.extract_value()

        if not value:
            value = self.capability.get("default", None)
            if value == "INVALID_OR_NOT_SET_TIME":
                value = self.capability.get("min", None)
        if not value:
            return self._cached_value
        if isinstance(self.unit, UnitOfTemperature):
            value = round(value, 2)
        elif isinstance(self.unit, UnitOfTime):
            # Electrolux bug - prevent negative/disabled timers
            value = max(value, 0)
        self._cached_value = value
        return value

    @property
    def native_max_value(self) -> float:
        """Return the max value."""
        # Check current program for program-specific constraints
        current_program = self.reported_state.get("program")

        if (
            current_program
            and hasattr(self.get_appliance, "data")
            and self.get_appliance.data
        ):
            appliance_data = self.get_appliance.data
            if hasattr(appliance_data, "capabilities") and appliance_data.capabilities:
                # Use normalized entity key to match program capabilities
                entity_key = self.entity_attr.lower().replace("fppn_", "").strip("_")
                program_caps = (
                    appliance_data.capabilities.get("program", {})
                    .get("values", {})
                    .get(current_program, {})
                    .get(entity_key, {})
                )
                if "max" in program_caps:
                    max_val = program_caps["max"]
                    if max_val is not None:
                        if self.unit == UnitOfTime.SECONDS:
                            max_val = time_seconds_to_minutes(cast(float, max_val))
                        return float(cast(float, max_val))

        # Fallback to global capability
        if self.unit == UnitOfTime.SECONDS:
            max_val = time_seconds_to_minutes(self.capability.get("max", 100))
            return float(max_val) if max_val is not None else 100.0
        if self.unit == UnitOfTemperature.CELSIUS:
            return float(self.capability.get("max", 300))
        return float(self.capability.get("max", 100))

    @property
    def native_min_value(self) -> float:
        """Return the min value."""
        # Check current program for program-specific constraints
        current_program = self.reported_state.get("program")

        if (
            current_program
            and hasattr(self.get_appliance, "data")
            and self.get_appliance.data
        ):
            appliance_data = self.get_appliance.data
            if hasattr(appliance_data, "capabilities") and appliance_data.capabilities:
                # Use normalized entity key to match program capabilities
                entity_key = self.entity_attr.lower().replace("fppn_", "").strip("_")
                program_caps = (
                    appliance_data.capabilities.get("program", {})
                    .get("values", {})
                    .get(current_program, {})
                    .get(entity_key, {})
                )
                if "min" in program_caps:
                    min_val = program_caps["min"]
                    if min_val is not None:
                        if self.unit == UnitOfTime.SECONDS:
                            min_val = time_seconds_to_minutes(cast(float, min_val))
                        return float(cast(float, min_val))

        # Fallback to global capability
        if self.unit == UnitOfTime.SECONDS:
            min_val = time_seconds_to_minutes(self.capability.get("min", 0))
            return float(min_val) if min_val is not None else 0.0
        return float(self.capability.get("min", 0))

    @property
    def native_step(self) -> float:
        """Return the step value."""
        # Check current program for program-specific constraints
        current_program = self.reported_state.get("program")

        if (
            current_program
            and hasattr(self.get_appliance, "data")
            and self.get_appliance.data
        ):
            appliance_data = self.get_appliance.data
            if hasattr(appliance_data, "capabilities") and appliance_data.capabilities:
                # Use normalized entity key to match program capabilities
                entity_key = self.entity_attr.lower().replace("fppn_", "").strip("_")
                program_caps = (
                    appliance_data.capabilities.get("program", {})
                    .get("values", {})
                    .get(current_program, {})
                    .get(entity_key, {})
                )
                if "step" in program_caps:
                    step_val = program_caps["step"]
                    if step_val is not None:
                        if self.unit == UnitOfTime.SECONDS:
                            step_val = time_seconds_to_minutes(cast(float, step_val))
                        return float(cast(float, step_val))

        # Fallback to global capability
        if self.unit == UnitOfTime.SECONDS:
            step_val = time_seconds_to_minutes(self.capability.get("step", 1))
            return float(step_val) if step_val is not None else 1.0
        if self.unit == UnitOfTemperature.CELSIUS:
            return float(self.capability.get("step", 1))
        return float(self.capability.get("step", 1))

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # Check if remote control is enabled
        remote_control = (
            self.appliance_status.get("properties", {})
            .get("reported", {})
            .get("remoteControl")
        )
        if remote_control is not None and "ENABLED" not in str(remote_control):
            _LOGGER.warning(
                "Cannot set %s for appliance %s: remote control is %s",
                self.entity_attr,
                self.pnc_id,
                remote_control,
            )
            raise HomeAssistantError(
                f"Remote control disabled (status: {remote_control})"
            )

        if self.unit == UnitOfTime.SECONDS:
            converted = time_minutes_to_seconds(value)
            value = float(converted) if converted is not None else value
        if self.capability.get("step", 1) == 1:
            value = int(value)

        client: ElectroluxApiClient = self.api

        # Format the value according to appliance capabilities
        formatted_value = format_command_for_appliance(
            self.capability, self.entity_attr, value
        )

        # --- START OF OUR FIX ---
        command = {}
        if self.entity_source == "latamUserSelections":
            _LOGGER.debug(
                "Electrolux: Detected latamUserSelections, building full command."
            )
            # Get the current state of all latam selections
            current_selections = (
                self.appliance_status.get("properties", {})
                .get("reported", {})
                .get("latamUserSelections", {})
            )
            if not current_selections:
                _LOGGER.error(
                    "Could not retrieve current latamUserSelections to build command."
                )
                return

            # Create a copy to modify
            new_selections = current_selections.copy()
            # Update only the value we want to change
            new_selections[self.entity_attr] = formatted_value
            # Assemble the final command with the entire block
            command = {"latamUserSelections": new_selections}
        # --- END OF OUR FIX ---

        # Original logic as a fallback for other entities
        elif self.entity_source == "userSelections":
            command = {
                self.entity_source: {
                    "programUID": self.appliance_status["properties"]["reported"][
                        "userSelections"
                    ]["programUID"],
                    self.entity_attr: formatted_value,
                },
            }
        elif self.entity_source:
            command = {self.entity_source: {self.entity_attr: formatted_value}}
        else:
            command = {self.entity_attr: formatted_value}

        _LOGGER.debug("Electrolux set value %s", command)
        try:
            result = await client.execute_appliance_command(self.pnc_id, command)
        except Exception as ex:
            error_msg = str(ex).lower()
            if "command_validation_error" in error_msg:
                # Try wrapping in userSelections as a generic fallback for command validation errors
                _LOGGER.debug(
                    "Trying %s command with userSelections wrapper",
                    self.entity_attr,
                )
                try:
                    fallback_command = {
                        "userSelections": {
                            self.entity_attr: formatted_value,
                        },
                    }
                    result = await client.execute_appliance_command(
                        self.pnc_id, fallback_command
                    )
                    _LOGGER.debug(
                        "Electrolux %s fallback command succeeded", self.entity_attr
                    )
                except Exception as fallback_ex:
                    # Use shared error mapping for fallback errors
                    raise map_command_error_to_home_assistant_error(
                        fallback_ex, self.entity_attr, _LOGGER
                    ) from fallback_ex
            else:
                # Use shared error mapping for other errors
                raise map_command_error_to_home_assistant_error(
                    ex, self.entity_attr, _LOGGER
                ) from ex
        _LOGGER.debug("Electrolux set value result %s", result)
        await self.coordinator.async_request_refresh()

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if self.unit == UnitOfTime.SECONDS:
            return UnitOfTime.MINUTES
        return self.unit

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        # Check if this entity is supported by the current program
        current_program = self.reported_state.get("program")
        if (
            current_program
            and hasattr(self.get_appliance, "data")
            and self.get_appliance.data
        ):
            appliance_data = self.get_appliance.data
            if hasattr(appliance_data, "capabilities") and appliance_data.capabilities:
                program_capabilities = (
                    appliance_data.capabilities.get("program", {})
                    .get("values", {})
                    .get(current_program, {})
                )
                if program_capabilities:
                    # Check if this entity attribute is supported in the current program
                    entity_key = (
                        self.entity_attr.lower().replace("fppn_", "").strip("_")
                    )
                    return entity_key in program_capabilities
        # Fall back to global capabilities if no program-specific data
        return super().entity_registry_enabled_default
