"""Test the Electrolux Status coordinator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.electrolux_status.models import Appliance, Appliances


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_coordinator(mock_api_client):
    """Create a mock coordinator with the necessary attributes."""
    from custom_components.electrolux_status.coordinator import ElectroluxCoordinator

    # Mock the DataUpdateCoordinator.__init__ to avoid HA setup issues
    with patch(
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator.__init__",
        return_value=None,
    ):
        coord = ElectroluxCoordinator.__new__(ElectroluxCoordinator)
        coord.api = mock_api_client
        coord.platforms = []
        coord.renew_interval = 7200
        coord.data = {}  # Initialize as empty dict instead of None
        return coord


def test_coordinator_attributes(mock_coordinator, mock_api_client):
    """Test that the coordinator has the expected attributes."""
    assert mock_coordinator.api == mock_api_client
    assert mock_coordinator.platforms == []
    assert mock_coordinator.renew_interval == 7200


@pytest.mark.asyncio
async def test_async_update_data_success(mock_coordinator, mock_api_client):
    """Test successful data update with mocked API response."""
    # Create mock appliance data
    mock_appliance_state = {
        "properties": {
            "reported": {
                "connectivityState": "connected",
                "applianceMode": "normal",
                "temperature": 25.0,
                "powerState": "on",
            }
        }
    }

    # Mock the API to return the appliance state
    mock_api_client.get_appliance_state = AsyncMock(return_value=mock_appliance_state)

    # Create a mock appliance in the coordinator data
    mock_appliance = MagicMock(spec=Appliance)
    mock_appliance.pnc_id = "test_appliance_1"
    mock_appliance.update = MagicMock()

    mock_appliances = MagicMock(spec=Appliances)
    mock_appliances.get_appliances.return_value = {"test_appliance_1": mock_appliance}

    # Set up coordinator data
    mock_coordinator.data = {"appliances": mock_appliances}

    # Call the update method
    result = await mock_coordinator._async_update_data()

    # Verify the API was called correctly
    mock_api_client.get_appliance_state.assert_called_once_with("test_appliance_1")

    # Verify the appliance was updated with the correct data
    mock_appliance.update.assert_called_once_with(mock_appliance_state)

    # Verify the result contains the expected data
    assert result == mock_coordinator.data


@pytest.mark.asyncio
async def test_async_update_data_api_error(mock_coordinator, mock_api_client):
    """Test data update when API call fails."""
    # Mock the API to raise an exception
    mock_api_client.get_appliance_state = AsyncMock(side_effect=Exception("API Error"))

    # Create a mock appliance
    mock_appliance = MagicMock(spec=Appliance)
    mock_appliance.pnc_id = "test_appliance_1"

    mock_appliances = MagicMock(spec=Appliances)
    mock_appliances.get_appliances.return_value = {"test_appliance_1": mock_appliance}

    # Set up coordinator data
    mock_coordinator.data = {"appliances": mock_appliances}

    # Call the update method and expect it to raise UpdateFailed
    from homeassistant.helpers.update_coordinator import UpdateFailed

    with pytest.raises(UpdateFailed):
        await mock_coordinator._async_update_data()


@pytest.mark.asyncio
async def test_async_update_data_auth_error(mock_coordinator, mock_api_client):
    """Test data update when authentication fails."""
    # Mock the API to raise an exception with auth keywords
    mock_api_client.get_appliance_state = AsyncMock(
        side_effect=Exception("401 Unauthorized")
    )

    # Create a mock appliance
    mock_appliance = MagicMock(spec=Appliance)
    mock_appliance.pnc_id = "test_appliance_1"

    mock_appliances = MagicMock(spec=Appliances)
    mock_appliances.get_appliances.return_value = {"test_appliance_1": mock_appliance}

    # Set up coordinator data
    mock_coordinator.data = {"appliances": mock_appliances}

    # Call the update method and expect it to raise ConfigEntryAuthFailed
    from homeassistant.exceptions import ConfigEntryAuthFailed

    with pytest.raises(ConfigEntryAuthFailed):
        await mock_coordinator._async_update_data()


@pytest.mark.asyncio
async def test_async_update_data_multiple_appliances(mock_coordinator, mock_api_client):
    """Test data update with multiple appliances."""
    # Create mock appliance states
    mock_state_1 = {
        "properties": {"reported": {"powerState": "on", "temperature": 20.0}}
    }
    mock_state_2 = {
        "properties": {"reported": {"powerState": "off", "temperature": 15.0}}
    }

    # Mock the API to return different states for different appliances
    mock_api_client.get_appliance_state = AsyncMock(
        side_effect=[mock_state_1, mock_state_2]
    )

    # Create mock appliances
    mock_appliance_1 = MagicMock(spec=Appliance)
    mock_appliance_1.pnc_id = "appliance_1"
    mock_appliance_1.update = MagicMock()

    mock_appliance_2 = MagicMock(spec=Appliance)
    mock_appliance_2.pnc_id = "appliance_2"
    mock_appliance_2.update = MagicMock()

    mock_appliances = MagicMock(spec=Appliances)
    mock_appliances.get_appliances.return_value = {
        "appliance_1": mock_appliance_1,
        "appliance_2": mock_appliance_2,
    }

    # Set up coordinator data
    mock_coordinator.data = {"appliances": mock_appliances}

    # Call the update method
    result = await mock_coordinator._async_update_data()

    # Verify the API was called for both appliances
    assert mock_api_client.get_appliance_state.call_count == 2
    mock_api_client.get_appliance_state.assert_any_call("appliance_1")
    mock_api_client.get_appliance_state.assert_any_call("appliance_2")

    # Verify both appliances were updated
    mock_appliance_1.update.assert_called_once_with(mock_state_1)
    mock_appliance_2.update.assert_called_once_with(mock_state_2)

    # Verify the result
    assert result == mock_coordinator.data
