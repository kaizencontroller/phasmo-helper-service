from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from .. import settings


def _banner_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._SITE_BANNER_FILE


def default_banner() -> Dict[str, Any]:
    return {"enabled": False, "message": "", "level": "notice", "updatedAt": 0, "expiresAt": 0}


def read_banner() -> Dict[str, Any]:
    data = default_banner()
    try:
        loaded = json.loads(_banner_path().read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data.update(loaded)
    except Exception:
        pass
    try:
        exp = int(data.get("expiresAt") or 0)
    except Exception:
        exp = 0
    if exp and exp < int(time.time() * 1000):
        data["enabled"] = False
    data["message"] = str(data.get("message") or "")[:500]
    data["level"] = data.get("level") if data.get("level") in {"notice", "maintenance", "warning"} else "notice"
    return data


def write_banner(patch: Dict[str, Any]) -> Dict[str, Any]:
    data = read_banner()
    if "enabled" in patch:
        data["enabled"] = bool(patch.get("enabled"))
    if "message" in patch:
        data["message"] = str(patch.get("message") or "")[:500]
    if "level" in patch:
        data["level"] = patch.get("level") if patch.get("level") in {"notice", "maintenance", "warning"} else "notice"
    if "expiresAt" in patch:
        try:
            data["expiresAt"] = max(0, int(float(patch.get("expiresAt") or 0)))
        except Exception:
            data["expiresAt"] = 0
    data["updatedAt"] = int(time.time() * 1000)
    _banner_path().write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data
