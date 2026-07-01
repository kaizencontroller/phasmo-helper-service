from __future__ import annotations

import json
import random
import re
import time
from pathlib import Path
from typing import Any, Dict
from .. import settings
from ..core.data import EVIDENCE
from ..core.config import _read_config
from ..core.utils import _normal_user

def _room_name(raw: str | None) -> str:
    room = (raw or "default").strip().lower()
    room = re.sub(r"[^a-z0-9_-]", "-", room)[:64]
    return room or "default"


def _state_path(room: str) -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / f"{room}.json"


def default_state(room: str = "default") -> Dict[str, Any]:
    return {
        "room": room,
        "evidence": {key: "unknown" for key in EVIDENCE},
        "evidenceMode": "3",
        "responds": "unknown",
        "setupComplete": False,
        "map": "unknown",
        "difficulty": "unknown",
        "weather": "unknown",
        "playerCount": 4,
        "sanityValues": [None, None, None, None],
        "huntSanity": None,
        "presentation": "unknown",
        "cursedItems": {},
        "behaviors": {},
        "votes": {},
        "guesses": {},
        "ignoredUsers": [],
        # Optional casual 4-digit room passcode. This is meant to keep random users
        # from changing a shared room, not to be high-security authentication.
        "roomCode": "",
        "timers": {},
        "manualGhosts": {"selected": None, "excluded": []},
        "roundId": f"{room}-{int(time.time() * 1000)}-{random.randint(1000, 9999)}",
        "contractResult": {
            "confirmedGhost": None,
            "confirmedAt": 0,
            "confirmedBy": "",
            "scored": False,
            "guessResults": {},
            "voteResults": {},
            "correctGuesses": 0,
            "wrongGuesses": 0,
            "correctVotes": 0,
            "wrongVotes": 0,
        },
        "stateVersion": 0,
        "updatedAt": int(time.time() * 1000),
        "lastActiveAt": int(time.time() * 1000),
        "lastCommand": "",
        "lastCommandResult": "",
        "panicCount": 0,
        "panicNote": "",
        "panicUser": "",
        "panicUntil": 0,
        "panicTakeoverUntil": 0,
        "panicCooldownUntil": 0,
        "panicSeq": 0,
        "classifiedUntil": 0,
        "fakeCandidate": None,
        "awardMessage": "",
        "resetCount": 0,
        "sanityTouched": False,
        "evidenceNarrowedAt": 0,
        "jumpscareUntil": 0,
        "jumpscareSeq": 0,
        "jumpscareCount": 0,
        # Display mode toggles: helper keeps next-best-test suggestions; tracker hides suggestions.
        "controlMode": "helper",
        "overlayMode": "helper",
        "supportOptIn": False,
        "supportChannel": "",
        "supportContact": "",
        "supportNote": "",
        "lastSupportPingAt": 0,
        "roomStatus": "open",
        "closedAt": 0,
        "closedBy": "",
    }


def read_state(room: str) -> Dict[str, Any]:
    path = _state_path(room)
    if not path.exists():
        state = default_state(room)
        state["jumpscareCount"] = _read_jumpscare_count()
        state["config"] = _read_config()
        return state
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        merged = default_state(room)
        merged.update(data)
        merged["evidence"] = {**default_state(room)["evidence"], **data.get("evidence", {})}
        merged["behaviors"] = data.get("behaviors", {}) or {}
        merged["votes"] = data.get("votes", {}) or {}
        merged["guesses"] = data.get("guesses", {}) or {}
        merged["ignoredUsers"] = sorted({_normal_user(u) for u in (data.get("ignoredUsers") or []) if str(u).strip()})
        merged["roomCode"] = _clean_room_code(data.get("roomCode"))
        merged["timers"] = data.get("timers", {}) or {}
        merged["sanityValues"] = (data.get("sanityValues") or [None, None, None, None])[:4] + [None] * max(0, 4 - len(data.get("sanityValues") or []))
        merged["playerCount"] = int(data.get("playerCount") or 4)
        merged["huntSanity"] = data.get("huntSanity")
        merged["presentation"] = data.get("presentation") if data.get("presentation") in {"unknown", "female", "male"} else "unknown"
        merged["cursedItems"] = data.get("cursedItems", {}) or {}
        merged["controlMode"] = data.get("controlMode") if data.get("controlMode") in {"helper", "tracker"} else "helper"
        merged["overlayMode"] = data.get("overlayMode") if data.get("overlayMode") in {"helper", "tracker"} else "helper"
        if not merged.get("map") and data.get("level"):
            merged["map"] = data.get("level")
        manual = data.get("manualGhosts", {}) or {}
        merged["manualGhosts"] = {
            "selected": manual.get("selected"),
            "excluded": manual.get("excluded", []) or [],
        }
        merged["jumpscareCount"] = _read_jumpscare_count()
        merged["resetCount"] = _read_reset_count()
        merged["roomStatus"] = data.get("roomStatus") if data.get("roomStatus") in {"open", "closed"} else "open"
        try:
            merged["closedAt"] = int(data.get("closedAt") or 0)
        except Exception:
            merged["closedAt"] = 0
        merged["closedBy"] = str(data.get("closedBy") or "")[:120]
        merged["config"] = _read_config()
        return merged
    except Exception:
        state = default_state(room)
        state["jumpscareCount"] = _read_jumpscare_count()
        state["config"] = _read_config()
        return state


