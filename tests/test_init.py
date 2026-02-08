"""Test the Electrolux Status integration setup."""

from custom_components.electrolux_status.const import DOMAIN


def test_domain():
    """Test that the domain is correct."""
    assert DOMAIN == "electrolux_status"
