"""
Local Streamer.bot bridge for the Phasmophobia decision tool.

Run locally on the streaming PC:
    pip install flask requests
    set RAILWAY_BASE_URL=https://your-railway-app.up.railway.app
    set PHASMO_ROOM=kaizen
    set PHASMO_ADMIN_TOKEN=your-token-if-set
    set PHASMO_OWNER_USERS=your_twitch_username
    python local_phasmo_streamerbot_bridge.py

Streamer.bot Web Request action:
    URL: http://127.0.0.1:8765/streamerbot/phasmo
    Method: POST
    Content-Type: application/json
    Body:
      {
        "command":"%rawInput%",
        "user":"%user%",
        "isMod":"%isMod%",
        "isBroadcaster":"%isBroadcaster%"
      }

Allowed from normal, non-ignored chatters by default:
    !ev emf yes/no/unknown
    !ev dots yes/no/unknown
    !ev freezing yes/no/unknown
    !ev orb yes/no/unknown
    !ev writing yes/no/unknown
    !ev box yes/no/unknown
    !ev uv yes/no/unknown

Admin-only commands:
    !responds alone/everyone/unknown
    !mode 3/2/1/0
    !reset
    !ignore USERNAME
    !unignore USERNAME
    !ignored
    !mods

Owner-only commands:
    !modadd USERNAME
    !modremove USERNAME

Behavior commands are intentionally blocked in this bridge for now:
    !b ...
    !beh ...
    !behavior ...
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

RAILWAY_BASE_URL = os.getenv("RAILWAY_BASE_URL", "").rstrip("/")
PHASMO_ROOM = os.getenv("PHASMO_ROOM", "kaizen")
PHASMO_ADMIN_TOKEN = os.getenv("PHASMO_ADMIN_TOKEN", "")
PHASMO_BRIDGE_PORT = int(os.getenv("PHASMO_BRIDGE_PORT", "8765"))

# If true, anyone not ignored may submit evidence commands. Recommended for stream participation.
# Set PHASMO_PUBLIC_EVIDENCE=false to make evidence updates admin-only.
PHASMO_PUBLIC_EVIDENCE = os.getenv("PHASMO_PUBLIC_EVIDENCE", "true").strip().lower() in {"1", "true", "yes", "on"}

MOD_FILE = Path(os.getenv("PHASMO_MOD_FILE", "phasmo_bridge_moderation.json"))
OWNER_USERS = set()
ADMIN_USERS = set()


def _norm_user(value: str | None) -> str:
    return (value or "").strip().lstrip("@").lower()


def _split_users(raw: str | None) -> set[str]:
    return {_norm_user(x) for x in (raw or "").replace(";", ",").split(",") if _norm_user(x)}


OWNER_USERS |= (_split_users(os.getenv("PHASMO_OWNER_USERS")) or {"kaizencontroller"})
ADMIN_USERS |= _split_users(os.getenv("PHASMO_ADMIN_USERS"))


def _default_mod_data() -> Dict[str, Any]:
    return {"admins": sorted(ADMIN_USERS), "ignored": []}


def load_mod_data() -> Dict[str, Any]:
    if not MOD_FILE.exists():
        data = _default_mod_data()
        save_mod_data(data)
        return data
    try:
        data = json.loads(MOD_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = _default_mod_data()
    data.setdefault("admins", [])
    data.setdefault("ignored", [])
    # Env admins always count even if not in file.
    admins = {_norm_user(x) for x in data.get("admins", []) if _norm_user(x)} | ADMIN_USERS
    data["admins"] = sorted(admins)
    data["ignored"] = sorted({_norm_user(x) for x in data.get("ignored", []) if _norm_user(x)})
    return data


def save_mod_data(data: Dict[str, Any]) -> None:
    data["admins"] = sorted({_norm_user(x) for x in data.get("admins", []) if _norm_user(x)} | ADMIN_USERS)
    data["ignored"] = sorted({_norm_user(x) for x in data.get("ignored", []) if _norm_user(x)})
    MOD_FILE.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _extract_payload() -> Dict[str, Any]:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    raw = request.get_data(as_text=True) or ""
    return {"command": raw}


def _extract_command(payload: Dict[str, Any]) -> str:
    return (
        payload.get("command")
        or payload.get("rawInput")
        or payload.get("message")
        or payload.get("args")
        or ""
    ).strip()


def _user_from_payload(payload: Dict[str, Any]) -> str:
    return _norm_user(
        payload.get("user")
        or payload.get("username")
        or payload.get("displayName")
        or payload.get("userName")
    )


def _is_owner(user: str, payload: Dict[str, Any]) -> bool:
    return user in OWNER_USERS or _truthy(payload.get("isBroadcaster")) or _truthy(payload.get("broadcaster"))


def _is_admin(user: str, payload: Dict[str, Any], mod_data: Dict[str, Any]) -> bool:
    return (
        _is_owner(user, payload)
        or user in set(mod_data.get("admins", []))
        or _truthy(payload.get("isMod"))
        or _truthy(payload.get("mod"))
    )


def _first_arg(parts: list[str]) -> str:
    return _norm_user(parts[1] if len(parts) > 1 else "")


def _local_command(user: str, payload: Dict[str, Any], command: str) -> Tuple[bool, Dict[str, Any] | None]:
    """Handle moderation commands locally.

    Returns (handled, response). If handled is False, command should be forwarded to Railway.
    """
    parts = command.strip().split()
    if not parts:
        return True, {"ok": False, "ignored": False, "result": "No command received."}

    cmd = parts[0].lower()
    mod_data = load_mod_data()
    ignored = set(mod_data.get("ignored", []))

    if user in ignored and cmd not in {"!unignore"}:
        return True, {"ok": True, "ignored": True, "result": f"Ignored command from {user}."}

    is_admin = _is_admin(user, payload, mod_data)
    is_owner = _is_owner(user, payload)

    if cmd in {"!b", "!beh", "!behavior"}:
        return True, {"ok": False, "ignored": False, "result": "Behavior chat commands are disabled for now. Evidence commands only."}

    if cmd == "!ignore":
        if not is_admin:
            return True, {"ok": False, "result": "Only admins can use !ignore."}
        target = _first_arg(parts)
        if not target:
            return True, {"ok": False, "result": "Usage: !ignore USERNAME"}
        if target in OWNER_USERS:
            return True, {"ok": False, "result": "Nope. Not ignoring an owner."}
        ignored.add(target)
        mod_data["ignored"] = sorted(ignored)
        save_mod_data(mod_data)
        return True, {"ok": True, "result": f"{target} is now ignored for Phasmo commands."}

    if cmd == "!unignore":
        if not is_admin:
            return True, {"ok": False, "result": "Only admins can use !unignore."}
        target = _first_arg(parts)
        if not target:
            return True, {"ok": False, "result": "Usage: !unignore USERNAME"}
        ignored.discard(target)
        mod_data["ignored"] = sorted(ignored)
        save_mod_data(mod_data)
        return True, {"ok": True, "result": f"{target} may submit Phasmo commands again."}

    if cmd == "!ignored":
        if not is_admin:
            return True, {"ok": False, "result": "Only admins can list ignored users."}
        listing = ", ".join(sorted(ignored)) or "none"
        return True, {"ok": True, "result": f"Ignored users: {listing}"}

    if cmd == "!modadd":
        if not is_owner:
            return True, {"ok": False, "result": "Only the owner/broadcaster can use !modadd."}
        target = _first_arg(parts)
        if not target:
            return True, {"ok": False, "result": "Usage: !modadd USERNAME"}
        admins = set(mod_data.get("admins", []))
        admins.add(target)
        mod_data["admins"] = sorted(admins)
        save_mod_data(mod_data)
        return True, {"ok": True, "result": f"{target} can now use Phasmo admin commands."}

    if cmd == "!modremove":
        if not is_owner:
            return True, {"ok": False, "result": "Only the owner/broadcaster can use !modremove."}
        target = _first_arg(parts)
        if not target:
            return True, {"ok": False, "result": "Usage: !modremove USERNAME"}
        admins = set(mod_data.get("admins", []))
        admins.discard(target)
        mod_data["admins"] = sorted(admins)
        save_mod_data(mod_data)
        return True, {"ok": True, "result": f"{target} removed from Phasmo admin commands."}

    if cmd == "!mods":
        if not is_admin:
            return True, {"ok": False, "result": "Only admins can list Phasmo admins."}
        listing = ", ".join(sorted(set(mod_data.get("admins", [])) | OWNER_USERS)) or "none"
        return True, {"ok": True, "result": f"Phasmo admins: {listing}"}

    # Restrict destructive/setup commands to admins.
    if cmd in {"!reset", "!phasmoreset", "!mode", "!evidencemode", "!responds", "!response", "!interact"} and not is_admin:
        return True, {"ok": False, "result": f"{cmd} is admin-only."}

    # Evidence commands can be public or admin-only by env setting.
    if cmd in {"!ev", "!evidence"} and not PHASMO_PUBLIC_EVIDENCE and not is_admin:
        return True, {"ok": False, "result": "Evidence commands are admin-only right now."}

    return False, None


@app.get("/health")
def health():
    mod_data = load_mod_data()
    return jsonify({
        "ok": True,
        "railway": bool(RAILWAY_BASE_URL),
        "room": PHASMO_ROOM,
        "public_evidence": PHASMO_PUBLIC_EVIDENCE,
        "owners": sorted(OWNER_USERS),
        "admins": mod_data.get("admins", []),
        "ignored_count": len(mod_data.get("ignored", [])),
    })


@app.post("/streamerbot/phasmo")
def streamerbot_phasmo():
    if not RAILWAY_BASE_URL:
        return jsonify({"ok": False, "error": "RAILWAY_BASE_URL is not set"}), 500

    payload = _extract_payload()
    command = _extract_command(payload)
    user = _user_from_payload(payload)
    if not command:
        return jsonify({"ok": False, "error": "No command received"}), 400

    handled, local_response = _local_command(user, payload, command)
    if handled:
        return jsonify({"source": "local_bridge", "user": user, "command": command, **(local_response or {})})

    headers = {"Content-Type": "application/json"}
    if PHASMO_ADMIN_TOKEN:
        headers["X-Phasmo-Token"] = PHASMO_ADMIN_TOKEN

    url = f"{RAILWAY_BASE_URL}/api/phasmo/command?room={PHASMO_ROOM}"
    response = requests.post(url, json={"command": command, "user": user}, headers=headers, timeout=8)
    try:
        body = response.json()
    except Exception:
        body = {"raw": response.text}

    return jsonify({
        "source": "railway",
        "ok": response.ok,
        "status_code": response.status_code,
        "user": user,
        "sent": command,
        "railway_response": body,
        "result": body.get("result") if isinstance(body, dict) else None,
    }), response.status_code


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PHASMO_BRIDGE_PORT)
