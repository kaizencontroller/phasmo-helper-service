from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict
from .. import settings

def _room_file_is_active(path: Path, now_ms: int | None = None) -> bool:
    if path.name.startswith("__global") or path.name.startswith("__"):
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        updated = int(data.get("lastActiveAt") or data.get("updatedAt") or 0)
    except Exception:
        return False
    if not updated:
        return False
    now_ms = now_ms or int(time.time() * 1000)
    return (now_ms - updated) < (settings._ROOM_TTL_SECONDS * 1000)


def cleanup_inactive_rooms() -> int:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    removed = 0
    now_ms = int(time.time() * 1000)
    for path in settings._STATE_DIR.glob("*.json"):
        if path.name.startswith("__global") or path.name.startswith("__"):
            continue
        if not _room_file_is_active(path, now_ms=now_ms):
            try:
                path.unlink()
                removed += 1
            except Exception:
                pass
    return removed


def active_room_summaries() -> list[Dict[str, Any]]:
    cleanup_inactive_rooms()
    rooms: list[Dict[str, Any]] = []
    now_ms = int(time.time() * 1000)
    for path in settings._STATE_DIR.glob("*.json"):
        if path.name.startswith("__global") or path.name.startswith("__"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        updated = int(data.get("lastActiveAt") or data.get("updatedAt") or 0)
        if not updated or (now_ms - updated) >= (settings._ROOM_TTL_SECONDS * 1000):
            continue
        rooms.append({
            "room": path.stem,
            "map": data.get("map", "unknown"),
            "difficulty": data.get("difficulty", "unknown"),
            "weather": data.get("weather", "unknown"),
            "setupComplete": bool(data.get("setupComplete")),
            "updatedAt": updated,
            "ageMinutes": round((now_ms - updated) / 60000, 1),
            "confirmedGhost": ((data.get("contractResult") or {}).get("confirmedGhost")),
            "guesses": len(data.get("guesses") or {}),
            "votes": len(data.get("votes") or {}),
            "locked": bool(str(data.get("roomCode") or "").strip()),
            "supportOptIn": bool(data.get("supportOptIn")),
            "supportChannel": str(data.get("supportChannel") or "")[:160],
        })
    rooms.sort(key=lambda item: item.get("updatedAt") or 0, reverse=True)
    return rooms
