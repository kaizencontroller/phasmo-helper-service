from __future__ import annotations

import csv
import io
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .. import settings

USAGE_FILE = "__global_room_usage.json"
EVENT_FILE = "__global_room_usage_events.jsonl"
SCHEMA_VERSION = 1
MAX_EVENTS_RETURNED = 500
MAX_ROUNDS_PER_ROOM = 500
MAX_EVENTS_PER_IMPORT = 5000


def _now_ms() -> int:
    return int(time.time() * 1000)


def _usage_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / USAGE_FILE


def _events_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / EVENT_FILE


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return default


def _clean_text(value: Any, limit: int = 160) -> str:
    return str(value or "").strip()[:limit]


def _duration_ms(record: Dict[str, Any], now_ms: int | None = None) -> int:
    start = _safe_int(record.get("firstSeenAt"))
    if not start:
        return 0
    end = _safe_int(record.get("closedAt")) or _safe_int(record.get("lastSeenAt")) or (now_ms or _now_ms())
    return max(0, end - start)


def _read_usage_raw() -> Dict[str, Any]:
    path = _usage_path()
    if not path.exists():
        return {"schemaVersion": SCHEMA_VERSION, "updatedAt": 0, "rooms": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("usage root must be object")
        rooms = data.get("rooms") if isinstance(data.get("rooms"), dict) else {}
        return {"schemaVersion": int(data.get("schemaVersion") or SCHEMA_VERSION), "updatedAt": _safe_int(data.get("updatedAt")), "rooms": rooms}
    except Exception:
        return {"schemaVersion": SCHEMA_VERSION, "updatedAt": 0, "rooms": {}}


def _write_usage_raw(data: Dict[str, Any]) -> Dict[str, Any]:
    data["schemaVersion"] = SCHEMA_VERSION
    data["updatedAt"] = _now_ms()
    _usage_path().write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data


def _new_record(room: str, now_ms: int) -> Dict[str, Any]:
    return {
        "room": room,
        "firstSeenAt": now_ms,
        "lastSeenAt": now_ms,
        "closedAt": 0,
        "roomStatus": "open",
        "roomLocked": False,
        "supportOptIn": False,
        "supportChannel": "",
        "lastMap": "unknown",
        "lastDifficulty": "unknown",
        "lastWeather": "unknown",
        "lastPlayerCount": 0,
        "lastEvidenceMode": "3",
        "lastCommand": "",
        "lastEvent": "room_created",
        "writeCount": 0,
        "commandCount": 0,
        "nextRoundCount": 0,
        "resetCount": 0,
        "endSessionCount": 0,
        "resultCount": 0,
        "jumpscareCount": 0,
        "rounds": [],
        "eventCounts": {},
    }


def _round_from_state(state: Dict[str, Any], now_ms: int) -> Dict[str, Any] | None:
    round_id = _clean_text(state.get("roundId"), 120)
    if not round_id:
        return None
    result = state.get("contractResult") or {}
    return {
        "roundId": round_id,
        "startedAt": now_ms,
        "lastSeenAt": now_ms,
        "map": _clean_text(state.get("map") or "unknown", 120),
        "difficulty": _clean_text(state.get("difficulty") or "unknown", 60),
        "weather": _clean_text(state.get("weather") or "unknown", 60),
        "playerCount": max(0, _safe_int(state.get("playerCount"))),
        "evidenceMode": _clean_text(state.get("evidenceMode") or "3", 10),
        "setupComplete": bool(state.get("setupComplete")),
        "confirmedGhost": _clean_text(result.get("confirmedGhost"), 80),
        "scored": bool(result.get("scored")),
        "completedAt": _safe_int(result.get("confirmedAt")),
    }


def _merge_round(record: Dict[str, Any], state: Dict[str, Any], now_ms: int) -> None:
    incoming = _round_from_state(state, now_ms)
    if not incoming:
        return
    rounds = record.setdefault("rounds", [])
    existing = None
    for item in rounds:
        if item.get("roundId") == incoming["roundId"]:
            existing = item
            break
    if existing is None:
        rounds.append(incoming)
    else:
        existing["lastSeenAt"] = now_ms
        for key in ["map", "difficulty", "weather", "playerCount", "evidenceMode", "setupComplete", "confirmedGhost", "scored", "completedAt"]:
            value = incoming.get(key)
            if value not in {None, "", "unknown", 0, False} or key in {"setupComplete", "scored"}:
                existing[key] = value
    if len(rounds) > MAX_ROUNDS_PER_ROOM:
        del rounds[0 : len(rounds) - MAX_ROUNDS_PER_ROOM]


def _event_summary(state: Dict[str, Any], event: str, source: str, actor: str, details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    result = state.get("contractResult") or {}
    payload = {
        "ts": _now_ms(),
        "room": _clean_text(state.get("room"), 80),
        "event": _clean_text(event or "state_write", 80),
        "source": _clean_text(source, 80),
        "actor": _clean_text(actor, 120),
        "roundId": _clean_text(state.get("roundId"), 120),
        "map": _clean_text(state.get("map") or "unknown", 120),
        "difficulty": _clean_text(state.get("difficulty") or "unknown", 60),
        "playerCount": max(0, _safe_int(state.get("playerCount"))),
        "confirmedGhost": _clean_text(result.get("confirmedGhost"), 80),
    }
    if details:
        safe_details: Dict[str, Any] = {}
        for key, value in details.items():
            if key.lower() in {"roomcode", "roompasscode", "code", "contact", "supportcontact"}:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe_details[str(key)[:60]] = _clean_text(value, 300) if isinstance(value, str) else value
        if safe_details:
            payload["details"] = safe_details
    return payload


def record_room_activity(room: str, state: Dict[str, Any], event: str = "state_write", source: str = "app", actor: str = "", details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Update aggregate room usage metrics and append milestone events.

    This intentionally avoids storing room passcodes or support contact details.
    It is an operational usage log for beta support, not a user identity tracker.
    """
    now_ms = _now_ms()
    room = _clean_text(room or state.get("room") or "default", 80) or "default"
    data = _read_usage_raw()
    rooms = data.setdefault("rooms", {})
    record = rooms.get(room) if isinstance(rooms.get(room), dict) else _new_record(room, now_ms)
    is_new = room not in rooms
    rooms[room] = record

    event = event or ("room_created" if is_new else "state_write")
    if is_new and event == "state_write":
        event = "room_created"

    record["lastSeenAt"] = now_ms
    record["roomStatus"] = _clean_text(state.get("roomStatus") or "open", 20) or "open"
    record["closedAt"] = _safe_int(state.get("closedAt")) if record["roomStatus"] == "closed" else 0
    record["roomLocked"] = bool(state.get("roomCode"))
    record["supportOptIn"] = bool(state.get("supportOptIn"))
    record["supportChannel"] = _clean_text(state.get("supportChannel"), 160)
    record["lastMap"] = _clean_text(state.get("map") or "unknown", 120)
    record["lastDifficulty"] = _clean_text(state.get("difficulty") or "unknown", 60)
    record["lastWeather"] = _clean_text(state.get("weather") or "unknown", 60)
    record["lastPlayerCount"] = max(record.get("lastPlayerCount") or 0, _safe_int(state.get("playerCount")))
    record["lastEvidenceMode"] = _clean_text(state.get("evidenceMode") or "3", 10)
    record["lastCommand"] = _clean_text(state.get("lastCommand"), 200)
    record["lastEvent"] = event
    record["writeCount"] = _safe_int(record.get("writeCount")) + 1
    if event in {"streamerbot_command", "streamerbot_get_command", "streamerbot_room_route"}:
        record["commandCount"] = _safe_int(record.get("commandCount")) + 1
    if event == "next_round":
        record["nextRoundCount"] = _safe_int(record.get("nextRoundCount")) + 1
    if event == "reset_round":
        record["resetCount"] = _safe_int(record.get("resetCount")) + 1
    if event == "end_session":
        record["endSessionCount"] = _safe_int(record.get("endSessionCount")) + 1
    if event == "contract_result":
        record["resultCount"] = _safe_int(record.get("resultCount")) + 1
    if event == "jumpscare":
        record["jumpscareCount"] = _safe_int(record.get("jumpscareCount")) + 1

    counts = record.setdefault("eventCounts", {})
    counts[event] = _safe_int(counts.get(event)) + 1
    _merge_round(record, state, now_ms)
    record["durationMs"] = _duration_ms(record, now_ms)
    record["roundsObserved"] = len(record.get("rounds") or [])
    record["roundsCompleted"] = sum(1 for r in (record.get("rounds") or []) if r.get("confirmedGhost") or r.get("scored"))
    _write_usage_raw(data)

    # Keep the event stream focused on useful milestones. Aggregate usage still
    # updates on every state write.
    if event != "state_write":
        with _events_path().open("a", encoding="utf-8") as f:
            event_payload = _event_summary({**state, "room": room}, event, source, actor, details)
            f.write(json.dumps(event_payload, ensure_ascii=False) + "\n")
    return record


def read_recent_usage_events(limit: int = MAX_EVENTS_RETURNED) -> List[Dict[str, Any]]:
    path = _events_path()
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-max(1, min(limit, 5000)) :]
        events = []
        for line in lines:
            try:
                item = json.loads(line)
                if isinstance(item, dict):
                    events.append(item)
            except Exception:
                continue
        return list(reversed(events))
    except Exception:
        return []


def usage_summary() -> Dict[str, Any]:
    data = _read_usage_raw()
    now_ms = _now_ms()
    records: List[Dict[str, Any]] = []
    for room, raw in (data.get("rooms") or {}).items():
        if not isinstance(raw, dict):
            continue
        rec = dict(raw)
        rec["room"] = rec.get("room") or room
        rec["durationMs"] = _duration_ms(rec, now_ms)
        rec["activeMinutes"] = round(rec["durationMs"] / 60000, 1)
        rec["roundsObserved"] = len(rec.get("rounds") or [])
        rec["roundsCompleted"] = sum(1 for r in (rec.get("rounds") or []) if r.get("confirmedGhost") or r.get("scored"))
        records.append(rec)
    records.sort(key=lambda r: _safe_int(r.get("lastSeenAt")), reverse=True)
    totals = {
        "rooms": len(records),
        "openRooms": sum(1 for r in records if r.get("roomStatus") != "closed"),
        "closedRooms": sum(1 for r in records if r.get("roomStatus") == "closed"),
        "roundsObserved": sum(_safe_int(r.get("roundsObserved")) for r in records),
        "roundsCompleted": sum(_safe_int(r.get("roundsCompleted")) for r in records),
        "totalDurationMs": sum(_safe_int(r.get("durationMs")) for r in records),
    }
    totals["totalActiveHours"] = round(totals["totalDurationMs"] / 3600000, 2)
    return {"ok": True, "schemaVersion": SCHEMA_VERSION, "updatedAt": data.get("updatedAt") or 0, "totals": totals, "rooms": records, "recentEvents": read_recent_usage_events()}


def export_usage() -> Dict[str, Any]:
    data = _read_usage_raw()
    return {"schemaVersion": SCHEMA_VERSION, "exportedAt": _now_ms(), "source": "phasmo-helper-room-usage", "usage": data, "recentEvents": read_recent_usage_events(2000)}


def import_usage(payload: Dict[str, Any]) -> Dict[str, Any]:
    incoming = payload.get("usage") if isinstance(payload.get("usage"), dict) else payload
    if not isinstance(incoming, dict):
        return {"importedRooms": 0, "mergedRooms": 0, "eventsImported": 0}
    current = _read_usage_raw()
    current_rooms = current.setdefault("rooms", {})
    incoming_rooms = incoming.get("rooms") if isinstance(incoming.get("rooms"), dict) else {}
    imported = 0
    merged = 0
    for room, rec in incoming_rooms.items():
        if not isinstance(rec, dict):
            continue
        room_key = _clean_text(room or rec.get("room"), 80)
        if not room_key:
            continue
        imported += 1
        if room_key not in current_rooms:
            current_rooms[room_key] = rec
            continue
        merged += 1
        existing = current_rooms[room_key]
        existing["firstSeenAt"] = min(_safe_int(existing.get("firstSeenAt")) or _safe_int(rec.get("firstSeenAt")), _safe_int(rec.get("firstSeenAt")) or _safe_int(existing.get("firstSeenAt")))
        if _safe_int(rec.get("lastSeenAt")) > _safe_int(existing.get("lastSeenAt")):
            for key, value in rec.items():
                if key not in {"eventCounts", "rounds"}:
                    existing[key] = value
        # Merge rounds by id.
        rounds = {r.get("roundId"): r for r in (existing.get("rounds") or []) if isinstance(r, dict) and r.get("roundId")}
        for r in rec.get("rounds") or []:
            if isinstance(r, dict) and r.get("roundId"):
                if r["roundId"] not in rounds or _safe_int(r.get("lastSeenAt")) > _safe_int(rounds[r["roundId"]].get("lastSeenAt")):
                    rounds[r["roundId"]] = r
        existing["rounds"] = list(rounds.values())[-MAX_ROUNDS_PER_ROOM:]
        counts = existing.setdefault("eventCounts", {})
        for key, value in (rec.get("eventCounts") or {}).items():
            counts[key] = _safe_int(counts.get(key)) + _safe_int(value)
    _write_usage_raw(current)

    events_imported = 0
    for event in (payload.get("recentEvents") or [])[:MAX_EVENTS_PER_IMPORT]:
        if isinstance(event, dict):
            with _events_path().open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
            events_imported += 1
    return {"importedRooms": imported, "mergedRooms": merged, "eventsImported": events_imported}


def usage_csv() -> str:
    summary = usage_summary()
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=[
        "room", "roomStatus", "roundsObserved", "roundsCompleted", "activeMinutes", "firstSeenAt", "lastSeenAt", "closedAt", "lastMap", "lastDifficulty", "lastPlayerCount", "commandCount", "writeCount", "nextRoundCount", "resetCount", "endSessionCount", "resultCount", "supportOptIn", "supportChannel", "roomLocked"
    ])
    writer.writeheader()
    for rec in summary.get("rooms") or []:
        writer.writerow({key: rec.get(key, "") for key in writer.fieldnames})
    return out.getvalue()
