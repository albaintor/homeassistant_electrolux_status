"""Utlities for the Electrolux Status platform."""

import asyncio
import base64
import logging
import math
import re
from typing import Any

from electrolux_group_developer_sdk.auth.token_manager import TokenManager
from electrolux_group_developer_sdk.client.appliance_client import ApplianceClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_NOTIFICATION_DEFAULT,
    CONF_NOTIFICATION_DIAG,
    CONF_NOTIFICATION_WARNING,
    NAME,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


class CommandError(Exception):
    """Base exception for command errors."""

    pass


class RemoteControlDisabledError(CommandError):
    """Remote control is disabled."""

    pass


class ApplianceOfflineError(CommandError):
    """Appliance is disconnected."""

    pass


class CommandValidationError(CommandError):
    """Command validation failed."""

    pass


class RateLimitError(CommandError):
    """Rate limit exceeded."""

    pass


class AuthenticationError(CommandError):
    """Authentication failed - tokens expired or invalid."""

    pass


def get_electrolux_session(
    api_key, access_token, refresh_token, client_session, hass=None
) -> "ElectroluxApiClient":
    """Return Electrolux API Session.

    Note: client_session is currently unused by the underlying SDK but is kept
    for future compatibility when the SDK supports passing in a shared aiohttp session.
    """
    return ElectroluxApiClient(api_key, access_token, refresh_token, hass)


def should_send_notification(config_entry, alert_severity, alert_status) -> bool:
    """Determine if the notification should be sent based on severity and config."""
    if alert_status == "NOT_NEEDED":
        return False
    if alert_severity == "DIAGNOSTIC":
        return config_entry.data.get(CONF_NOTIFICATION_DIAG, False)
    elif alert_severity == "WARNING":
        return config_entry.data.get(CONF_NOTIFICATION_WARNING, False)
    else:
        return config_entry.data.get(CONF_NOTIFICATION_DEFAULT, True)


def create_notification(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    alert_name: str,
    alert_severity: str,
    alert_status: str,
    title: str = NAME,
):
    """Create a notification."""

    message = (
        f"Alert: {alert_name}</br>Severity: {alert_severity}</br>Status: {alert_status}"
    )

    if should_send_notification(config_entry, alert_severity, alert_status) is False:
        _LOGGER.debug(
            "Discarding notification.\nTitle: %s\nMessage: %s",
            title,
            message,
        )
        return

    # Convert the string to base64 - this prevents the same alert being spammed
    input_string = f"{title}-{message}"
    bytes_string = input_string.encode("utf-8")
    base64_bytes = base64.b64encode(bytes_string)
    base64_string = base64_bytes.decode("utf-8")

    # send notification with crafted notification id so we dont spam notifications
    _LOGGER.debug(
        "Sending notification.\nTitle: %s\nMessage: %s",
        title,
        message,
    )
    hass.async_create_task(
        hass.services.async_call(
            "persistent_notification",
            "create",
            {"message": message, "title": title, "notification_id": base64_string},
        )
    )


def time_seconds_to_minutes(seconds: float | None) -> int | None:
    """Convert seconds to minutes."""
    if seconds is None:
        return None
    if seconds == -1:
        return -1
    return int(math.ceil(int(seconds) / 60))


def time_minutes_to_seconds(minutes: float | None) -> int | None:
    """Convert minutes to seconds."""
    if minutes is None:
        return None
    if minutes == -1:
        return -1
    return int(minutes) * 60


