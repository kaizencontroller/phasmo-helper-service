from fastapi.testclient import TestClient

from phasmo_helper.app import app
from phasmo_helper import settings
from phasmo_helper.services.chat import ChatIdentity
from phasmo_helper.services.events import AppEvent, EventBus
from phasmo_helper.services.permissions import PermissionEngine
from phasmo_helper.services.state import default_state, write_state


client = TestClient(app)


def test_v581_workspace_pages_and_status():
    home = client.get("/phasmo")
    assert home.status_code == 200
    assert "Integrations" in home.text and "Export center" in home.text
    assert client.get("/phasmo/integrations?room=test-v581").status_code == 200
    assert client.get("/phasmo/export-center?room=test-v581").status_code == 200
    status = client.get("/api/phasmo/status?room=test-v581").json()
    assert status["applicationVersion"] == "v5.8.1"


def test_export_center_is_downloadable_and_sanitized():
    response = client.get("/api/phasmo/export-center?scope=configuration")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert "roomCode" not in response.text


def test_permission_inheritance_and_event_bus():
    moderator = ChatIdentity("mod", "Mod", "test", {"moderator"})
    explanation = PermissionEngine().explain(moderator)
    assert "viewer" in explanation["roles"]
    bus, seen = EventBus(), []
    bus.subscribe("EvidenceAdded", lambda event: seen.append(event.payload))
    bus.publish(AppEvent("EvidenceAdded", "test", 1, payload={"evidence": "orbs"}))
    assert seen == [{"evidence": "orbs"}]


def test_passcode_gate_has_timeout_and_refresh_guard(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "_STATE_DIR", tmp_path)
    state = default_state("locked-room")
    state["roomCode"] = "1234"
    write_state("locked-room", state)
    response = client.get("/phasmo/control?room=locked-room")
    assert response.status_code == 403
    assert "AbortController" in response.text
    assert "phasmoGateAttempt:" in response.text
    assert "temporarily unavailable" in response.text


def test_static_assets_are_compressed_and_cacheable():
    response = client.get("/phasmo/static/phasmo.js", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers["content-encoding"] == "gzip"
    assert "max-age=3600" in response.headers["cache-control"]