def write_state(room: str, state: Dict[str, Any], usage_event: str = "state_write", usage_source: str = "app", usage_actor: str = "", usage_details: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state["room"] = room
    now_ms = int(time.time() * 1000)
    # Track when a normal 3-evidence round reaches 2 confirmed evidence.
    # After 5 minutes there, the overlay can rotate in unique behavior checks
    # instead of only repeating the final missing evidence suggestion.
    try:
        yes_count = sum(1 for v in (state.get("evidence") or {}).values() if v == "yes")
        mode = str(state.get("evidenceMode") or "3")
        if mode == "3" and yes_count >= 2:
            if not state.get("evidenceNarrowedAt"):
                state["evidenceNarrowedAt"] = now_ms
        else:
            state["evidenceNarrowedAt"] = 0
    except Exception:
        state["evidenceNarrowedAt"] = 0
    state["updatedAt"] = now_ms
    state["lastActiveAt"] = now_ms
    try:
        state["stateVersion"] = int(state.get("stateVersion") or 0) + 1
    except Exception:
        state["stateVersion"] = 1
    to_save = dict(state)
    # Jumpscare presses are intentionally global across all rooms/sessions.
    # Do not persist this value into individual room state files.
    to_save.pop("jumpscareCount", None)
    to_save.pop("config", None)
    _state_path(room).write_text(json.dumps(to_save, indent=2, sort_keys=True), encoding="utf-8")
    state["jumpscareCount"] = _read_jumpscare_count()
    try:
        from .usage import record_room_activity
        record_room_activity(room, state, event=usage_event, source=usage_source, actor=usage_actor, details=usage_details)
    except Exception:
        # Usage analytics should never break active room state updates.
        pass
    return state


def _auth_ok(x_phasmo_token: str | None, token_query: str | None) -> bool:
    # Global admin tokens are intentionally disabled for the public/community helper.
    # Room-level edits can instead use an optional 4-digit room passcode.
    return True


def _clean_room_code(raw: Any) -> str:
    code = re.sub(r"[^0-9]", "", str(raw or ""))[:4]
    return code if len(code) == 4 else ""


def _room_code_ok(state: Dict[str, Any], supplied: Any) -> bool:
    expected = _clean_room_code(state.get("roomCode"))
    if not expected:
        return True
    return _clean_room_code(supplied) == expected


def public_state(state: Dict[str, Any]) -> Dict[str, Any]:
    public = dict(state)
    public["roomLocked"] = bool(_clean_room_code(public.get("roomCode")))
    public.pop("roomCode", None)
    # Contact details are stored for support follow-up but not returned to public browser state.
    public.pop("supportContact", None)
    return public

RESET_COUNTER_FILE = "__global_reset_counter.json"

FAKE_GHOSTS = [
    {"name": "The Intern", "ev": ["box", "writing", "orbs"], "note": "Not real. Probably holding the EMF reader upside down."},
    {"name": "OSHA Violation", "ev": ["dots", "emf5", "uv"], "note": "Not real. Haunts unsecured tripods and blocked exits."},
    {"name": "Three Kids in a Trenchcoat", "ev": ["freezing", "orbs", "box"], "note": "Not real. Suspiciously asks where the snacks are."},
]


def _reset_counter_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / RESET_COUNTER_FILE


def _read_reset_count() -> int:
    try:
        data = json.loads(_reset_counter_path().read_text(encoding="utf-8"))
        return max(0, int(data.get("count") or 0))
    except Exception:
        return 0


def _write_reset_count(count: int) -> int:
    count = max(0, int(count))
    _reset_counter_path().write_text(json.dumps({"count": count}, indent=2), encoding="utf-8")
    return count


def _increment_reset_count() -> int:
    return _write_reset_count(_read_reset_count() + 1)


def _reset_award(reset_count: int) -> str:
    awards = [
        "Best Supporting Scream",
        "Most Likely To Touch The Mirror",
        "Outstanding Achievement in Door Mismanagement",
        "Excellence in Van-Based Leadership",
        "Most Improved Panic Callout",
        "Lifetime Achievement in Ignoring Hiding Spots",
        "Best Use of Salt as a Project Management Tool",
        "Least Suspicious Cursed Object Enthusiast",
    ]
    return awards[reset_count % len(awards)]


def _new_reset_state(room: str) -> Dict[str, Any]:
    count = _increment_reset_count()
    state = default_state(room)
    state["resetCount"] = count
    # Awards are intentionally occasional, like a fake achievement unlock.
    if random.random() < 0.25:
        state["awardMessage"] = _reset_award(count)
    if count > 0 and count % 100 == 0:
        state["fakeCandidate"] = FAKE_GHOSTS[(count // 100) % len(FAKE_GHOSTS)]
    return state


def _jumpscare_counter_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._JUMPSCARE_COUNTER_FILE


def _read_jumpscare_count() -> int:
    try:
        data = json.loads(_jumpscare_counter_path().read_text(encoding="utf-8"))
        return max(0, int(data.get("count") or 0))
    except Exception:
        return 0


def _write_jumpscare_count(count: int) -> int:
    count = max(0, int(count))
    _jumpscare_counter_path().write_text(json.dumps({"count": count}, indent=2), encoding="utf-8")
    return count

