"""Authentication success must not log access-token values."""

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant
from pyelectroluxocp import OneAppApi

from custom_components.electrolux_status.coordinator import ElectroluxCoordinator


async def test_successful_login_keeps_access_token_out_of_logs(
    hass: HomeAssistant, caplog
):
    """Preserve successful authentication and token updates without logging secrets."""
    token = SimpleNamespace(token={"accessToken": "synthetic-access-token"})
    api = AsyncMock(spec=OneAppApi)
    api.get_user_token.return_value = token
    coordinator = ElectroluxCoordinator(hass, api, 3600, "test-account")
    coordinator.update_token_lifetime = AsyncMock(
        spec=coordinator.update_token_lifetime
    )

    with caplog.at_level(logging.DEBUG, logger="custom_components.electrolux_status"):
        assert await coordinator.async_login() is True

    coordinator.update_token_lifetime.assert_awaited_once_with(token)
    api.get_user_token.assert_awaited_once_with()
    assert "logged in successfully" in caplog.text
    assert "synthetic-access-token" not in caplog.text