def string_to_boolean(value: str | None, fallback=True) -> bool | str | None:
    """Convert a string input to boolean."""
    if value is None:
        return None

    on_values = {
        "charging",
        "connected",
        "detected",
        "enabled",
        "home",
        "hot",
        "light",
        "locked",
        "locking",
        "motion",
        "moving",
        "occupied",
        "on",
        "open",
        "plugged",
        "power",
        "problem",
        "running",
        "smoke",
        "sound",
        "tampering",
        "true",
        "unsafe",
        "update available",
        "vibration",
        "wet",
        "yes",
    }

    off_values = {
        "away",
        "clear",
        "closed",
        "disabled",
        "disconnected",
        "dry",
        "false",
        "no",
        "no light",
        "no motion",
        "no power",
        "no problem",
        "no smoke",
        "no sound",
        "no tampering",
        "no vibration",
        "normal",
        "not charging",
        "not occupied",
        "not running",
        "off",
        "safe",
        "stopped",
        "unlocked",
        "unlocking",
        "unplugged",
        "up-to-date",
    }

    normalize_input = re.sub(r"\s+", " ", value.replace("_", " ").strip().lower())

    if normalize_input in on_values:
        return True
    if normalize_input in off_values:
        return False
    _LOGGER.debug("Electrolux unable to convert value to boolean")
    if fallback:
        return value
    return False


async def execute_command_with_error_handling(
    client: "ElectroluxApiClient",
    pnc_id: str,
    command: dict[str, Any],
    entity_attr: str,
    logger: logging.Logger,
    capability: dict[str, Any] | None = None,
) -> Any:
    """Execute command with standardized error handling.

    Args:
        client: API client instance
        pnc_id: Appliance ID
        command: Command dictionary to send
        entity_attr: Entity attribute name (for logging)
        logger: Logger instance

    Returns:
        Command result

    Raises:
        HomeAssistantError: With user-friendly message
    """
    logger.debug("Executing command for %s: %s", entity_attr, command)

    try:
        result = await client.execute_appliance_command(pnc_id, command)
        logger.debug("Command succeeded for %s: %s", entity_attr, result)
        return result

    except Exception as ex:
        # Use shared error mapping function
        raise map_command_error_to_home_assistant_error(
            ex, entity_attr, logger, capability
        ) from ex


