"""Shared fixtures for the Electrolux Status tests.

The tests build appliances straight from the sanitized sample payloads in
``samples/`` so that entity generation is exercised against real capability
documents rather than against hand-written approximations of them.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = REPO_ROOT / "samples"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from custom_components.electrolux_status.api import (  # noqa: E402
    Appliance,
    Appliances,
    ElectroluxLibraryEntity,
)


def load_sample(model: str, name: str) -> Any:
    """Return one sanitized sample payload."""
    return json.loads((SAMPLES / model / f"{name}.json").read_text())


class StubConfigEntry:
    """Minimal stand-in for a Home Assistant config entry."""

    entry_id = "test-entry"


class StubCoordinator:
    """Minimal stand-in for ElectroluxCoordinator.

    ``ElectroluxEntity`` only needs ``api``, ``config_entry`` and ``data``
    during construction, so the tests avoid pulling in a full Home Assistant
    instance.
    """

    def __init__(self) -> None:
        """Initialize the stub."""
        self.api = None
        self.config_entry = StubConfigEntry()
        self.data: dict[str, Any] = {}


def build_appliance(model: str) -> Appliance:
    """Build and set up an Appliance from the sanitized samples for a model."""
    state = load_sample(model, "get_appliance_state")
    info = load_sample(model, "get_appliances_info")[0]
    capabilities = load_sample(model, "get_appliance_capabilities")
    appliance_id = state["applianceId"]

    coordinator = StubCoordinator()
    appliance = Appliance(
        coordinator=coordinator,
        name=state["applianceData"]["applianceName"],
        pnc_id=appliance_id,
        brand=info["brand"],
        model=info["model"],
        state=state,
    )
    coordinator.data["appliances"] = Appliances({appliance_id: appliance})
    appliance.setup(
        ElectroluxLibraryEntity(
            name=appliance.name,
            status=state.get("connectionState"),
            state=state,
            appliance_info=info,
            capabilities=capabilities,
        )
    )
    # The coordinator pushes the first status right after setup; without it the
    # entities have no appliance status to read values from.
    appliance.update(state)
    return appliance


def entity_by_path(appliance: Appliance, path: str):
    """Return the single entity generated for a capability path."""
    matches = [entity for entity in appliance.entities if entity.json_path == path]
    assert len(matches) == 1, f"expected exactly one entity for {path}, got {len(matches)}"
    return matches[0]


def paths(appliance: Appliance) -> set[str]:
    """Return every capability path the appliance generated an entity for."""
    return {entity.json_path for entity in appliance.entities}


@pytest.fixture
def hob() -> Appliance:
    """Return the AEG CCE84779CB induction hob (applianceType HB)."""
    return build_appliance("CCE84779CB")


@pytest.fixture
def fridge() -> Appliance:
    """Return a non-HB appliance, used to check for regressions."""
    return build_appliance("EHE6899SA")


@pytest.fixture
def washer() -> Appliance:
    """Return a non-HB appliance, used to check for regressions."""
    return build_appliance("EW7F3816DB")
