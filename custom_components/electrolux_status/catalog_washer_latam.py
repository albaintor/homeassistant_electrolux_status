"""Defined catalog of entities for LATAM washing machines.

LATAM appliances report a `latamUserSelections` container whose attributes carry no `values`,
no `min`, no `max` and no `step`. Without an entry here every one of them becomes a bare
`number` spinning from 0 to 100, including the wash program, the water level and four options
that are really on/off.

The keys below are the flattened capability names, the same `container/attribute` form the API
already uses for `iceMaker/executeCommand` and `networkInterface/swVersion`.

Two layers. WASHER_LATAM goes into CATALOG_BASE: the `latamUserSelections` and
`latamApplianceCareAndMaintenance` capabilities exist only on LATAM appliances, so those entries
are inert everywhere else, and what they do (on/off options as switches, counters as sensors) is
not specific to one model. WASHER_LWI13 goes into CATALOG_MODEL under the model the appliance info
reports: program names, wash levels, the defaults written with each program and the options each
program accepts were all read from that washer, and another model may number them differently.

Verified against an LWI13_127V_MVT. The program ids were read back one by one from the appliance,
and the names come from the program picker in the Home+ app. Ids 3 and 4 are accepted by the
appliance but appear in neither the picker nor the panel, so they are deliberately left out: the
select falls back to showing the raw value for them rather than carrying a guessed label.
"""

from homeassistant.const import EntityCategory, Platform

from .model import ElectroluxDevice

# Why every entry that changes type sets entity_platform: Appliance.get_entity decides the entity
# type from the raw API capability before it merges the catalog `values` in, and only lets the
# catalog override that type through device_class or entity_platform. The API sends these
# attributes as bare readwrite numbers, so without entity_platform they stay numbers no matter
# what the catalog says.

# Wash programs, by the id the appliance reports in latamUserSelections.programId.
# Ids 3 and 4 exist and are accepted, but are unnamed in the app and on the panel.
WASHER_LWI13_PROGRAMS: dict[int, str] = {
    0: "DUVET",
    1: "HEAVY_JEANS",
    2: "STAIN_REMOVAL",
    5: "MACHINE_CLEAN",
    6: "DARKS",
    7: "COLORS",
    8: "WHITES",
    9: "DELICATE_SPORT",
    10: "NORMAL",
    11: "QUICK",
}

# Water levels, by the id reported in latamUserSelections.washLevel. The appliance rejects
# 0 and anything above 9. The app shows the even ids as steps between two named levels
# ("extra low / low"), which the _TO_ tokens keep.
WASHER_LWI13_WASH_LEVELS: dict[int, str] = {
    1: "EXTRA_LOW",
    2: "EXTRA_LOW_TO_LOW",
    3: "LOW",
    4: "LOW_TO_MEDIUM",
    5: "MEDIUM",
    6: "MEDIUM_TO_HIGH",
    7: "HIGH",
    8: "HIGH_TO_DUVET",
    9: "DUVET",
}


# What the Home+ app writes along with each program. Read back from the appliance after picking
# every program in the app, one at a time. The app sets extra rinse and phaseAdvance per program.
# Extra rinse was already off when ids 2, 5, 8 and 11 were picked, so off there is inferred from
# the app writing it for every other program. Turbo agitation, turbo spin, water reuse and the
# wash level are not written: the app left them alone except for turning turbo agitation off on
# Whites, which a single pass cannot explain, so the current value is kept.
WASHER_LWI13_PROGRAM_DEFAULTS: dict[int, dict[str, int]] = {
    0: {"rinse": 1, "phaseAdvance": 2},
    1: {"rinse": 0, "phaseAdvance": 2},
    2: {"rinse": 0, "phaseAdvance": 1},
    5: {"rinse": 0, "phaseAdvance": 1},
    6: {"rinse": 1, "phaseAdvance": 2},
    7: {"rinse": 0, "phaseAdvance": 2},
    8: {"rinse": 0, "phaseAdvance": 1},
    9: {"rinse": 1, "phaseAdvance": 2},
    10: {"rinse": 0, "phaseAdvance": 2},
    11: {"rinse": 0, "phaseAdvance": 3},
}

# Programs under which the appliance accepts each turbo option. Probed by turning the option on
# under every program with the other options off: elsewhere the write is silently ignored. Extra
# rinse and water reuse are accepted under all of them, and so is every wash level.
WASHER_LWI13_TURBO_AGITATION_PROGRAMS = frozenset({1, 2, 8, 10, 11})
WASHER_LWI13_TURBO_SPIN_PROGRAMS = frozenset({0, 1, 2, 6, 7, 8, 10, 11})

# Appliance states in which the program defaults are written. They include phaseAdvance, which a
# running or paused cycle may act on, so mid-cycle the program is written alone.
WASHER_LWI13_PROGRAM_STATES = frozenset({"OFF", "IDLE", "READY_TO_START", "END_OF_CYCLE"})