def map_command_error_to_home_assistant_error(
    ex: Exception,
    entity_attr: str,
    logger: logging.Logger,
    capability: dict[str, Any] | None = None,
) -> HomeAssistantError:
    """Map command exceptions to user-friendly Home Assistant errors.

    Uses multiple detection methods for robustness:
    1. Structured error response parsing
    2. HTTP status code detection
    3. Improved string pattern matching

    Args:
        ex: The original exception
        entity_attr: Entity attribute name (for logging)
        logger: Logger instance

    Returns:
        HomeAssistantError with user-friendly message
    """

    # Check for authentication errors first - these should be handled differently
    error_str = str(ex).lower()
    if any(
        keyword in error_str
        for keyword in [
            "401",
            "unauthorized",
            "forbidden",
            "invalid grant",
            "token",
            "auth",
        ]
    ):
        logger.warning(
            "Authentication error detected for %s: %s",
            entity_attr,
            ex,
        )
        raise AuthenticationError("Authentication failed") from ex

    # Method 1: Try to parse structured error response
    error_data = None
    try:
        # Check if exception has response data
        if hasattr(ex, "response") and getattr(ex, "response", None):
            response = getattr(ex, "response")
            if hasattr(response, "json") and callable(getattr(response, "json", None)):
                try:
                    error_data = response.json()
                except Exception:
                    pass
            elif hasattr(response, "text"):
                try:
                    import json

                    error_data = json.loads(response.text)
                except Exception:
                    pass
        # Check if exception has direct error data
        elif hasattr(ex, "error_data"):
            error_data = getattr(ex, "error_data")
        elif hasattr(ex, "details"):
            error_data = getattr(ex, "details")
    except Exception:
        # Parsing failed, continue to other methods
        pass

    # If we got structured error data, use it
    if error_data and isinstance(error_data, dict):
        error_code = (
            error_data.get("code")
            or error_data.get("error_code")
            or error_data.get("error")
            or error_data.get("status")
        )

        # Map error codes to user-friendly messages
        ERROR_CODE_MAPPING = {
            "REMOTE_CONTROL_DISABLED": "Remote control is disabled for this appliance. Please enable it on the appliance's control panel.",
            "RC_DISABLED": "Remote control is disabled for this appliance. Please enable it on the appliance's control panel.",
            "REMOTE_CONTROL_NOT_ACTIVE": "Remote control is disabled for this appliance. Please enable it on the appliance's control panel.",
            "APPLIANCE_OFFLINE": "Appliance is disconnected or not available. Check the appliance's network connection.",
            "DEVICE_OFFLINE": "Appliance is disconnected or not available. Check the appliance's network connection.",
            "CONNECTION_LOST": "Appliance is disconnected or not available. Check the appliance's network connection.",
            "RATE_LIMIT_EXCEEDED": "Too many commands sent. Please wait a moment and try again.",
            "RATE_LIMIT": "Too many commands sent. Please wait a moment and try again.",
            "TOO_MANY_REQUESTS": "Too many commands sent. Please wait a moment and try again.",
            "COMMAND_VALIDATION_ERROR": "Command not accepted by appliance. Check that the appliance supports this operation.",
            "VALIDATION_ERROR": "Command not accepted by appliance. Check that the appliance supports this operation.",
            "INVALID_COMMAND": "Command not accepted by appliance. Check that the appliance supports this operation.",
        }

        if error_code and str(error_code).upper() in ERROR_CODE_MAPPING:
            user_message = ERROR_CODE_MAPPING[str(error_code).upper()]
            logger.warning(
                "Command failed for %s: %s - %s",
                entity_attr,
                error_code,
                ex,
            )
            return HomeAssistantError(user_message)

    # Check for Type mismatch errors specifically (prevent false positive remote control errors)
    error_str = str(ex).lower()
    if "type mismatch" in error_str:
        logger.warning(
            "Command failed for %s: type mismatch - %s",
            entity_attr,
            ex,
        )
        return HomeAssistantError(
            f"Integration Error: Data type mismatch for {entity_attr}. Expected Boolean."
        )

    # Method 2: Check HTTP status codes
    status_code = None
    try:
        status_code = getattr(ex, "status", None)
        if not status_code and hasattr(ex, "response"):
            response = getattr(ex, "response")
            status_code = getattr(response, "status", None)
        if not status_code and hasattr(ex, "status_code"):
            status_code = getattr(ex, "status_code")
    except Exception:
        pass

    if status_code:
        STATUS_CODE_MAPPING = {
            403: "Remote control is disabled for this appliance. Please enable it on the appliance's control panel.",
            406: "Command not accepted by appliance. Check that the appliance supports this operation.",
            429: "Too many commands sent. Please wait a moment and try again.",
            503: "Appliance is disconnected or not available. Check the appliance's network connection.",
        }

        if status_code in STATUS_CODE_MAPPING:
            user_message = STATUS_CODE_MAPPING[status_code]

            # Enhanced 406 error handling with detail parsing
            if status_code == 406:
                detail_message = None
                try:
                    # Try to extract detail from error response
                    if error_data and isinstance(error_data, dict):
                        detail = error_data.get("detail") or error_data.get("message")
                        if detail:
                            detail_lower = str(detail).lower()

                            if "invalid step" in detail_lower:
                                # Get step value from capability for dynamic error message
                                step_value = "valid"
                                if capability:
                                    step = capability.get("step")
                                    if step is not None:
                                        step_value = str(step)
                                detail_message = f"Invalid Value: This appliance requires increments of {step_value}."

                            elif "type mismatch" in detail_lower:
                                detail_message = "Integration Error: Formatting mismatch (Expected Boolean/String)."

                            elif (
                                "temporary_locked" in detail_lower
                                or "temporary lock" in detail_lower
                            ):
                                detail_message = "Remote control is temporarily locked. Please open and close the appliance door, then press the physical 'Remote Start' button on the appliance."

                except Exception:
                    # If detail parsing fails, continue with generic message
                    pass

                if detail_message:
                    user_message = detail_message

            logger.warning(
                "Command failed for %s: HTTP %d - %s",
                entity_attr,
                status_code,
                ex,
            )
            return HomeAssistantError(user_message)

    # Method 3: Improved string pattern matching (fallback)
    error_msg = str(ex).lower()

    # More comprehensive pattern matching
    if any(
        phrase in error_msg
        for phrase in [
            "remote control disabled",
            "remote control is disabled",
            "remote control not active",
            "remote control off",
            "rc disabled",
            "rc not active",
        ]
    ):
        logger.warning(
            "Command failed for %s: remote control disabled - %s",
            entity_attr,
            ex,
        )
        return HomeAssistantError(
            "Remote control is disabled for this appliance. "
            "Please enable it on the appliance's control panel."
        )

    elif any(
        phrase in error_msg
        for phrase in [
            "disconnected",
            "offline",
            "not available",
            "connection lost",
            "device offline",
            "appliance offline",
        ]
    ):
        logger.warning(
            "Command failed for %s: appliance offline - %s",
            entity_attr,
            ex,
        )
        return HomeAssistantError(
            "Appliance is disconnected or not available. "
            "Check the appliance's network connection."
        )

    elif any(
        phrase in error_msg
        for phrase in [
            "rate limit",
            "too many requests",
            "rate exceeded",
            "throttled",
            "429",
        ]
    ):
        logger.warning(
            "Command failed for %s: rate limited - %s",
            entity_attr,
            ex,
        )
        return HomeAssistantError(
            "Too many commands sent. Please wait a moment and try again."
        )

    elif any(
        phrase in error_msg
        for phrase in [
            "command validation",
            "validation error",
            "invalid command",
            "not acceptable",
            "406",
        ]
    ):
        logger.warning(
            "Command failed for %s: command validation error - %s",
            entity_attr,
            ex,
        )
        return HomeAssistantError(
            "Command not accepted by appliance. Check that the appliance supports this operation."
        )

    # Default: Generic error
    logger.error(
        "Command failed for %s with unexpected error: %s",
        entity_attr,
        ex,
    )
    return HomeAssistantError(f"Command failed: {ex}. Check logs for details.")


