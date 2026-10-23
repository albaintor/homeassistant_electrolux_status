"""Resource ownership regressions using the actual pinned SDK."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientSession, web
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pyelectroluxocp.webSocketClient import WebSocketClient

from custom_components.electrolux_status.util import get_electrolux_session


async def test_sdk_owned_http_session_closes_without_touching_ha(
    hass, aiohttp_server, monkeypatch, socket_enabled
):
    """A real vendor request must use a vendor-owned session and close it."""
    shared = async_get_clientsession(hass)
    closed = []
    original_close = ClientSession.close

    async def close_session(session):
        closed.append(session)
        await original_close(session)

    monkeypatch.setattr(ClientSession, "close", close_session)
    client = get_electrolux_session("test-account", "test-password", "us")
    client._get_formatted_user_token = AsyncMock(
        spec=client._get_formatted_user_token, return_value="Bearer synthetic-token"
    )

    async def appliances(_request):
        return web.json_response([])

    app = web.Application()
    app.router.add_get("/appliance/api/v2/appliances", appliances)
    server = await aiohttp_server(app)
    client._get_base_url = AsyncMock(
        spec=client._get_base_url, return_value=str(server.make_url("/"))
    )
    try:
        assert await client.get_appliances_list() == []
        await client.close()
        assert closed
        assert all(session.closed for session in closed)
        assert shared not in closed
        assert not shared.closed
        async with shared.get(
            server.make_url("/appliance/api/v2/appliances")
        ) as response:
            assert await response.json() == []
    finally:
        await client.close()


async def test_closing_one_client_preserves_another_clients_watch(hass):
    """SDK-created tasks must belong to their own API instance."""
    clients = [
        get_electrolux_session("test-account", "test-password", "us", None)
        for _ in range(2)
    ]
    started = asyncio.Event()
    cancelled = asyncio.Event()

    async def connect(_headers):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    transport = AsyncMock(spec=WebSocketClient)
    transport.connect.side_effect = connect
    clients[1]._get_websocket_client = AsyncMock(
        spec=clients[1]._get_websocket_client, return_value=transport
    )
    watch = asyncio.create_task(clients[1].connect_websocket(["test-appliance"]))
    try:
        await started.wait()
        await clients[0].close()
        await asyncio.sleep(0)
        assert not cancelled.is_set()
        await clients[1].close()
        assert cancelled.is_set()
    finally:
        watch.cancel()
        await asyncio.gather(watch, return_exceptions=True)
        for client in clients:
            await client.close()


async def test_late_sdk_task_never_starts_transport_after_close(hass):
    """Disconnect callbacks must not start fresh requests during teardown."""
    client = get_electrolux_session("test-account", "test-password", "us", None)
    transport = AsyncMock(spec=WebSocketClient)

    async def connect(_headers):
        await asyncio.Event().wait()

    transport.connect.side_effect = connect
    client._get_websocket_client = AsyncMock(
        spec=client._get_websocket_client, return_value=transport
    )
    try:
        await client.close()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(client.connect_websocket(["test-appliance"]), 0.1)
        transport.connect.assert_not_awaited()
    finally:
        await client.close()
