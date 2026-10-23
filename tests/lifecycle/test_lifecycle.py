"""Coordinator and entry teardown must preserve resource ownership."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from pyelectroluxocp import OneAppApi
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.electrolux_status import async_unload_entry
from custom_components.electrolux_status.api import Appliance, Appliances
from custom_components.electrolux_status.const import DOMAIN, TIME_ENTITIES_TO_UPDATE
from custom_components.electrolux_status.coordinator import ElectroluxCoordinator


@pytest.fixture
def coordinator(hass):
    """Create the real coordinator with a constrained network boundary."""
    api = AsyncMock(spec=OneAppApi)
    result = ElectroluxCoordinator(hass, api, 3600, "test-account")
    result.data = {"appliances": Appliances({"test-appliance": Mock(spec=Appliance)})}
    return result


async def test_shutdown_awaits_all_coordinator_tasks(coordinator):
    """Watch, renewal and delayed state work must finish before shutdown returns."""
    started = asyncio.Event()

    async def watch(_ids, _callback):
        started.set()
        await asyncio.Event().wait()

    coordinator.api.watch_for_appliance_state_updates.side_effect = watch
    before = asyncio.all_tasks()
    try:
        coordinator.listen_websocket()
        await started.wait()
        await coordinator.launch_websocket_renewal_task()
        await coordinator.launch_token_renewal_task()
        coordinator.incoming_data(
            {"test-appliance": {next(iter(TIME_ENTITIES_TO_UPDATE)): 1}}
        )
        await asyncio.sleep(0)
        owned = asyncio.all_tasks() - before
        assert len(owned) == 4
        await asyncio.gather(coordinator.async_shutdown(), coordinator.async_shutdown())
        assert all(task.done() for task in owned)
        coordinator.api.close.assert_awaited_once_with()
        await coordinator.async_shutdown()
        coordinator.api.close.assert_awaited_once_with()

        coordinator.listen_websocket()
        await coordinator.launch_websocket_renewal_task()
        await coordinator.launch_token_renewal_task()
        coordinator.incoming_data(
            {"test-appliance": {next(iter(TIME_ENTITIES_TO_UPDATE)): 1}}
        )
        assert not (asyncio.all_tasks() - before)
    finally:
        pending = asyncio.all_tasks() - before
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


async def test_token_renewal_does_not_cancel_its_current_generation(coordinator):
    """Scheduling the next renewal must let the current refresh finish."""

    async def current_generation():
        coordinator.token_task = asyncio.current_task()
        await coordinator.launch_token_renewal_task()
        await asyncio.sleep(0)
        return True

    try:
        assert await asyncio.create_task(current_generation()) is True
    finally:
        await coordinator.async_shutdown()


@pytest.mark.parametrize("platforms_unload", [False, True])
async def test_unload_only_closes_after_platform_acceptance(
    hass, coordinator, monkeypatch, platforms_unload
):
    """One entry's unload must neither break refused platforms nor another account."""
    entry = MockConfigEntry(domain=DOMAIN)
    other = object()
    hass.data[DOMAIN] = {entry.entry_id: coordinator, "other-entry": other}
    monkeypatch.setattr(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=platforms_unload),
    )
    try:
        assert await async_unload_entry(hass, entry) is platforms_unload
        assert hass.data[DOMAIN]["other-entry"] is other
        if platforms_unload:
            assert entry.entry_id not in hass.data[DOMAIN]
            coordinator.api.close.assert_awaited_once_with()
        else:
            assert hass.data[DOMAIN][entry.entry_id] is coordinator
            coordinator.api.close.assert_not_awaited()
            coordinator.api.disconnect_websocket.assert_not_awaited()
    finally:
        await coordinator.async_shutdown()
