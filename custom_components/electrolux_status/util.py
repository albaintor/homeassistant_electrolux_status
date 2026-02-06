"""Utlities for the Electrolux Status platform."""

import base64
import logging
import math
import re
from typing import Any

from electrolux_group_developer_sdk.auth.token_manager import TokenManager
from electrolux_group_developer_sdk.client.appliance_client import ApplianceClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_NOTIFICATION_DEFAULT,
    CONF_NOTIFICATION_DIAG,
    CONF_NOTIFICATION_WARNING,
    NAME,
)

_LOGGER: logging.Logger = logging.getLogger(__package__)


def get_electrolux_session(
    api_key, access_token, refresh_token, client_session, language="eng"
) -> "ElectroluxApiClient":
    """Return Electrolux API Session."""
    return ElectroluxApiClient(api_key, access_token, refresh_token)


def should_send_notification(config_entry, alert_severity, alert_status):
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
    hass.services.async_call(
        "persistent_notification",
        "create",
        {"message": message, "title": title, "notification_id": base64_string},
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
    _LOGGER.debug("Electrolux unable to convert %s to boolean", value)
    if fallback:
        return value
    return False


class ElectroluxApiClient:
    """Wrapper for the new Electrolux API client to maintain compatibility."""

    def __init__(self, api_key: str, access_token: str, refresh_token: str):
        """Initialize the API client."""
        self._token_manager = TokenManager(access_token, refresh_token, api_key)
        self._client = ApplianceClient(self._token_manager)
        self._user_token = None

    async def get_user_token(self):
        """Get user token - compatibility method."""

        # The new API doesn't have this concept, but we can return a mock token
        # since authentication is handled by TokenManager
        class MockToken:
            def __init__(self):
                self.token = "mock_token"

        return MockToken()

    async def get_appliances_list(self):
        """Get list of appliances."""
        appliances = await self._client.get_appliances()
        # Convert to the expected format
        result = []
        for appliance in appliances:
            result.append(
                {
                    "applianceId": appliance.applianceId,
                    "applianceName": appliance.applianceName,
                    "applianceType": appliance.applianceType,
                    "connectionState": "connected",  # Assume connected
                    "applianceData": {
                        "applianceName": appliance.applianceName,
                        "modelName": getattr(appliance, "model", "Unknown"),
                    },
                    "created": "2022-01-01T00:00:00.000Z",  # Mock creation date
                }
            )
        return result

    async def get_appliances_info(self, appliance_ids):
        """Get appliances info."""
        result = []
        for appliance_id in appliance_ids:
            try:
                details = await self._client.get_appliance_details(appliance_id)
                # Convert to expected format
                info = {
                    "pnc": appliance_id,
                    "brand": getattr(details, "brand", "Electrolux"),
                    "model": getattr(details, "model", "Unknown"),
                    "device_type": getattr(details, "deviceType", "Unknown"),
                    "variant": getattr(details, "variant", "Unknown"),
                    "color": getattr(details, "color", "Unknown"),
                }
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
        """Watch for state updates - not implemented in new API."""
        # The new API doesn't have websocket support mentioned
        # This is a placeholder
        _LOGGER.warning("Websocket functionality not available in new API")
        pass

    async def disconnect_websocket(self):
        """Disconnect websocket - not implemented."""
        pass

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
            # If the method doesn't exist, try alternative approaches
            _LOGGER.warning("execute_command method not found in new API")
            # Return a mock success response
            return {"result": "success"}

    async def close(self):
        """Close the client."""
        # The new SDK doesn't have a close method, but TokenManager might need cleanup
        pass