def _as_values(mapping: dict[int, str]) -> dict[str, dict]:
    """Turn an id to token mapping into the `values` dict the api module expects."""
    return {token: {} for token in mapping.values()}


def _selection(
    name: str,
    key: str,
    mapping: dict[int, str],
    icon: str,
    defaults: dict | None = None,
    defaults_when: tuple[str, frozenset] | None = None,
) -> ElectroluxDevice:
    """Build a catalog entry for an id the appliance reports and accepts as an integer."""
    return ElectroluxDevice(
        friendly_name=name,
        translation_key=key,
        capability_info={
            "access": "readwrite",
            "type": "number",
            "values": _as_values(mapping),
        },
        value_mapping=mapping,
        value_mapping_on_write=True,
        write_defaults=defaults or {},
        write_defaults_when=defaults_when,
        entity_platform=Platform.SELECT,
        entity_icon=icon,
    )


# An option that is really a toggle. The appliance reports and accepts 0 and 1. No `values` on
# purpose: switch.py posts "ON"/"OFF" strings whenever the capability has values, and these
# attributes want the numbers.
def _option(name: str, key: str, icon: str, programs: frozenset | None = None) -> ElectroluxDevice:
    """Build a catalog entry for a 0/1 wash option, unavailable under programs that ignore it."""
    return ElectroluxDevice(
        friendly_name=name,
        translation_key=key,
        entity_platform=Platform.SWITCH,
        entity_icon=icon,
        available_when=("latamUserSelections/programId", programs) if programs else None,
    )


# Cycles since a part was last serviced. The API marks these readwrite, but they are meters.
# They read the same as totalCycleCounter until someone resets them, so they go to diagnostics.
def _counter(name: str, key: str, icon: str) -> ElectroluxDevice:
    """Build a catalog entry for a maintenance counter."""
    return ElectroluxDevice(
        friendly_name=name,
        translation_key=key,
        entity_platform=Platform.SENSOR,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_icon=icon,
    )


# Any LATAM washer: on/off options become switches, counters become diagnostic sensors.
WASHER_LATAM: dict[str, ElectroluxDevice] = {
    "latamUserSelections/rinse": _option("Extra rinse", "latam_extra_rinse", "mdi:water-sync"),
    "latamUserSelections/turboAgitation": _option("Turbo agitation", "latam_turbo_agitation", "mdi:rotate-3d-variant"),
    "latamUserSelections/turboDrying": _option("Turbo spin", "latam_turbo_spin", "mdi:weather-windy"),
    "latamUserSelections/waterReuse": _option("Water reuse", "latam_water_reuse", "mdi:recycle"),
    # Named after the attribute. The Home+ app writes a per program value here (see
    # WASHER_LWI13_PROGRAM_DEFAULTS), and a running cycle has been advanced by pausing, writing 1
    # and resuming, which belongs in a script rather than in a single button press.
    "latamUserSelections/phaseAdvance": ElectroluxDevice(
        friendly_name="Advance phase",
        translation_key="latam_advance_phase",
        entity_category=EntityCategory.CONFIG,
        entity_icon="mdi:skip-next",
    ),
    "latamApplianceCareAndMaintenance/counterBasket": _counter(
        "Cycles since basket service", "latam_counter_basket", "mdi:washing-machine"
    ),
    "latamApplianceCareAndMaintenance/counterHose": _counter(
        "Cycles since hose service", "latam_counter_hose", "mdi:pipe"
    ),
    "latamApplianceCareAndMaintenance/counterLint": _counter(
        "Cycles since lint filter service", "latam_counter_lint", "mdi:air-filter"
    ),
    "latamApplianceCareAndMaintenance/counterPreventive": _counter(
        "Cycles since preventive service", "latam_counter_preventive", "mdi:wrench-clock"
    ),
}

# The LWI13 on top of that, keyed in CATALOG_MODEL by the model its appliance info reports.
# Entries here replace the WASHER_LATAM entries with the same key.
WASHER_LWI13: dict[str, ElectroluxDevice] = {
    "latamUserSelections/programId": _selection(
        "Program",
        "latam_program",
        WASHER_LWI13_PROGRAMS,
        "mdi:washing-machine",
        WASHER_LWI13_PROGRAM_DEFAULTS,
        ("applianceState", WASHER_LWI13_PROGRAM_STATES),
    ),
    # "Wash level", not "Water level": the appliance already has a read only waterLevel sensor
    "latamUserSelections/washLevel": _selection(
        "Wash level", "latam_wash_level", WASHER_LWI13_WASH_LEVELS, "mdi:cup-water"
    ),
    "latamUserSelections/turboAgitation": _option(
        "Turbo agitation", "latam_turbo_agitation", "mdi:rotate-3d-variant", WASHER_LWI13_TURBO_AGITATION_PROGRAMS
    ),
    "latamUserSelections/turboDrying": _option(
        "Turbo spin", "latam_turbo_spin", "mdi:weather-windy", WASHER_LWI13_TURBO_SPIN_PROGRAMS
    ),
}
