"""Isolated configuration directories for lifecycle regression tests."""

import pytest


@pytest.fixture
def hass_config_dir(tmp_path):
    """Keep synthetic integration state separate for every test."""
    return str(tmp_path)
