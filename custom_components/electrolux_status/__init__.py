"""electrolux status integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_COUNTRY_CODE,
    CONF_LANGUAGE,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_RENEW_INTERVAL,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_LANGUAGE,
    DEFAULT_WEBSOCKET_RENEWAL_DELAY,
    DOMAIN,
    PLATFORMS,
    languages,
)
from .coordinator import ElectroluxCoordinator
from .util import get_electrolux_session

_LOGGER: logging.Logger = logging.getLogger(__package__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


# noinspection PyUnusedLocal
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the entry and unwind its resources if startup fails."""
    hass.data.setdefault(DOMAIN, {})
    renew_interval = entry.options.get(CONF_RENEW_INTERVAL) or DEFAULT_WEBSOCKET_RENEWAL_DELAY
    client = None
    coordinator = None
    try:
        # The SDK closes its retry-client sessions. Let it own those sessions
        # rather than lending it Home Assistant's shared session/connector.
        client = get_electrolux_session(
            entry.data.get(CONF_USERNAME),
            entry.data.get(CONF_PASSWORD),
            entry.data.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
        )
        coordinator = ElectroluxCoordinator(
            hass,
            client=client,
            renew_interval=renew_interval,
            username=entry.data.get(CONF_USERNAME),
            config_entry=entry,
        )
        await coordinator.get_stored_token()
        if not await coordinator.async_login():
            raise ConfigEntryAuthFailed("Electrolux wrong credentials")

        hass.data[DOMAIN][entry.entry_id] = coordinator
        await coordinator.setup_entities()
        coordinator.listen_websocket()

        async def async_stop(_event):
            """Accept the stop event and drain this entry's resources."""
            await coordinator.async_shutdown()

        entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_stop))
        entry.async_on_unload(entry.add_update_listener(update_listener))
        await coordinator.async_config_entry_first_refresh()
        if not coordinator.last_update_success:
            raise ConfigEntryNotReady
        coordinator.platforms.extend(PLATFORMS)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        # Preserve the existing device-identifier migration.
        _async_remove_old_device_identifiers(hass, entry)
        return True
    except BaseException:
        try:
            if coordinator is not None:
                await coordinator.async_shutdown()
            elif client is not None:
                await client.close()
        except Exception as error:
            _LOGGER.error("Failed-entry cleanup could not finish (%s)", type(error).__name__)
        domain_data = hass.data.get(DOMAIN)
        if domain_data is not None:
            if domain_data.get(entry.entry_id) is coordinator:
                domain_data.pop(entry.entry_id, None)
            if not domain_data:
                hass.data.pop(DOMAIN, None)
        raise


@callback
def _async_remove_old_device_identifiers(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Remove the bad device registry entries."""
    _LOGGER.debug("_async_remove_old_device_identifiers")

    device_registry = dr.async_get(hass)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    appliances = coordinator.data.get("appliances", None)
    all_api_ids = set(appliances.appliances) if appliances else set()

    if all_api_ids:  # only complete if we got the device list from the api
        device_list = list(device_registry.devices)  # Make a copy before removals
        for device in device_list:
            # Only check devices for this domain
            for identifier in device.identifiers:
                # Identifiers from other integrations (homekit, rfxtrx, etc.)
                # may have more than 2 elements — only unpack what we need.
                if len(identifier) < 2:
                    continue
                domain = identifier[0]
                deviceid = identifier[1]

                if domain != DOMAIN:
                    continue

                if deviceid not in all_api_ids:
                    _LOGGER.debug("Removing old device identifier: %s", deviceid)
                    device_registry.async_remove_device(device.id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    _LOGGER.debug("async_remove_config_entry_device")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    appliances = coordinator.data.get("appliances", None)
    all_api_ids = set(appliances.appliances) if appliances else set()

    identifier_tuple = next(iter(device_entry.identifiers))[1]
    if identifier_tuple not in all_api_ids:
        return True
    return False


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator: ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await coordinator.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Electrolux async_reload_entry %s", entry)
    await hass.config_entries.async_reload(entry.entry_id)