def get_capability(capabilities: dict[str, Any], key: str) -> Any:
    """Safely get a capability value, handling both dict and direct value formats.

    For constant capabilities, returns the 'default' value if the capability is a dict.
    For other capabilities, returns the value directly.

    Args:
        capabilities: The capabilities dictionary
        key: The capability key to look up

    Returns:
        The capability value, or None if not found
    """
    if key not in capabilities:
        return None

    value = capabilities[key]
    if isinstance(value, dict):
        # For dict capabilities (like constants), return the default value
        return value.get("default")
    else:
        # For direct value capabilities, return the value as-is
        return value


def format_command_for_appliance(
    capability: dict[str, Any], attr: str, value: Any
) -> Any:
    """Format a command value according to the appliance capability specifications.

    This function dynamically formats Home Assistant command values to match
    the expected format for the Electrolux appliance based on capability metadata.

    Args:
        capability: The capability definition for the attribute
        attr: The attribute name (e.g., 'cavityLight', 'targetTemperatureC')
        value: The raw value from Home Assistant

    Returns:
        The formatted value ready for the appliance API
    """
    if not capability or not isinstance(capability, dict):
        # Fallback to original behavior if no capability info
        if isinstance(value, bool):
            return "ON" if value else "OFF"
        return value

    # Get the capability type
    cap_type = capability.get("type", "").lower()

    if cap_type == "boolean":
        # Boolean type - return raw Python bool
        if isinstance(value, bool):
            return value
        # Handle string representations
        if isinstance(value, str):
            return value.lower() in ("true", "on", "1", "yes")
        # Handle numeric representations
        return bool(value)

    elif "temperature" in attr.lower() or cap_type in ("number", "float", "integer"):
        # Temperature or numeric type - ensure float and apply step constraints for safety
        try:
            numeric_value = float(value)

            # Apply step constraints as safety measure (sliders should prevent invalid values, but this handles edge cases)
            step = capability.get("step")
            if step is not None:
                step = float(step)
                if step > 0:
                    # For sliders, we still want to ensure step compliance
                    # Calculate from a reasonable minimum (0 for most cases)
                    min_val = capability.get("min", 0)
                    steps_from_min = (numeric_value - min_val) / step
                    # Round to nearest valid step
                    numeric_value = min_val + round(steps_from_min) * step

            return numeric_value

        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid numeric value %s for attribute %s, using as-is", value, attr
            )
            return value

    elif cap_type in ("string", "enum") or "values" in capability:
        # String or enum type - validate against allowed values
        values_dict = capability.get("values", {})

        if isinstance(values_dict, dict) and values_dict:
            # Check if the value is a valid key in the values dict
            if str(value) in values_dict:
                return str(value)
            else:
                # Try to find a matching value by case-insensitive comparison
                value_str = str(value).lower()
                for key in values_dict.keys():
                    if key.lower() == value_str:
                        return key

                _LOGGER.warning(
                    "Value %s not found in allowed values for %s: %s",
                    value,
                    attr,
                    list(values_dict.keys()),
                )
                # Return the original value if not found - let the API handle validation
                return value
        else:
            # No values constraint, return as string
            return str(value)

    else:
        # Unknown or unspecified type - use fallback logic
        if isinstance(value, bool):
            return "ON" if value else "OFF"
        return value


