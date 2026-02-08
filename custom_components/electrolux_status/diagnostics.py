"""Diagnostics support for Electrolux Status."""

from __future__ import annotations

from typing import Any

import attr
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .const import CONF_ACCESS_TOKEN, CONF_API_KEY, CONF_REFRESH_TOKEN, DOMAIN
from .coordinator import ElectroluxCoordinator

REDACT_CONFIG: set[str] = {CONF_API_KEY, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = await _async_get_diagnostics(hass, entry)

    # Include redacted config entry data
    data["config_entry"] = {
        "entry_id": entry.entry_id,
        "domain": entry.domain,
        "title": entry.title,
        "data": dict(entry.data),  # Will be redacted by async_redact_data
        "options": dict(entry.options),
        "unique_id": entry.unique_id,
        "disabled_by": entry.disabled_by,
    }

    device_registry = dr.async_get(hass)
    data.update(
        device_info=[
            _async_device_as_dict(hass, device)
            for device in dr.async_entries_for_config_entry(
                device_registry, entry.entry_id
            )
        ],
    )
    return async_redact_data(data, REDACT_CONFIG)


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device entry."""
    data = await _async_get_diagnostics(hass, entry)

    # Include redacted config entry data
    data["config_entry"] = {
        "entry_id": entry.entry_id,
        "domain": entry.domain,
        "title": entry.title,
        "data": dict(entry.data),  # Will be redacted by async_redact_data
        "options": dict(entry.options),
        "unique_id": entry.unique_id,
        "disabled_by": entry.disabled_by,
    }

    data.update(device_info=_async_device_as_dict(hass, device))
    return async_redact_data(data, REDACT_CONFIG)


@callback
async def _async_get_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    app_entry: ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]

    data = {
        "user_metadata": None,
        "appliances_info": None,
        "appliances_list": None,
        "appliances_detail": {},
        "errors": [],
    }

    try:
        data["user_metadata"] = await app_entry.api.get_user_metadata()
    except Exception as ex:
        data["errors"].append(f"Failed to get user metadata: {ex}")

    try:
        data["appliances_list"] = await app_entry.api.get_appliances_list()
    except Exception as ex:
        data["errors"].append(f"Failed to get appliances list: {ex}")
        # Can't continue without appliances list
        return async_redact_data(data, REDACT_CONFIG)

    if data["appliances_list"]:
        try:
            data["appliances_info"] = await app_entry.api.get_appliances_info(
                [x["applianceId"] for x in data["appliances_list"]]
            )
        except Exception as ex:
            data["errors"].append(f"Failed to get appliances info: {ex}")

        for appliance in data["appliances_list"]:
            appliance_id = appliance["applianceId"]
            appliance_detail = {}

            try:
                appliance_detail["capabilities"] = (
                    await app_entry.api.get_appliance_capabilities(appliance_id)
                )
            except Exception as ex:
                appliance_detail["capabilities_error"] = str(ex)

            try:
                appliance_detail["state"] = await app_entry.api.get_appliance_state(
                    appliance_id
                )
            except Exception as ex:
                appliance_detail["state_error"] = str(ex)

            if appliance_detail:
                data["appliances_detail"][appliance_id] = appliance_detail

    return async_redact_data(data, REDACT_CONFIG)


@callback
def _async_device_as_dict(hass: HomeAssistant, device: DeviceEntry) -> dict[str, Any]:
    """Represent a device's entities as a dictionary."""

    # Gather information how this device is represented in Home Assistant
    entity_registry = er.async_get(hass)

    data = async_redact_data(attr.asdict(device), REDACT_CONFIG)  # type: ignore[arg-type]
    data["entities"] = []
    entities: list[dict[str, Any]] = data["entities"]

    entries = er.async_entries_for_device(
        entity_registry,
        device_id=device.id,
        include_disabled_entities=True,
    )

    for entity_entry in entries:
        state = hass.states.get(entity_entry.entity_id)
        state_dict = None
        if state:
            state_dict = dict(state.as_dict())
            state_dict.pop("context", None)

        entity = attr.asdict(entity_entry)  # type: ignore[arg-type]
        entity["state"] = state_dict
        entities.append(entity)

    return async_redact_data(data, REDACT_CONFIG)
