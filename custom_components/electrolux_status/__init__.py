"""electrolux status integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
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


# noinspection PyUnusedLocal
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

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
        username=api_key,  # Use API key as account identifier
    )

    # await coordinator.get_stored_token()  # Not needed with new SDK
    if not await coordinator.async_login():
        raise ConfigEntryAuthFailed("Electrolux wrong credentials")

    # Bug ?
    if coordinator.config_entry is None:
        coordinator.config_entry = entry

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Initialize entities
    _LOGGER.debug("async_setup_entry setup_entities")
    await coordinator.setup_entities()
    _LOGGER.debug("async_setup_entry listen_websocket")
    coordinator.listen_websocket()
    _LOGGER.debug("async_setup_entry launch_websocket_renewal_task")
    await coordinator.launch_websocket_renewal_task()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, coordinator.api.close)
    )

    entry.async_on_unload(entry.add_update_listener(update_listener))

    _LOGGER.debug("async_setup_entry async_config_entry_first_refresh")
    # Fill in the values for first time
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    _LOGGER.debug("async_setup_entry extend PLATFORMS")
    coordinator.platforms.extend(PLATFORMS)

    # Call async_setup_entry in entity files
    _LOGGER.debug("async_setup_entry async_forward_entry_setups")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.debug("async_setup_entry OVER")
    return True


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator: ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.close_websocket()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Electrolux async_reload_entry %s", entry)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
