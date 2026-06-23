from __future__ import annotations

import json
import re
import time
from typing import Any, Dict
from .. import settings
from .state import _room_name


def _profiles_path():
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / "__global_streamerbot_profiles.json"


def _clean_key(raw: str | None) -> str:
    value = (raw or "").strip().lower().lstrip("@")
    value = re.sub(r"[^a-z0-9_.-]+", "-", value).strip("-")[:80]
    return value


def streamer_key(channel: str | None = None, bot_account: str | None = None, user: str | None = None) -> str:
    """Stable profile key for Streamer.bot default-room routing.

    Channel is preferred because the same bot can serve multiple channels.
    Bot account is next best. User is only a fallback for local testing.
    """
    for prefix, raw in (("channel", channel), ("bot", bot_account), ("user", user)):
        key = _clean_key(raw)
        if key:
            return f"{prefix}:{key}"
    return "default"


def read_profiles() -> Dict[str, Any]:
    try:
        data = json.loads(_profiles_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_profiles(profiles: Dict[str, Any]) -> Dict[str, Any]:
    _profiles_path().write_text(json.dumps(profiles, indent=2, sort_keys=True), encoding="utf-8")
    return profiles


def get_profile(channel: str | None = None, bot_account: str | None = None, user: str | None = None) -> Dict[str, Any]:
    key = streamer_key(channel=channel, bot_account=bot_account, user=user)
    profile = read_profiles().get(key) or {}
    return profile if isinstance(profile, dict) else {}


def get_default_room(channel: str | None = None, bot_account: str | None = None, user: str | None = None) -> str:
    room = (get_profile(channel=channel, bot_account=bot_account, user=user).get("defaultRoom") or "").strip()
    return _room_name(room) if room else ""


def set_default_room(room: str, channel: str | None = None, bot_account: str | None = None, user: str | None = None) -> Dict[str, Any]:
    safe_room = _room_name(room)
    key = streamer_key(channel=channel, bot_account=bot_account, user=user)
    profiles = read_profiles()
    current = profiles.get(key) if isinstance(profiles.get(key), dict) else {}
    current.update({
        "key": key,
        "defaultRoom": safe_room,
        "channel": (channel or "")[:160],
        "botAccount": (bot_account or "")[:160],
        "updatedBy": (user or "")[:160],
        "updatedAt": int(time.time() * 1000),
    })
    profiles[key] = current
    write_profiles(profiles)
    return current


def parse_room_command(command: str | None) -> str:
    text = (command or "").strip()
    if not text:
        return ""
    parts = text.split()
    if not parts:
        return ""
    first = parts[0].lower().lstrip("!")
    # Supported forms:
    #   !phasmo-room kaizen
    #   !phasmo_room kaizen
    #   !setphasmo kaizen
    #   !setphasmo-room kaizen
    #   !setroom kaizen
    #   !phasmo room kaizen
    if first in {"phasmo-room", "phasmo_room", "setphasmo", "setphasmo-room", "setphasmo_room", "setroom", "room"} and len(parts) >= 2:
        return _room_name(parts[1])
    if first == "phasmo" and len(parts) >= 3 and parts[1].lower() in {"room", "setroom", "set-room"}:
        return _room_name(parts[2])
    return ""
