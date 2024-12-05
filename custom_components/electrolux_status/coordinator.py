"""electrolux status integration."""

import asyncio
import aiofiles
import base64
from datetime import UTC, timedelta
import json
import logging
from typing import Any

from aiohttp import ClientResponseError
from pyelectroluxocp import OneAppApi
from pyelectroluxocp.apiModels import UserTokenResponse
from pyelectroluxocp.oneAppApiClient import UserToken

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import Appliance, Appliances, ElectroluxLibraryEntity
from .const import DOMAIN, TIME_ENTITIES_TO_UPDATE, LOOKUP_DIRECTORY_PATH
from .model import ElectroluxTokenStore

_LOGGER: logging.Logger = logging.getLogger(__package__)

SAVE_DELAY = 0
STORAGE_VERSION = 1


class ElectroluxCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    api: OneAppApi = None

    def __init__(
        self,
        hass: HomeAssistant,
        client: OneAppApi,
        renew_interval: int,
        username: str,
    ) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []
        self.renew_task = None
        self.token_task = None
        self.renew_interval = renew_interval
        self._token_expiry = renew_interval
        self._websocket = None
        self._accountid = username
        self._token: UserToken | None = None
        self._token_store: ElectroluxTokenStore | None = None
        self._store: Store[ElectroluxTokenStore] = Store(hass, STORAGE_VERSION, DOMAIN)

        super().__init__(hass, _LOGGER, name=DOMAIN)

    @property
    def accountid(self) -> str:
        """Encode the accountid to base64 for storage."""
        return base64.b64encode(self._accountid.encode("utf-8")).decode("utf-8")

    async def load_store(self) -> None:
        """Load data from file."""
        self._token_store = await self._store.async_load() or {"accounts": {}}

    async def account_token(self) -> UserToken | None:
        """Convert the store token to a usable format."""
        # ensure store is loaded
        if self._token_store is None:
            await self.load_store()

        # search the store for the account we have loaded
        data = self._token_store
        if self.accountid in data["accounts"]:
            entry = data["accounts"][self.accountid]
            try:
                response = UserTokenResponse(entry["token"])
                token = UserToken(response)
                token.expiresAt = dt_util.parse_datetime(
                    entry["expiresAt"],
                    raise_on_error=True,
                )  # token is UTC, so ensure that context remains
                self._token = token  # dont save again, we just loaded it
                await self.update_token_lifetime(token)
            except Exception as ex:  # noqa: BLE001
                _LOGGER.debug("Electrolux store retrieval failed: %s", ex)
                self._store.async_delay_save(self._clear_token, SAVE_DELAY)
            else:
                return token
        return None

    async def update_token_lifetime(self, token: UserToken) -> None:
        """Store the lifetime of the token into the coordinator."""
        if (
            self._token is None
            or self._token.token != token.token
            or self._token.expiresAt != token.expiresAt
        ):
            self._token = token
            self._store.async_delay_save(self._save_token, SAVE_DELAY)

        # Convert the token expiry time to UTC timezone aware then compare
        # token to time 5 minutes from now so we can renew before expiry
        utc_expiry = dt_util.utc_from_timestamp(
            self._token.expiresAt.timestamp(), tz=UTC
        )
        utc_in_5_minutes = dt_util.now(time_zone=UTC) + timedelta(minutes=5)

        if utc_expiry <= utc_in_5_minutes:
            # Token has already expired or will expire within 5 minutes
            self._token_expiry = 0
            self._cancel_token_task()
        else:
            # Calculate the time remaining until the token expires
            self._token_expiry = (utc_expiry - utc_in_5_minutes).seconds
            await self.launch_token_renewal_task()

    @callback
    def _save_token(self) -> ElectroluxTokenStore:
        """Return token data to store in a file."""
        _LOGGER.debug("Saving token to store for %s", self._accountid)
        data = self._token_store

        data["accounts"][self.accountid] = {
            "token": self._token.token,
            "expiresAt": self._token.expiresAt.isoformat(),
        }

        if self._token is None:
            del data["accounts"][self.accountid]

        self._token_store = data
        return data

    @callback
    def _clear_token(self) -> ElectroluxTokenStore:
        """Return token data to store in a file."""
        _LOGGER.debug("Clearing the stored token '%s' from storage", self._accountid)
        data = self._token_store

        if self.accountid in data["accounts"]:
            del data["accounts"][self.accountid]

        self._token_store = data
        self._token = None
        return data

    async def get_stored_token(self) -> None:
        """Fetch the store token and store into the coordinator."""
        if self._token is None:
            self._token = await self.account_token()

        if self._token is None:
            _LOGGER.debug("Stored token not available")
            return

        # force renewal 5 minutes before expiry
        if self._token_expiry <= 300:
            _LOGGER.debug(
                "Requesting new login session. %s stored token expires at: %s",
                self._accountid,
                self._token.expiresAt,
            )
            self._store.async_delay_save(self._clear_token, SAVE_DELAY)
        else:
            _LOGGER.debug(
                "Stored token for %s is still valid until %s and will be reused",
                self._accountid,
                dt_util.now() + timedelta(seconds=self._token_expiry),
            )
            # Load the token into the API
            self.api._user_token = self._token  # noqa: SLF001
            await self.api._get_gigya_client()  # noqa: SLF001

    async def async_login(self) -> bool:
        """Authenticate with the service."""
        try:
            # Check that one can extract the appliance list to confirm login?
            token = await self.api.get_user_token()

            if token and token.token:
                if self._token is None or self._token.token != token.token:
                    # update the token_expiry only if the token changed
                    await self.update_token_lifetime(token)
                _LOGGER.debug("Electrolux logged in successfully, %s", token.token)
                return True
            _LOGGER.debug("Electrolux wrong credentials")
        except ClientResponseError as ex:
            _LOGGER.debug(
                "HTTP error occurred during login to ElectroluxStatus: %s", ex
            )
            self._store.async_delay_save(self._clear_token, SAVE_DELAY)
            if ex.status == 429:
                raise ConfigEntryNotReady(
                    "You have exceeded the maximum number of active sessions. "
                    "Please log out of another device or wait until an existing session expires"
                ) from ex
            raise ConfigEntryError from ex
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
        appliances: Appliances = self.data.get("appliances", None)
        # Should not happen : wonder if this is not the cause of infinite loop of integrations creations => disabled
        # if appliances is None or len(appliances.get_appliances()) == 0:
        #     await self.setup_entities()
        #     appliances = self.data.get('appliances', None)

        for local_appliance_id in appliances.get_appliances():
            if local_appliance_id != appliance_id:
                pass
            try:
                appliance: Appliance = appliances.get_appliances().get(appliance_id)
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
        appliances: Appliances = self.data.get("appliances", None)
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
        appliances: Appliances = self.data.get("appliances", None)
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

    def _cancel_token_task(self):
        """Cancel the running token renewal task."""
        if self.token_task:
            self.token_task.cancel()
            self.token_task = None

    async def launch_token_renewal_task(self):
        """Start the renewal of token."""
        _LOGGER.debug("configuring token_renewal_task")
        self._cancel_token_task()
        self.token_task = asyncio.create_task(
            self.token_renewal_task(), name="Electrolux renewal token"
        )

    async def token_renewal_task(self):
        """Renew token."""

        _LOGGER.debug(
            "Electrolux token_renewal_task will sleep for %s seconds and will start at: %s",
            self._token_expiry,
            dt_util.now() + timedelta(seconds=self._token_expiry),
        )

        # wait until the token is about to expire
        await asyncio.sleep(self._token_expiry)

        # manipulate the token expiry time to force an early token refresh
        _LOGGER.debug("Executing Electrolux token_renewal_task")
        fake_expiry = (dt_util.utcnow() - timedelta(minutes=10)).replace(tzinfo=None)
        self.api._user_token.expiresAt = fake_expiry  # noqa: SLF001
        await self.async_login()

    async def close_websocket(self):
        """Close websocket."""
        if self.renew_task:
            self.renew_task.cancel()
            self.renew_task = None
        if self.token_task:
            self.token_task.cancel()
            self.token_task = None
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
                model_name = appliance_json.get("applianceData").get(
                    "modelName"
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
                    #json_test = '{"DoorOpen":{"access": "read", "type": "boolean"},"FilterType":{"access": "read", "type": "number"},"FilterLife":{"access": "read", "max":100,"min":0,"step":1,"type": "number"},"ECO2":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"Humidity":{"access":"read","step":1,"type":"number"},"Temp":{"access":"read","step":1,"type":"number"},"PM1":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"PM10":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"PM2_5":{"access":"read","max":65535,"min":0,"step":1,"type":"number"},"TVOC":{"access":"read","max":4295,"min":0,"step":1,"type":"number"},"Fanspeed":{"access":"readwrite","max":9,"min":1,"schedulable":true,"step":1,"type":"int"},"Workmode":{"access":"readwrite","schedulable":true,"triggers":[{"action":{"Fanspeed":{"access":"readwrite","disabled":true,"max":9,"min":1,"step":1,"type":"int"}},"condition":{"operand_1":"value","operand_2":"Auto","operator":"eq"}},{"action":{"Fanspeed":{"access":"readwrite","max":9,"min":1,"step":1,"type":"int"}},"condition":{"operand_1":"value","operand_2":"Manual","operator":"eq"}},{"action":{"Fanspeed":{"access":"readwrite","disabled":true,"type":"int"}},"condition":{"operand_1":"value","operand_2":"PowerOff","operator":"eq"}}],"type":"string","values":{"Manual":{},"PowerOff":{},"Auto":{}}},"UILight":{"access":"readwrite","default":true,"schedulable":true,"type":"boolean"},"SafetyLock":{"access":"readwrite","default":false,"type":"boolean"},"Ionizer":{"access":"readwrite","schedulable":true,"type":"boolean"}}'
                    if model_name == "PUREA9":
                        appliance_definition_json_path = self.hass.config.path(LOOKUP_DIRECTORY_PATH + model_name + ".json")
                        async with aiofiles.open(appliance_definition_json_path, mode='r') as handle:
                            appliance_definition_json = await handle.read()
                        appliance_capabilities = json.loads(appliance_definition_json)
                    else:
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
                        appliance_info=appliance_info,
                        capabilities=appliance_capabilities,
                    )
                )
        except Exception as exception:
            _LOGGER.debug("setup_entities: %s", exception)
            raise UpdateFailed from exception
        return self.data

    async def _async_update_data(self):
        """Update data via library."""
        appliances: Appliances = self.data.get("appliances", None)
        for appliance_id, appliance in appliances.get_appliances().items():
            try:
                appliance_status = await self.api.get_appliance_state(appliance_id)
                appliance.update(appliance_status)
            except Exception as exception:
                _LOGGER.debug("_async_update_data: %s", exception)
                raise UpdateFailed from exception
        return self.data
