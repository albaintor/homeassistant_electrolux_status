"""Utlities for the Electrolux Status platform."""

import base64
import logging
import math
import re

from pyelectroluxocp import OneAppApi

from homeassistant.components.persistent_notification import async_create
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import CONF_NOTIFICATIONS, NAME

_LOGGER: logging.Logger = logging.getLogger(__package__)


def get_electrolux_session(
    username, password, client_session, language="eng"
) -> OneAppApi:
    """Return OneAppApi Session."""
    return OneAppApi(username, password, client_session)


def create_notification(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    message: str,
    title: str = NAME,
):
    """Create a notification."""
    if config_entry.data.get(CONF_NOTIFICATIONS, True) is False:
        _LOGGER.debug(
            "Discarding notification.\nTitle: %s\nMessage: %s",
            title,
            message,
        )
        return

    input_string = f"{title}-{message}"

    # Convert the string to base64
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
    return math.ceil(seconds / 60)


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
        "home",
        "hot",
        "light",
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
        "unlocked",
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
        "disconnected",
        "dry",
        "locked",
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
