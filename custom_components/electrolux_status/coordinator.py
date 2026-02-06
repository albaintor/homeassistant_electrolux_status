"""Electrolux status integration."""

import asyncio
import json
import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Appliance, Appliances, ElectroluxLibraryEntity
from .const import DOMAIN, TIME_ENTITIES_TO_UPDATE
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
        self._sse_task = None  # Track SSE task
        self._deferred_tasks = set()  # Track deferred update tasks

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                hours=6
            ),  # Health check every 6 hours instead of 30 seconds
        )

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
                # Track the deferred task to prevent memory leaks
                task = asyncio.create_task(self.deferred_update(appliance_id, 70))
                self._deferred_tasks.add(task)
                task.add_done_callback(self._deferred_tasks.discard)

    def listen_websocket(self):
        """Listen for state changes."""
        appliances: Any = self.data.get("appliances", None)
        ids = appliances.get_appliance_ids()
        _LOGGER.debug("Electrolux listen_websocket for appliances %s", ",".join(ids))
        if ids is None or len(ids) == 0:
            return
        # Cancel any existing SSE task before starting a new one
        if self._sse_task and not self._sse_task.done():
            self._sse_task.cancel()
        # Start SSE streaming (creates its own background task)
        self._sse_task = asyncio.create_task(
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
        """Renew SSE event stream."""
        while True:
            await asyncio.sleep(self.renew_interval)
            _LOGGER.debug("Electrolux renew SSE event stream")
            try:
                # Cancel existing SSE task before disconnecting
                if self._sse_task and not self._sse_task.done():
                    self._sse_task.cancel()
                    try:
                        await self._sse_task
                    except asyncio.CancelledError:
                        pass
                    self._sse_task = None

                await self.api.disconnect_websocket()  # This will be updated to properly close SSE
                self.listen_websocket()  # Restart SSE connection
            except Exception as ex:
                _LOGGER.error("Electrolux renew SSE failed %s", ex)

    async def close_websocket(self):
        """Close SSE event stream."""
        # Cancel renewal task
        if self.renew_task:
            self.renew_task.cancel()
            self.renew_task = None

        # Cancel SSE task
        if self._sse_task and not self._sse_task.done():
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
            self._sse_task = None

        # Cancel all deferred tasks
        for task in self._deferred_tasks.copy():
            if not task.done():
                task.cancel()
        self._deferred_tasks.clear()

        try:
            await self.api.disconnect_websocket()
        except Exception as ex:
            _LOGGER.error("Electrolux close SSE failed %s", ex)

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
                    appliance_capabilities = await self.api.get_appliance_capabilities(
                        appliance_id
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
                # Fallback to model from appliance list if info doesn't have it
                if not appliance_model:
                    appliance_model = appliance_json.get("applianceData", {}).get(
                        "modelName", ""
                    )
                brand = appliance_info.get("brand") if appliance_info else ""
                # Fallback to Electrolux if no brand
                if not brand:
                    brand = "Electrolux"

                _LOGGER.debug(
                    "Appliance %s info: name='%s', model='%s' (from %s), brand='%s' (from %s), applianceData=%s",
                    appliance_id,
                    appliance_name,
                    appliance_model,
                    (
                        "appliance_info"
                        if appliance_info and appliance_info.get("model")
                        else "appliance_json"
                    ),
                    brand,
                    (
                        "appliance_info"
                        if appliance_info and appliance_info.get("brand")
                        else "fallback"
                    ),
                    appliance_json.get("applianceData", {}),
                )
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
                error_msg = str(exception).lower()
                # Check if this is an authentication error
                if any(
                    keyword in error_msg
                    for keyword in ["401", "unauthorized", "auth", "token"]
                ):
                    _LOGGER.warning(
                        "Authentication failed during data update: %s", exception
                    )
                    raise ConfigEntryAuthFailed(
                        "Token expired or invalid"
                    ) from exception
                _LOGGER.debug("_async_update_data: %s", exception)
                raise UpdateFailed from exception
        return self.data
