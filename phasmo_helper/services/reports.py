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


def _read_jsonl(path: Path) -> list[Dict[str, Any]]:
    out: list[Dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    out.append(item)
            except Exception:
                continue
    except Exception:
        pass
    return out


def _issue_id(report: Dict[str, Any], index: int) -> str:
    val = report.get("id") or report.get("issueId")
    if val:
        return str(val)[:64]
    created = int(report.get("createdAt") or int(time.time() * 1000))
    room = _room_name(str(report.get("room") or "default"))
    return f"BR-{created}-{index}-{room}"


def read_bug_issues() -> list[Dict[str, Any]]:
    issues = []
    for idx, report in enumerate(_read_jsonl(_bug_report_path()), start=1):
        item = dict(report)
        item.setdefault("id", _issue_id(item, idx))
        item.setdefault("title", (str(item.get("message") or "")[:80] or "Untitled report"))
        item.setdefault("status", "new")
        item.setdefault("priority", "medium")
        item.setdefault("targetVersion", "")
        item.setdefault("fixedVersion", "")
        item.setdefault("internalNotes", "")
        item.setdefault("publicNotes", "")
        item.setdefault("updatedAt", item.get("createdAt") or int(time.time() * 1000))
        issues.append(item)
    return issues


def write_bug_issues(issues: list[Dict[str, Any]]) -> int:
    path = _bug_report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in issues:
            clean = dict(item)
            f.write(json.dumps(clean, ensure_ascii=False) + "\n")
    return len(issues)


def update_bug_issue(issue_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    issues = read_bug_issues()
    allowed_status = {"new", "triaged", "planned", "in_progress", "fixed", "wont_fix", "duplicate", "needs_info"}
    allowed_priority = {"low", "medium", "high", "urgent"}
    for issue in issues:
        if str(issue.get("id")) == str(issue_id):
            if "status" in patch and patch.get("status") in allowed_status:
                issue["status"] = patch.get("status")
            if "priority" in patch and patch.get("priority") in allowed_priority:
                issue["priority"] = patch.get("priority")
            for key, limit in (("title", 160), ("targetVersion", 40), ("fixedVersion", 40), ("internalNotes", 2000), ("publicNotes", 1000)):
                if key in patch:
                    issue[key] = str(patch.get(key) or "")[:limit]
            issue["updatedAt"] = int(time.time() * 1000)
            write_bug_issues(issues)
            return issue
    raise KeyError(issue_id)


def export_bug_tracker() -> Dict[str, Any]:
    return {"schemaVersion": 1, "exportedAt": int(time.time() * 1000), "source": "phasmo-helper", "issues": read_bug_issues()}


def import_bug_tracker(payload: Dict[str, Any]) -> Dict[str, Any]:
    incoming = payload.get("issues") if isinstance(payload, dict) else None
    if not isinstance(incoming, list):
        return {"imported": 0, "updated": 0, "skipped": 0}
    current = {str(item.get("id")): item for item in read_bug_issues()}
    imported = updated = skipped = 0
    for raw in incoming:
        if not isinstance(raw, dict):
            skipped += 1
            continue
        item = dict(raw)
        item.setdefault("id", _issue_id(item, len(current) + imported + 1))
        iid = str(item.get("id"))
        if iid in current:
            current[iid].update(item)
            updated += 1
        else:
            current[iid] = item
            imported += 1
    write_bug_issues(list(current.values()))
    return {"imported": imported, "updated": updated, "skipped": skipped}
