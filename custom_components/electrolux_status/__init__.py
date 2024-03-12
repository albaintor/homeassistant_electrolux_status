"""electrolux status integration."""
import asyncio
import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Config
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed

from .api import Appliance, Appliances, ElectroluxLibraryEntity
from .const import CONF_LANGUAGE, DEFAULT_LANGUAGE, DEFAULT_WEBSOCKET_RENEWAL_DELAY, CONF_RENEW_INTERVAL
from .const import CONF_PASSWORD
from .const import CONF_USERNAME
from .const import DOMAIN
from .const import PLATFORMS
from .const import languages
from pyelectroluxocp import OneAppApi
from .pyelectroluxconnect_util import pyelectroluxconnect_util

_LOGGER: logging.Logger = logging.getLogger(__package__)


# noinspection PyUnusedLocal
async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    renew_interval = DEFAULT_WEBSOCKET_RENEWAL_DELAY
    if entry.options.get(CONF_RENEW_INTERVAL):
        renew_interval = entry.options[CONF_RENEW_INTERVAL]

    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    language = languages.get(entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE), "eng")

    client = pyelectroluxconnect_util.get_session(username, password, _LOGGER, language)
    coordinator = ElectroluxCoordinator(hass, client=client, renew_interval=renew_interval)
    if not await coordinator.async_login():
        raise Exception("Electrolux wrong credentials")

    # Bug ?
    if coordinator.config_entry is None:
        coordinator.config_entry = entry

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Initialize entities
    _LOGGER.debug("async_setup_entry setup_entities")
    await coordinator.setup_entities()
    _LOGGER.debug("async_setup_entry listen_websocket")
    coordinator.listen_websocket()
    #_LOGGER.debug("async_setup_entry launch_websocket_renewal_task")
    #await coordinator.launch_websocket_renewal_task()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, coordinator.api.close)
    )

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
    _LOGGER.debug("async_setup_entry add_update_listener")
    entry.add_update_listener(async_reload_entry)
    _LOGGER.debug("async_setup_entry OVER")
    return True


class ElectroluxCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""
    api: OneAppApi = None

    def __init__(self, hass: HomeAssistant, client: OneAppApi, renew_interval: int) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []
        self.renew_task = None
        self.renew_interval = renew_interval

        super().__init__(hass, _LOGGER, name=DOMAIN)

    async def async_login(self) -> bool:
        try:
            # Check that one can extract the appliance list to confirm login
            token = await self.api.get_user_token()
            if token and token.token:
                _LOGGER.debug("Electrolux logged successfully, %s", token.token)
                return True
            _LOGGER.debug("Electrolux wrong credentials")
        except Exception as ex:
            _LOGGER.error("Could not log in to ElectroluxStatus, %s", ex)
            raise ex
        return False

    def incoming_data(self, data: dict[str, dict[str, any]]):
        _LOGGER.debug("Electrolux appliance state updated %s", json.dumps(data))
        self.async_set_updated_data(data)

    def listen_websocket(self):
        appliances: Appliances = self.data.get('appliances', None)
        ids = appliances.get_appliance_ids()
        _LOGGER.debug("Electrolux listen_websocket for appliances %s", ",".join(ids))
        if ids is None or len(ids) == 0:
            return
        asyncio.create_task(self.api.watch_for_appliance_state_updates(ids, self.incoming_data))

    async def launch_websocket_renewal_task(self):
        if self.renew_task:
            self.renew_task.cancel()
            self.renew_task = None
        self.renew_task = asyncio.create_task(self.renew_websocket(), name="Electrolux renewal websocket")

    async def renew_websocket(self):
        while True:
            await asyncio.sleep(self.renew_interval)
            _LOGGER.debug("Electrolux renew_websocket")
            try:
                await self.api.disconnect_websocket()
            except Exception as ex:
                _LOGGER.error("Electrolux renew_websocket could not close websocket %s", ex)
            self.listen_websocket()

    async def close_websocket(self):
        if self.renew_task:
            self.renew_task.cancel()
            self.renew_task = None
        try:
            await self.api.disconnect_websocket()
        except Exception as ex:
            _LOGGER.error("Electrolux close_websocket could not close websocket %s", ex)

    async def setup_entities(self):
        _LOGGER.debug("Electrolux setup_entities")
        appliances = Appliances({})
        self.data = {
            "appliances": appliances
        }
        try:
            appliances_list = await self.api.get_appliances_list()
            if appliances_list is None:
                _LOGGER.error("Electrolux unable to retrieve appliances list. Cancelling setup")
                raise Exception("Electrolux unable to retrieve appliances list. Cancelling setup")
            _LOGGER.debug("Electrolux update appliances %s %s",self.api, json.dumps(appliances_list))
            for appliance_json in appliances_list:
                appliance_capabilities = None
                appliance_id = appliance_json.get('applianceId')
                connection_status = appliance_json.get('connectionState')
                _LOGGER.debug("Electrolux found appliance %s", appliance_id)
                # appliance_profile = await self.hass.async_add_executor_job(self.api.getApplianceProfile, appliance)
                appliance_name = appliance_json.get('applianceData').get('applianceName')
                appliance_infos = await self.api.get_appliances_info([appliance_id])
                appliance_state = await self.api.get_appliance_state(appliance_id)
                _LOGGER.debug("Electrolux get_appliance_status result %s", json.dumps(appliance_state))
                try:
                    appliance_capabilities = await self.api.get_appliance_capabilities(appliance_id)
                    _LOGGER.debug("Electrolux appliance capabilities %s", json.dumps(appliance_capabilities))
                except Exception as exception:
                    _LOGGER.warning("Electrolux unable to retrieve capabilities, we are going on our own")

                appliance_info = None if len(appliance_infos) == 0 else appliance_infos[0]
                appliance_model = appliance_info.get('model') if appliance_info else ""
                brand = appliance_info.get('brand') if appliance_info else ""
                # appliance_profile not reported
                appliance = Appliance(coordinator=self,
                                      pnc_id=appliance_id,
                                      name=appliance_name,
                                      brand=brand,
                                      model=appliance_model,
                                      state=appliance_state)
                appliances.appliances[appliance_id] = appliance

                appliance.setup(ElectroluxLibraryEntity(name=appliance_name, status=connection_status,
                                                        state=appliance_state, appliance_info=appliance_info,
                                                        capabilities=appliance_capabilities))
            return self.data
        except Exception as exception:
            _LOGGER.exception(exception)
            raise UpdateFailed() from exception


    async def _async_update_data(self):
        """Update data via library."""
        appliances: Appliances = self.data.get('appliances', None)
        # Should not happen : wonder if this is not the cause of infinite loop of integrations creations => disabled
        # if appliances is None or len(appliances.get_appliances()) == 0:
        #     await self.setup_entities()
        #     appliances = self.data.get('appliances', None)

        for appliance_id in appliances.get_appliances():
            try:
                appliance: Appliance = appliances.get_appliances().get(appliance_id)
                appliance_status = await self.api.get_appliance_state(appliance_id)
                appliance.update(appliance_status)
            except Exception as exception:
                _LOGGER.exception(exception)
                raise UpdateFailed() from exception
        return self.data

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator:ElectroluxCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.close_websocket()
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Electrolux async_reload_entry %s", entry)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
