"""Entry setup and credential-validation resource lifecycle."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import Event
from homeassistant.exceptions import ConfigEntryAuthFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import electrolux_status as integration
from custom_components.electrolux_status import config_flow
from custom_components.electrolux_status.const import DOMAIN
from custom_components.electrolux_status.coordinator import ElectroluxCoordinator


@pytest.fixture
async def setup_boundary(hass, monkeypatch):
    """Keep the actual API/coordinator and replace only startup network operations."""
    clients, close_calls, session_args, stop_callbacks = [], [], [], []
    original_factory = integration.get_electrolux_session
    original_listen = type(hass.bus).async_listen_once

    def factory(*args):
        client = original_factory(*args)
        close = client.close

        async def close_client():
            close_calls.append(client)
            await close()

        client.close = close_client
        clients.append(client)
        session_args.append(args[3] if len(args) > 3 else None)
        return client

    def listen(bus, event_type, callback, *args, **kwargs):
        if bus is hass.bus and event_type == EVENT_HOMEASSISTANT_STOP:
            stop_callbacks.append(callback)
            return lambda: None
        return original_listen(bus, event_type, callback, *args, **kwargs)

    monkeypatch.setattr(integration, "get_electrolux_session", factory)
    monkeypatch.setattr(config_flow, "get_electrolux_session", factory)
    monkeypatch.setattr(type(hass.bus), "async_listen_once", listen)
    monkeypatch.setattr(
        integration,
        "_async_remove_old_device_identifiers",
        Mock(spec=integration._async_remove_old_device_identifiers),
    )
    for method in (
        "get_stored_token",
        "async_login",
        "setup_entities",
        "async_config_entry_first_refresh",
    ):
        monkeypatch.setattr(
            ElectroluxCoordinator,
            method,
            AsyncMock(spec=getattr(ElectroluxCoordinator, method), return_value=True),
        )
    monkeypatch.setattr(
        ElectroluxCoordinator,
        "listen_websocket",
        Mock(spec=ElectroluxCoordinator.listen_websocket),
    )
    monkeypatch.setattr(hass.config_entries, "async_forward_entry_setups", AsyncMock())
    entry = MockConfigEntry(
        domain=DOMAIN, data={"username": "test-account", "password": "test-password"}
    )
    entry.add_to_hass(hass)
    yield entry, clients, close_calls, session_args, stop_callbacks
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator:
        await coordinator.async_shutdown()
    for client in clients:
        await client.close()


async def test_stop_callback_accepts_event_and_shuts_down(hass, setup_boundary):
    """Home Assistant supplies an Event to the registered stop listener."""
    entry, clients, close_calls, session_args, callbacks = setup_boundary
    assert await integration.async_setup_entry(hass, entry)
    assert len(callbacks) == 1
    await callbacks[0](Event(EVENT_HOMEASSISTANT_STOP))
    assert close_calls == clients
    assert session_args == [None]


@pytest.mark.parametrize("stage", ["login", "entities", "platforms", "cancelled"])
async def test_failed_setup_closes_only_its_client(hass, setup_boundary, stage):
    """Authentication, startup exceptions and cancellation must unwind the client."""
    entry, clients, close_calls, _, _ = setup_boundary
    other = object()
    hass.data[DOMAIN] = {"other-entry": other}
    expected = RuntimeError
    if stage == "login":
        ElectroluxCoordinator.async_login.return_value = False
        expected = ConfigEntryAuthFailed
    elif stage == "entities":
        ElectroluxCoordinator.setup_entities.side_effect = RuntimeError(
            "synthetic setup failure"
        )
    elif stage == "platforms":
        hass.config_entries.async_forward_entry_setups.side_effect = RuntimeError(
            "synthetic platform failure"
        )
    else:
        ElectroluxCoordinator.async_login.side_effect = asyncio.CancelledError
        expected = asyncio.CancelledError
    with pytest.raises(expected):
        await integration.async_setup_entry(hass, entry)
    assert hass.data[DOMAIN] == {"other-entry": other}
    assert close_calls == clients


@pytest.mark.parametrize("outcome", ["success", "failure", "cancelled"])
async def test_credential_validation_always_closes_client(
    hass, setup_boundary, monkeypatch, outcome
):
    """The temporary validator must not retain a client or borrow HA's session."""
    _, clients, close_calls, session_args, _ = setup_boundary
    original_factory = config_flow.get_electrolux_session

    def factory(*args):
        client = original_factory(*args)
        client.get_appliances_list = AsyncMock(spec=client.get_appliances_list)
        if outcome == "failure":
            client.get_appliances_list.side_effect = RuntimeError(
                "synthetic validation failure"
            )
        elif outcome == "cancelled":
            client.get_appliances_list.side_effect = asyncio.CancelledError
        return client

    monkeypatch.setattr(config_flow, "get_electrolux_session", factory)
    flow = config_flow.ElectroluxStatusFlowHandler()
    flow.hass = hass
    if outcome == "cancelled":
        with pytest.raises(asyncio.CancelledError):
            await flow._test_credentials("test-account", "test-password", "us")
    else:
        assert await flow._test_credentials("test-account", "test-password", "us") is (
            outcome == "success"
        )
    assert close_calls == clients
    assert session_args == [None]


async def test_reload_does_not_setup_after_refused_unload(hass, monkeypatch):
    """Delegate reload coordination instead of creating a second live client."""
    entry = MockConfigEntry(domain=DOMAIN)
    native_reload = AsyncMock(return_value=False)
    setup = AsyncMock()
    monkeypatch.setattr(hass.config_entries, "async_reload", native_reload)
    monkeypatch.setattr(
        integration, "async_unload_entry", AsyncMock(return_value=False)
    )
    monkeypatch.setattr(integration, "async_setup_entry", setup)
    await integration.async_reload_entry(hass, entry)
    setup.assert_not_awaited()
    native_reload.assert_awaited_once_with(entry.entry_id)
