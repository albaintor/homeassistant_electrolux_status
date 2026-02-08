"""electrolux status integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_REFRESH_TOKEN,
    DEFAULT_WEBSOCKET_RENEWAL_DELAY,
    DOMAIN,
    PLATFORMS,
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
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    # Always create new coordinator for clean, predictable behavior
    _LOGGER.debug("Electrolux creating coordinator instance")
    renew_interval = DEFAULT_WEBSOCKET_RENEWAL_DELAY

    api_key = entry.data.get(CONF_API_KEY) or ""
    access_token = entry.data.get(CONF_ACCESS_TOKEN) or ""
    refresh_token = entry.data.get(CONF_REFRESH_TOKEN) or ""
    session = async_get_clientsession(hass)

    client = get_electrolux_session(api_key, access_token, refresh_token, session)
    coordinator = ElectroluxCoordinator(
        hass,
        client=client,
        renew_interval=renew_interval,
        username=api_key,
    )
    coordinator.config_entry = entry

    # Authenticate
    if not await coordinator.async_login():
        raise ConfigEntryAuthFailed("Electrolux wrong credentials")

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Initialize entities
    _LOGGER.debug("async_setup_entry setup_entities")
    await coordinator.setup_entities()
    _LOGGER.debug("async_setup_entry listen_websocket")
    await coordinator.listen_websocket()
    _LOGGER.debug("async_setup_entry launch_websocket_renewal_task")
    await coordinator.launch_websocket_renewal_task()

    _LOGGER.debug("async_setup_entry async_config_entry_first_refresh")
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    _LOGGER.debug("async_setup_entry extend PLATFORMS")
    coordinator.platforms.extend(PLATFORMS)

    # Call async_setup_entry in entity files
    _LOGGER.debug("async_setup_entry async_forward_entry_setups")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Setup cleanup handlers
    async def _close_api(event):
        await coordinator.api.close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _close_api)
    )
    entry.async_on_unload(entry.add_update_listener(update_listener))

    _LOGGER.debug("async_setup_entry OVER")
    return True


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator: ElectroluxCoordinator = hass.data[DOMAIN].get(entry.entry_id)

    if coordinator:
        # Proper cleanup of coordinator resources
        await coordinator.close_websocket()
        await coordinator.api.close()

        # Remove from registry to prevent memory leaks
        hass.data[DOMAIN].pop(entry.entry_id, None)

    # Unload platforms
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Electrolux async_reload_entry %s", entry)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
