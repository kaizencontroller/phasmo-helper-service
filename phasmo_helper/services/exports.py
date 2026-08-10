from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from typing import Any

from .. import settings
from ..content import get_registry
from ..core.config import _read_config
from .investigations import analytics_from_states
from .permissions import read_permissions
from .reports import export_bug_tracker


def room_states() -> list[dict[str, Any]]:
    states = []
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    for path in settings._STATE_DIR.glob("*.json"):
        if path.name.startswith("__global_"):
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            state.pop("roomCode", None)
            state.pop("supportContact", None)
            states.append(state)
        except Exception:
            continue
    return states


def export_payload(scope: str = "complete") -> dict[str, Any]:
    states = room_states()
    base = {
        "schemaVersion": 1, "scope": scope, "applicationVersion": settings._APP_VERSION,
        "platformVersion": settings._PLATFORM_VERSION, "gameVersion": get_registry().game_version.get("supportedVersion"),
    }
    if scope in {"complete", "backup"}:
        base.update({"rooms": states, "configuration": _read_config(), "permissions": read_permissions(), "analytics": analytics_from_states(states), "bugReports": export_bug_tracker(), "contentValidation": get_registry().report()})
    elif scope == "configuration":
        base.update({"configuration": _read_config(), "permissions": read_permissions()})
    elif scope == "analytics":
        base["analytics"] = analytics_from_states(states)
    elif scope == "bugs":
        base["bugReports"] = export_bug_tracker()
    elif scope == "release":
        manifest_path = Path(__file__).resolve().parents[2] / ".kaizen" / "manifest.json"
        base.update({"manifest": json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}, "contentValidation": get_registry().report()})
    else:
        raise ValueError(f"unknown export scope: {scope}")
    return base


def export_zip() -> bytes:
    payload = export_payload("complete")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                archive.writestr(f"{key}.json", json.dumps(value, indent=2, ensure_ascii=False))
        archive.writestr("README.txt", "Phasmo Helper complete backup. Tokens, room passcodes, and support contacts are excluded.\n")
    return output.getvalue()
