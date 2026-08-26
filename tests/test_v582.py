from phasmo_helper.content import get_registry
from phasmo_helper.core.data import GHOST_ALIASES, MAP_ALIASES
from phasmo_helper.services.commands import apply_command
from phasmo_helper.services.state import default_state


def test_qol2_registry_and_restricted_maps():
    registry = get_registry()
    assert registry.valid, registry.report()
    assert registry.game_version["supportedVersion"] == "0.19.0.0"
    maps = {item["id"]: item for item in registry.items("maps.json")}
    assert maps["point-hope-restricted"]["size"] == "small"
    assert maps["prison-restricted"]["variantSelection"] == "random"
    assert maps["brownstone-restricted"]["size"] == "medium"


def test_restricted_map_commands_and_ui_aliases():
    state = default_state("qol2")
    for command, expected in [
        ("!map point-restricted", "Point Hope Restricted"),
        ("!map prison-restricted", "Prison Restricted"),
        ("!map school-restricted", "Brownstone High School Restricted"),
    ]:
        state, _ = apply_command(state, command, "tester")
        assert state["map"] == expected
    assert MAP_ALIASES["brownstone-r"] == "Brownstone High School Restricted"


def test_deildegast_and_willow_rework_remain_valid():
    registry = get_registry()
    ghost = next(item for item in registry.ghosts if item["id"] == "deildegast")
    assert ghost["evidence"] == ["emf5", "writing", "dots"]
    assert GHOST_ALIASES["dildegeist"] == "Deildegast"
    willow = registry.rooms["willow.json"]
    assert willow["mapId"] == "willow"
    assert any(room["id"] == "willow-laundry-room" and "utility-room" in room["legacyIds"] for room in willow["items"])
