"""Diagnostics support for Electrolux Status."""

from __future__ import annotations

from typing import Any

import attr

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN
from .coordinator import ElectroluxCoordinator

REDACT_CONFIG = {}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = await _async_get_diagnostics(hass, entry)
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
    data.update(device_info=_async_device_as_dict(hass, device))
    return data


@callback
async def _async_get_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    app_entry: ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]
    user_metadata = await app_entry.api.get_user_metadata()
    appliances_list = await app_entry.api.get_appliances_list()
    appliances_info = await app_entry.api.get_appliances_info(
        [x["applianceId"] for x in appliances_list]
    )
    data = {
        "user_metadata": user_metadata,
        "appliances_info": appliances_info,
        "appliances_list": appliances_list,
        "appliances_detail": {},
    }
    for appliance in appliances_list:
        appliance_id = appliance["applianceId"]
        model_name = appliance.get("applianceData").get(
            "modelName"
        )
        if model_name == "PUREA9":
            appliance_definition_json_path = hass.config.path(LOOKUP_DIRECTORY_PATH + model_name + ".json")
            async with aiofiles.open(appliance_definition_json_path, mode='r') as handle:
                appliance_definition_json = await handle.read()
            appliance_capabilities = json.loads(appliance_definition_json)
            data["appliances_detail"][appliance_id] = {
                "capabilities": appliance_capabilities,
                "state": await app_entry.api.get_appliance_state(appliance_id),
            }
        else:
            data["appliances_detail"][appliance_id] = {
                "capabilities": await app_entry.api.get_appliance_capabilities(appliance_id),
                "state": await app_entry.api.get_appliance_state(appliance_id),
            }
    return async_redact_data(data, REDACT_CONFIG)


@callback
def _async_device_as_dict(hass: HomeAssistant, device: DeviceEntry) -> dict[str, Any]:
    """Represent a device's entities as a dictionary."""

    # Gather information how this device is represented in Home Assistant
    entity_registry = er.async_get(hass)

    data = async_redact_data(attr.asdict(device), REDACT_CONFIG)
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

        entity = attr.asdict(entity_entry)
        entity["state"] = state_dict
        entities.append(entity)

    return async_redact_data(data, REDACT_CONFIG)
