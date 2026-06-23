from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict

from .. import settings
from ..services.state import _room_name


def _bug_report_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._BUG_REPORT_FILE


def _feedback_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._FEEDBACK_FILE


def _support_ping_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._SUPPORT_PINGS_FILE


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _send_support_webhook_async(payload: Dict[str, Any]) -> None:
    url = settings._SUPPORT_WEBHOOK_URL
    if not url:
        return

    def worker() -> None:
        try:
            room = payload.get("room") or "default"
            channel = payload.get("channel") or "not provided"
            user = payload.get("user") or "anonymous"
            source = payload.get("source") or "command endpoint"
            command = payload.get("command") or ""
            room_url = payload.get("roomUrl") or ""
            text = (
                "Phasmo Helper support opt-in ping\n"
                f"Room: {room}\n"
                f"Channel/streamer: {channel}\n"
                f"Command user: {user}\n"
                f"Source: {source}\n"
                f"Command: {command}\n"
                f"Open: {room_url}"
            )
            body = json.dumps({"content": text}).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=3).read()
        except Exception:
            # Notification should never break gameplay commands.
            pass

    threading.Thread(target=worker, daemon=True).start()


def maybe_record_support_ping(
    state: Dict[str, Any],
    *,
    room: str,
    user: str,
    command: str,
    source: str = "command",
    channel: str = "",
    bot_account: str = "",
    base_url: str = "",
) -> Dict[str, Any] | None:
    """Record a throttled support ping only when a room explicitly opts in.

    Privacy rule: this only fires if supportOptIn is true. It is throttled per room so
    a busy chat does not spam the owner. The state is mutated with lastSupportPingAt
    so callers should write_state after calling this.
    """
    if not bool(state.get("supportOptIn")):
        return None
    now_ms = int(time.time() * 1000)
    cooldown_ms = max(60, settings._SUPPORT_PING_COOLDOWN_SECONDS) * 1000
    last = int(state.get("lastSupportPingAt") or 0)
    if last and now_ms - last < cooldown_ms:
        return None

    safe_room = _room_name(room)
    chosen_channel = (channel or state.get("supportChannel") or "").strip()[:160]
    payload = {
        "createdAt": now_ms,
        "room": safe_room,
        "user": str(user or "anonymous")[:120],
        "command": str(command or "")[:300],
        "source": str(source or "command")[:80],
        "channel": chosen_channel,
        "botAccount": str(bot_account or "")[:120],
        "note": str(state.get("supportNote") or "")[:500],
        "roomUrl": (base_url.rstrip("/") + f"/phasmo/control?room={safe_room}") if base_url else f"/phasmo/control?room={safe_room}",
    }
    _append_jsonl(_support_ping_path(), payload)
    state["lastSupportPingAt"] = now_ms
    _send_support_webhook_async(payload)
    return payload