class ElectroluxApiClient:
    """Wrapper for the new Electrolux API client to maintain compatibility."""

    def __init__(self, api_key: str, access_token: str, refresh_token: str, hass=None):
        """Initialize the API client."""
        self.hass = hass
        self._token_manager = TokenManager(access_token, refresh_token, api_key)
        self._client = ApplianceClient(self._token_manager)

    async def get_appliances_list(self):
        """Get list of appliances."""
        appliances = await self._client.get_appliances()
        # Convert to the expected format
        result = []
        for appliance in appliances:
            # Try to extract model from PNC (Product Number Code)
            pnc = appliance.applianceId
            model_name = getattr(appliance, "model", "Unknown")
            if model_name == "Unknown" and pnc:
                # Extract model from PNC format like '944188772_00:31862190-443E07363DAB'
                pnc_parts = pnc.split("_")
                if len(pnc_parts) > 0:
                    model_part = pnc_parts[0]
                    # Use the first part as model if it looks like a model number
                    if model_part.isdigit() and len(model_part) >= 6:
                        model_name = model_part

            appliance_data = {
                "applianceId": appliance.applianceId,
                "applianceName": appliance.applianceName,
                "applianceType": appliance.applianceType,
                "connectionState": "connected",  # Assume connected
                "applianceData": {
                    "applianceName": appliance.applianceName,
                    "modelName": model_name,
                },
                "created": "2022-01-01T00:00:00.000Z",  # Mock creation date
            }
            _LOGGER.debug("API appliance list item processed")
            result.append(appliance_data)
        return result

    async def get_appliances_info(self, appliance_ids):
        """Get appliances info."""
        result = []
        for appliance_id in appliance_ids:
            try:
                details = await self._client.get_appliance_details(appliance_id)
                # Try to extract model from PNC if API doesn't provide it
                # Note: Electrolux API often returns "Unknown" for model, but the PNC
                # contains the actual product code (e.g., "944188772") which is the most
                # specific model identifier available through the API
                model = getattr(details, "model", "Unknown")
                if model == "Unknown" and appliance_id:
                    # Extract model from PNC format like '944188772_00:31862190-443E07363DAB'
                    pnc_parts = appliance_id.split("_")
                    if len(pnc_parts) > 0:
                        model_part = pnc_parts[0]
                        # Use the first part as model if it looks like a model number
                        if model_part.isdigit() and len(model_part) >= 6:
                            model = model_part

                # Convert to expected format
                info = {
                    "pnc": appliance_id,
                    "brand": getattr(details, "brand", "Electrolux"),
                    "model": model,
                    "device_type": getattr(details, "deviceType", "Unknown"),
                    "variant": getattr(details, "variant", "Unknown"),
                    "color": getattr(details, "color", "Unknown"),
                }
                _LOGGER.debug("API appliance details retrieved for %s", appliance_id)
                result.append(info)
            except Exception as e:
                _LOGGER.warning(
                    "Failed to get info for appliance %s: %s", appliance_id, e
                )
        return result

    async def get_appliance_state(self, appliance_id) -> dict[str, Any]:
        """Get appliance state."""
        state = await self._client.get_appliance_state(appliance_id)
        # Convert to expected format
        return {
            "applianceId": appliance_id,
            "connectionState": "connected",
            "status": "enabled",
            "properties": {
                "reported": (
                    state.properties.get("reported", {}) if state.properties else {}
                )
            },
        }

    async def get_appliance_capabilities(self, appliance_id):
        """Get appliance capabilities."""
        details = await self._client.get_appliance_details(appliance_id)
        return details.capabilities

    async def watch_for_appliance_state_updates(self, appliance_ids, callback):
        """Watch for state updates using Server-Sent Events (SSE)."""
        try:
            # Add listeners for each appliance
            for appliance_id in appliance_ids:
                self._client.add_listener(appliance_id, callback)
                _LOGGER.debug("Added SSE listener for appliance %s", appliance_id)

            # Start the event stream as a background task (it runs indefinitely)
            if self.hass:
                self._sse_task = self.hass.async_create_task(
                    self._client.start_event_stream()
                )
            else:
                self._sse_task = asyncio.create_task(self._client.start_event_stream())
            _LOGGER.debug(
                "Started SSE event stream for %d appliances", len(appliance_ids)
            )

        except Exception as e:
            _LOGGER.error("Failed to start SSE event stream: %s", e)
            raise

    async def disconnect_websocket(self):
        """Disconnect SSE event stream."""
        try:
            if hasattr(self, "_sse_task") and self._sse_task:
                self._sse_task.cancel()
                try:
                    await self._sse_task
                except asyncio.CancelledError:
                    _LOGGER.debug(
                        "Electrolux SSE task was cancelled during disconnect, as expected"
                    )
                self._sse_task = None
            _LOGGER.debug("SSE disconnect completed")
        except Exception as e:
            _LOGGER.error("Error during SSE disconnect: %s", e)

    async def get_user_metadata(self):
        """Get user metadata - compatibility method."""
        # Return mock metadata since the new API doesn't expose this
        return {"userId": "mock_user"}

    async def execute_appliance_command(self, appliance_id, command):
        """Execute a command on an appliance."""
        # The new API should have a method to send commands
        # For now, try to call execute_command if it exists
        try:
            # Try different possible method names
            execute_method = getattr(self._client, "execute_command", None)
            if execute_method:
                return await execute_method(appliance_id, command)
            send_method = getattr(self._client, "send_command", None)
            if send_method:
                return await send_method(appliance_id, command)
            else:
                raise AttributeError("No command execution method found")
        except AttributeError:
            # If the method doesn't exist, raise an exception
            _LOGGER.error(
                "execute_command method not found in new API - command execution not supported"
            )
            raise NotImplementedError(
                "Command execution is not supported by the current API implementation"
            )
        except Exception:
            # Re-raise all exceptions to be handled by the calling entity
            raise

    async def close(self):
        """Close the client."""
        # The new SDK doesn't have a close method, but TokenManager might need cleanup
        pass
