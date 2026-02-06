"""Electrolux status integration."""

import asyncio
import base64
import json
import logging
from typing import Any

import aiofiles
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Appliance, Appliances, ElectroluxLibraryEntity
from .const import DOMAIN, LOOKUP_DIRECTORY_PATH, TIME_ENTITIES_TO_UPDATE
from .util import ElectroluxApiClient

_LOGGER: logging.Logger = logging.getLogger(__package__)


class ElectroluxCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    api: ElectroluxApiClient

    def __init__(
        self,
        hass: HomeAssistant,
        client: ElectroluxApiClient,
        renew_interval: int,
        username: str,
    ) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []
        self.renew_task = None
        self.renew_interval = renew_interval
        self._token_expiry = renew_interval
        self._websocket = None
        self._accountid = username

        super().__init__(hass, _LOGGER, name=DOMAIN)

    @property
    def accountid(self) -> str:
        """Encode the accountid to base64 for storage."""
        return base64.b64encode(self._accountid.encode("utf-8")).decode("utf-8")

    async def async_login(self) -> bool:
        """Authenticate with the service."""
        try:
            # Test authentication by fetching appliances
            await self.api.get_appliances_list()
            _LOGGER.debug("Electrolux logged in successfully")
            return True
        except Exception as ex:
            _LOGGER.error("Could not log in to ElectroluxStatus, %s", ex)
            raise ConfigEntryError from ex
        return False

    async def deferred_update(self, appliance_id: str, delay: int) -> None:
        """Deferred update due to Electrolux not sending updated data at the end of the appliance program/cycle."""
        _LOGGER.debug(
            "Electrolux scheduling deferred update for appliance %s", appliance_id
        )
        await asyncio.sleep(delay)
        _LOGGER.debug(
            "Electrolux scheduled deferred update for appliance %s running",
            appliance_id,
        )
        appliances: Any = self.data.get("appliances", None)
        if not appliances:
            return
        try:
            appliance: Appliance = appliances.get_appliance(appliance_id)
            if appliance:
                appliance_status = await self.api.get_appliance_state(appliance_id)
                appliance.update(appliance_status)
                self.async_set_updated_data(self.data)
        except Exception as exception:
            _LOGGER.exception(exception)  # noqa: TRY401
            raise UpdateFailed from exception

    def incoming_data(self, data: dict[str, dict[str, Any]]):
        """Process incoming data."""
        _LOGGER.debug("Electrolux appliance state updated %s", json.dumps(data))
        # Update reported data
        appliances: Any = self.data.get("appliances", None)
        for appliance_id, appliance_data in data.items():
            appliance = appliances.get_appliance(appliance_id)
            appliance.update_reported_data(appliance_data)
        self.async_set_updated_data(self.data)
        # Bug in Electrolux library : no data sent when appliance cycle is over
        for appliance_id, appliance_data in data.items():
            do_deferred = False
            for key, value in appliance_data.items():
                if key in TIME_ENTITIES_TO_UPDATE:
                    if value is not None and 0 < value <= 1:
                        do_deferred = True
                        break
            if do_deferred:
                asyncio.create_task(self.deferred_update(appliance_id, 70))

    def listen_websocket(self):
        """Listen for state changes."""
        appliances: Any = self.data.get("appliances", None)
        ids = appliances.get_appliance_ids()
        _LOGGER.debug("Electrolux listen_websocket for appliances %s", ",".join(ids))
        if ids is None or len(ids) == 0:
            return
        self._websocket = asyncio.create_task(
            self.api.watch_for_appliance_state_updates(ids, self.incoming_data)
        )

    async def launch_websocket_renewal_task(self):
        """Start the renewal of websocket."""
        if self.renew_task:
            self.renew_task.cancel()
            self.renew_task = None
        self.renew_task = asyncio.create_task(
            self.renew_websocket(), name="Electrolux renewal websocket"
        )

    async def renew_websocket(self):
        """Renew websocket state."""
        while True:
            await asyncio.sleep(self.renew_interval)
            _LOGGER.debug("Electrolux renew_websocket")
            try:
                await self.api.disconnect_websocket()
            except Exception as ex:  # noqa: BLE001
                _LOGGER.error(
                    "Electrolux renew_websocket could not close websocket %s", ex
                )
            self.listen_websocket()

    async def close_websocket(self):
        """Close websocket."""
        if self.renew_task:
            self.renew_task.cancel()
            self.renew_task = None
        try:
            await self.api.disconnect_websocket()
        except Exception as ex:  # noqa: BLE001
            _LOGGER.error("Electrolux close_websocket could not close websocket %s", ex)

    async def setup_entities(self):
        """Configure entities."""
        _LOGGER.debug("Electrolux setup_entities")
        appliances = Appliances({})
        self.data = {"appliances": appliances}
        try:
            appliances_list = await self.api.get_appliances_list()
            if appliances_list is None:
                _LOGGER.error(
                    "Electrolux unable to retrieve appliances list. Cancelling setup"
                )
                raise ConfigEntryNotReady(
                    "Electrolux unable to retrieve appliances list. Cancelling setup"
                )
            _LOGGER.debug(
                "Electrolux get_appliances_list %s %s",
                self.api,
                json.dumps(appliances_list),
            )

            for appliance_json in appliances_list:
                appliance_capabilities = None
                appliance_id = appliance_json.get("applianceId")
                connection_status = appliance_json.get("connectionState")
                _LOGGER.debug("Electrolux found appliance %s", appliance_id)
                # appliance_profile = await self.hass.async_add_executor_job(self.api.getApplianceProfile, appliance)
                appliance_name = appliance_json.get("applianceData").get(
                    "applianceName"
                )
                model_name = appliance_json.get("applianceData").get("modelName")
                appliance_infos = await self.api.get_appliances_info([appliance_id])
                _LOGGER.debug(
                    "Electrolux get_appliances_info result: %s",
                    json.dumps(appliance_infos),
                )
                appliance_state = await self.api.get_appliance_state(appliance_id)
                _LOGGER.debug(
                    "Electrolux get_appliance_state result: %s",
                    json.dumps(appliance_state),
                )
                try:
                    # json_test = '{"DoorOpen":{"access": "read", "type": "boolean"},"FilterType":{"access": "read", "type": "number"},"FilterLife":{"access": "read", "max":100,"min":0,"step":1,"type": "number"},"ECO2":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"Humidity":{"access":"read","step":1,"type":"number"},"Temp":{"access":"read","step":1,"type":"number"},"PM1":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"PM10":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"PM2_5":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"TVOC":{"access":"read","max":4295,"min":0,"step":1,"type":"number"},"Fanspeed":{"access":"readwrite","max":9,"min":1,"schedulable":true,"step":1,"type":"int"},"Workmode":{"access":"readwrite","schedulable":true,"triggers":[{"action":{"Fanspeed":{"access":"readwrite","disabled":true,"max":9,"min":1,"step":1,"type":"int"}},"condition":{"operand_1":"value","operand_2":"Auto","operator":"eq"}},{"action":{"Fanspeed":{"access":"readwrite","max":9,"min":1,"step":1,"type":"int"}},"condition":{"operand_1":"value","operand_2":"Manual","operator":"eq"}},{"action":{"Fanspeed":{"access":"readwrite","disabled":true,"type":"int"}},"condition":{"operand_1":"value","operand_2":"PowerOff","operator":"eq"}}],"type":"string","values":{"Manual":{},"PowerOff":{},"Auto":{}}},"UILight":{"access":"readwrite","default":true,"schedulable":true,"type":"boolean"},"SafetyLock":{"access":"readwrite","default":false,"type":"boolean"},"Ionizer":{"access":"readwrite","schedulable":true,"type":"boolean"}}'
                    if model_name == "PUREA9":
                        appliance_definition_json_path = self.hass.config.path(
                            LOOKUP_DIRECTORY_PATH + model_name + ".json"
                        )
                        async with aiofiles.open(
                            appliance_definition_json_path, mode="r"
                        ) as handle:
                            appliance_definition_json = await handle.read()
                        appliance_capabilities = json.loads(appliance_definition_json)
                    else:
                        appliance_capabilities = (
                            await self.api.get_appliance_capabilities(appliance_id)
                        )
                    _LOGGER.debug(
                        "Electrolux get_appliance_capabilities result: %s",
                        json.dumps(appliance_capabilities),
                    )
                except Exception as exception:  # noqa: BLE001
                    _LOGGER.warning(
                        "Electrolux unable to retrieve capabilities, we are going on our own",
                        exception,
                    )
                    # raise ConfigEntryNotReady(
                    #     "Electrolux unable to retrieve capabilities. Cancelling setup"
                    # ) from exception

                appliance_info = appliance_infos[0] if appliance_infos else None

                appliance_model = appliance_info.get("model") if appliance_info else ""
                brand = appliance_info.get("brand") if appliance_info else ""
                # appliance_profile not reported
                appliance = Appliance(
                    coordinator=self,
                    pnc_id=appliance_id,
                    name=appliance_name,
                    brand=brand,
                    model=appliance_model,
                    state=appliance_state,
                )
                appliances.appliances[appliance_id] = appliance

                appliance.setup(
                    ElectroluxLibraryEntity(
                        name=appliance_name,
                        status=connection_status,
                        state=appliance_state,
                        appliance_info=appliance_info or {},
                        capabilities=appliance_capabilities or {},
                    )
                )
        except Exception as exception:
            _LOGGER.debug("setup_entities: %s", exception)
            raise UpdateFailed from exception
        return self.data

    async def _async_update_data(self):
        """Update data via library."""
        appliances: Appliances = self.data.get("appliances")  # type: ignore[union-attr]
        for appliance_id, appliance in appliances.get_appliances().items():
            try:
                appliance_status = await self.api.get_appliance_state(appliance_id)
                appliance.update(appliance_status)
            except Exception as exception:
                _LOGGER.debug("_async_update_data: %s", exception)
                raise UpdateFailed from exception
        return self.data
