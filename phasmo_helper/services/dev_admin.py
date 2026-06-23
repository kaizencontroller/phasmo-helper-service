from __future__ import annotations

import json
import time
from typing import Any, Dict

from .. import settings
from ..core.data import GHOST_NAMES
from .leaderboard import _rebuild_leaderboard, _write_leaderboard
from .state import default_state, write_state, _state_path


def dev_admin_available() -> bool:
    return bool(settings._DEV_ADMIN_ENABLED)


def dev_admin_code_ok(code: str | None) -> bool:
    return dev_admin_available() and str(code or "").strip() == settings._DEV_ADMIN_CODE


def _base_demo_state(room: str) -> Dict[str, Any]:
    state = default_state(room)
    state.update({
        "setupComplete": True,
        "playerCount": 4,
        "difficulty": "professional",
        "weather": "fog",
        "responds": "unknown",
        "evidenceMode": "3",
        "lastCommand": "Dev Admin",
        "lastCommandResult": "Sample data loaded.",
    })
    return state


def load_sample_data() -> Dict[str, Any]:
    now = int(time.time() * 1000)
    rooms: list[str] = []

    helper = _base_demo_state("demo-helper")
    helper.update({
        "map": "6 Tanglewood Drive",
        "controlMode": "helper",
        "overlayMode": "helper",
        "evidence": {**helper["evidence"], "orbs": "yes", "freezing": "yes", "box": "unknown"},
        "behaviors": {"hantu-temperature-speed": "observed", "mimic-fake-orbs": "unknown"},
        "guesses": {"kaizenfan": "Hantu", "ghostgambler": "The Mimic", "orb_enjoyer": "Hantu"},
        "votes": {"chatmod": "Hantu", "van_goblin": "The Mimic"},
    })
    write_state("demo-helper", helper); rooms.append("demo-helper")

    tracker = _base_demo_state("demo-tracker")
    tracker.update({
        "map": "Camp Woodwind",
        "difficulty": "nightmare",
        "weather": "snow",
        "controlMode": "tracker",
        "overlayMode": "tracker",
        "evidenceMode": "2",
        "evidence": {**tracker["evidence"], "dots": "yes", "uv": "no"},
        "guesses": {"trackerfan": "Yurei"},
    })
    write_state("demo-tracker", tracker); rooms.append("demo-tracker")

    support = _base_demo_state("demo-support")
    support.update({
        "map": "Point Hope",
        "supportOptIn": True,
        "supportChannel": "kaizencontroller",
        "lastCommand": "!guess Deogen",
        "lastCommandResult": "Guess recorded for sampleviewer: Deogen.",
        "guesses": {"sampleviewer": "Deogen", "orblord": "Phantom"},
    })
    write_state("demo-support", support); rooms.append("demo-support")

    closed = _base_demo_state("demo-closed")
    closed.update({
        "map": "13 Willow Street",
        "difficulty": "intermediate",
        "weather": "clear",
        "evidence": {**closed["evidence"], "dots": "yes", "writing": "yes", "box": "yes"},
        "guesses": {"kaizenfan": "Deogen", "ghostgambler": "Wraith", "orb_enjoyer": "Deogen"},
        "votes": {"chatmod": "Deogen"},
        "contractResult": {
            "confirmedGhost": "Deogen",
            "confirmedAt": now,
            "confirmedBy": "dev-admin",
            "scored": True,
            "guessResults": {},
            "voteResults": {},
            "correctGuesses": 2,
            "wrongGuesses": 1,
            "correctVotes": 1,
            "wrongVotes": 0,
        },
    })
    write_state("demo-closed", closed); rooms.append("demo-closed")

    # Build a deliberately varied leaderboard to test accuracy vs volume.
    history: list[Dict[str, Any]] = []
    ghosts = ["Deogen", "Hantu", "Wraith", "The Mimic", "Revenant", "Banshee"]
    idx = 0
    def add_round(room: str, confirmed: str, guesses: Dict[str, str]):
        nonlocal idx
        idx += 1
        history.append({
            "roundId": f"demo-seed-{idx}",
            "room": room,
            "confirmedGhost": confirmed,
            "confirmedAt": now - (idx * 60000),
            "confirmedBy": "dev-admin",
            "guesses": guesses,
            "votes": {},
            "map": "Sample Map",
            "difficulty": "professional",
            "weather": "clear",
        })

    for i in range(10):
        confirmed = ghosts[i % len(ghosts)]
        add_round("demo-helper", confirmed, {"kaizenfan": confirmed if i < 8 else "Wraith"})
    for i in range(240):
        confirmed = ghosts[i % len(ghosts)]
        add_round("demo-global", confirmed, {"ghostgambler": confirmed if i < 24 else "Wraith"})
    for i in range(3):
        confirmed = ghosts[i % len(ghosts)]
        add_round("demo-tracker", confirmed, {"orb_enjoyer": confirmed})
    for i in range(12):
        confirmed = ghosts[i % len(ghosts)]
        add_round("demo-support", confirmed, {"wraithwrongagain": confirmed if i == 0 else "Wraith"})

    _write_leaderboard(_rebuild_leaderboard(history))
    return {"rooms": rooms, "historyCount": len(history)}


def clear_sample_data() -> Dict[str, Any]:
    removed = []
    for room in ["demo-helper", "demo-tracker", "demo-support", "demo-closed"]:
        path = _state_path(room)
        if path.exists():
            path.unlink()
            removed.append(room)
    _write_leaderboard(_rebuild_leaderboard([]))
    return {"removedRooms": removed}
