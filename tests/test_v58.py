from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from phasmo_helper import settings
from phasmo_helper.app import app
from phasmo_helper.content import get_registry
from phasmo_helper.core.data import GHOST_ALIASES, GHOST_NAMES
from phasmo_helper.services.chat import StreamerBotProvider
from phasmo_helper.services.dispatcher import CommandDispatcher
from phasmo_helper.services.investigations import session_summary, summary_csv, summary_markdown
from phasmo_helper.services.permissions import PermissionEngine, default_permissions, read_permissions
from phasmo_helper.services.state import default_state


def test_content_registry_and_deildegast():
    registry = get_registry()
    assert registry.valid, registry.report()
    assert len(registry.ghosts) == 30
    deildegast = next(item for item in registry.ghosts if item["id"] == "deildegast")
    assert deildegast["evidence"] == ["emf5", "writing", "dots"]
    assert GHOST_ALIASES["dildegeist"] == "Deildegast"
    assert "Deildegast" in GHOST_NAMES


def test_permission_dispatcher_denies_viewer_reset_and_allows_mod():
    state = default_state("dispatch")
    provider = StreamerBotProvider()
    viewer = provider.parse({"command": "!reset", "user": "viewer"})
    denied = CommandDispatcher(PermissionEngine(default_permissions())).dispatch(state, viewer)
    assert not denied.allowed
    moderator = provider.parse({"command": "!reset", "user": "mod", "isMod": True})
    allowed = CommandDispatcher(PermissionEngine(default_permissions())).dispatch(state, moderator)
    assert allowed.allowed


def test_viewers_can_log_behavior_but_disruptive_controls_stay_restricted():
    state = default_state("permission-safety")
    provider = StreamerBotProvider()
    dispatcher = CommandDispatcher(PermissionEngine(default_permissions()))

    behavior = dispatcher.dispatch(state, provider.parse({"command": "!be 12 yes", "user": "viewer"}))
    assert behavior.allowed
    assert behavior.state["behaviors"]["salt-footprints"] == "observed"

    for command in ("!select Wraith", "!notghost Spirit", "!ignore troublemaker", "!nextround"):
        denied = dispatcher.dispatch(state, provider.parse({"command": command, "user": "viewer"}))
        assert not denied.allowed, command

    moderator = dispatcher.dispatch(
        state,
        provider.parse({"command": "!select Wraith", "user": "mod", "isMod": True}),
    )
    assert moderator.allowed
    assert moderator.state["manualGhosts"]["selected"] == "Wraith"


def test_v2_permissions_migrate_to_safe_viewer_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "_STATE_DIR", tmp_path)
    (tmp_path / "__global_permissions.json").write_text(
        '{"schemaVersion":2,"matrix":{"behavior.log":["moderator"],"room.reset":["moderator"]}}',
        encoding="utf-8",
    )
    permissions = read_permissions()
    assert permissions["matrix"]["behavior.log"] == ["viewer"]
    assert permissions["matrix"]["ghost.override"] == ["moderator"]
    assert permissions["matrix"]["room.reset"] == ["moderator"]


def test_summary_exports():
    state = default_state("summary")
    state["map"] = "13 Willow Street"
    state["difficulty"] = "professional"
    state["guesses"] = {"viewer": "Deildegast"}
    state["contractResult"]["confirmedGhost"] = "Deildegast"
    summary = session_summary(state)
    assert summary["ghostStatistics"] == {"Deildegast": 1}
    assert "Investigation Summary" in summary_markdown(summary)
    assert "rounds_played" in summary_csv(summary)


def test_http_surfaces(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "_STATE_DIR", tmp_path)
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/ready").json()["content"]["valid"] is True
    assert client.get("/version").json()["game_version"] == "0.19.0.0"
    assert client.get("/api/phasmo/content/validation").json()["validation"]["counts"]["ghosts"] == 30
    page = client.get("/phasmo/encyclopedia?q=dildegeist")
    assert page.status_code == 200
    assert "Deildegast" in page.text
    response = client.post("/api/phasmo/state?room=willow-test", json={"objectives": {"emf-photo": 1}, "photos": {"emf-level-5": 1}})
    assert response.status_code == 200
    assert response.json()["state"]["objectives"]["emf-photo"] == 1


def test_frontend_roster_contains_deildegast():
    script = (Path(__file__).parents[1] / "phasmo_helper" / "static" / "phasmo.js").read_text(encoding="utf-8")
    assert "name:'Deildegast'" in script
    assert "deildegast-moved-items-slow" in script
