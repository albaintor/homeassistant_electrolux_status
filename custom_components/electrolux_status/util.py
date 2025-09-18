"""Utlities for the Electrolux Status platform."""

import base64
import logging
import math
import re

from pyelectroluxocp import OneAppApi

from homeassistant.components.persistent_notification import async_create
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
    username, password, country_code, client_session, language="eng"
) -> OneAppApi:
    """Return OneAppApi Session."""
    return OneAppApi(username, password, country_code, client_session)


def should_send_notification(config_entry, alert_severity, alert_status):
    """Determine if the notification should be sent based on severity and config."""
    if alert_status == "NOT_NEEDED":
        return False
    if alert_severity == "DIAGNOSTIC":
        return config_entry.data.get(CONF_NOTIFICATION_DIAG, False)
    if alert_severity == "WARNING":
        return config_entry.data.get(CONF_NOTIFICATION_WARNING, False)
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
    async_create(hass, message, title=title, notification_id=base64_string)


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
