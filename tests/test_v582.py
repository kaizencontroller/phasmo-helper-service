from phasmo_helper.content import get_registry
from phasmo_helper.core.data import GHOST_ALIASES, MAP_ALIASES
from phasmo_helper.services.commands import apply_command
from phasmo_helper.services.state import default_state
from fastapi.testclient import TestClient
from phasmo_helper.app import app


client = TestClient(app)


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


def test_weather_and_response_condition_are_on_control_step():
    page = client.get("/phasmo/round?room=conditions-test")
    assert page.status_code == 200
    setup_markup = page.text.split('id="setupPanel"', 1)[1].split('class="panel tracker-panel"', 1)[0]
    assert "Number of Players" in setup_markup
    assert "Game Level / Difficulty" in setup_markup
    assert "Weather" not in setup_markup
    assert "Ghost responds to" not in setup_markup
    assert 'class="panel control-context-panel"' in page.text
    assert "Investigation Conditions" in page.text
    assert "Live Hunt Risk" in page.text
    assert 'id="newRoundModal"' in page.text
    assert "/phasmo/static/phasmo.js?v=5.8.7-dashboard" in page.text
    assert 'id="respondsText" style="display:none!important"' in page.text
    assert 'id="layoutToggle"' in page.text
    assert "Highest threshold among remaining candidates." in page.text


def test_next_round_shortcut_resets_and_applies_new_contract_atomically():
    room = "v582-next-round-test"
    client.post(
        f"/api/phasmo/state?room={room}",
        json={"createRoom": True},
    )
    client.post(
        f"/api/phasmo/state?room={room}",
        json={"setupComplete": True, "map": "13 Willow Street", "difficulty": "amateur", "playerCount": 2, "weather": "fog"},
    )
    response = client.post(
        f"/api/phasmo/state?room={room}",
        json={"nextRound": True, "map": "Point Hope Restricted", "difficulty": "professional", "playerCount": 4, "setupComplete": True},
    )
    assert response.status_code == 200
    state = response.json()["state"]
    assert state["map"] == "Point Hope Restricted"
    assert state["difficulty"] == "professional"
    assert state["playerCount"] == 4
    assert state["setupComplete"] is True
    assert state["weather"] == "unknown"
