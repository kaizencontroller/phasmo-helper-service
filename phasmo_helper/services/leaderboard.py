from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple
from .. import settings
from ..core.data import GHOST_NAMES
from ..core.utils import _normal_user, _normal_ghost, _now_ms

def _leaderboard_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._LEADERBOARD_FILE


def _empty_leaderboard() -> Dict[str, Any]:
    return {"players": {}, "history": []}


def _read_leaderboard() -> Dict[str, Any]:
    try:
        data = json.loads(_leaderboard_path().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("players", {})
            data.setdefault("history", [])
            return data
    except Exception:
        pass
    return _empty_leaderboard()


def _write_leaderboard(data: Dict[str, Any]) -> Dict[str, Any]:
    data.setdefault("players", {})
    data.setdefault("history", [])
    _leaderboard_path().write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data


def _rebuild_leaderboard(history: list[Dict[str, Any]]) -> Dict[str, Any]:
    players: Dict[str, Dict[str, Any]] = {}
    for item in history:
        confirmed = item.get("confirmedGhost")
        if not confirmed:
            continue
        for user, ghost in (item.get("guesses") or {}).items():
            username = _normal_user(str(user))
            row = players.setdefault(username, {
                "guessTotal": 0, "guessCorrect": 0, "guessWrong": 0,
                "voteTotal": 0, "voteCorrect": 0, "voteWrong": 0,
                "points": 0, "lastCorrectAt": 0,
            })
            row["guessTotal"] += 1
            if ghost == confirmed:
                row["guessCorrect"] += 1
                row["points"] += 3
                row["lastCorrectAt"] = max(int(row.get("lastCorrectAt") or 0), int(item.get("confirmedAt") or 0))
            else:
                row["guessWrong"] += 1
        for user, ghost in (item.get("votes") or {}).items():
            username = _normal_user(str(user))
            row = players.setdefault(username, {
                "guessTotal": 0, "guessCorrect": 0, "guessWrong": 0,
                "voteTotal": 0, "voteCorrect": 0, "voteWrong": 0,
                "points": 0, "lastCorrectAt": 0,
            })
            row["voteTotal"] += 1
            if ghost == confirmed:
                row["voteCorrect"] += 1
                row["points"] += 1
                row["lastCorrectAt"] = max(int(row.get("lastCorrectAt") or 0), int(item.get("confirmedAt") or 0))
            else:
                row["voteWrong"] += 1
    for stats in players.values():
        gt = int(stats.get("guessTotal") or 0)
        gc = int(stats.get("guessCorrect") or 0)
        vt = int(stats.get("voteTotal") or 0)
        vc = int(stats.get("voteCorrect") or 0)
        guess_accuracy = (gc / gt) if gt else 0.0
        vote_accuracy = (vc / vt) if vt else 0.0
        # Confidence-adjusted score keeps 8/10 above 24/240 while still rewarding sample size.
        stats["guessAccuracy"] = round(guess_accuracy, 4)
        stats["voteAccuracy"] = round(vote_accuracy, 4)
        stats["rankScore"] = round((guess_accuracy * min(1.0, gt / 10.0)) + (vote_accuracy * 0.05), 4)
    return {"players": players, "history": history[-settings._MAX_LEADERBOARD_HISTORY:]}


def _score_contract_result(state: Dict[str, Any], confirmed_ghost: str, confirmed_by: str = "control") -> Tuple[Dict[str, Any], str]:
    ghost = _normal_ghost(confirmed_ghost) or confirmed_ghost
    if ghost not in GHOST_NAMES:
        return state, f"Unknown actual ghost: {confirmed_ghost or 'blank'}."
    now_ms = _now_ms() if '_now_ms' in globals() else int(time.time() * 1000)
    round_id = str(state.get("roundId") or f"{state.get('room', 'default')}-{now_ms}")
    guesses = dict(state.get("guesses") or {})
    votes = dict(state.get("votes") or {})
    guess_results = {user: {"guess": guessed, "correct": guessed == ghost} for user, guessed in guesses.items()}
    vote_results = {user: {"vote": voted, "correct": voted == ghost} for user, voted in votes.items()}
    correct_guesses = sum(1 for row in guess_results.values() if row.get("correct"))
    wrong_guesses = sum(1 for row in guess_results.values() if not row.get("correct"))
    correct_votes = sum(1 for row in vote_results.values() if row.get("correct"))
    wrong_votes = sum(1 for row in vote_results.values() if not row.get("correct"))
    result = {
        "confirmedGhost": ghost,
        "confirmedAt": now_ms,
        "confirmedBy": _normal_user(confirmed_by),
        "scored": True,
        "guessResults": guess_results,
        "voteResults": vote_results,
        "correctGuesses": correct_guesses,
        "wrongGuesses": wrong_guesses,
        "correctVotes": correct_votes,
        "wrongVotes": wrong_votes,
    }
    state["roundId"] = round_id
    state["contractResult"] = result

    board = _read_leaderboard()
    history = [item for item in (board.get("history") or []) if item.get("roundId") != round_id]
    history.append({
        "roundId": round_id,
        "room": state.get("room", "default"),
        "confirmedGhost": ghost,
        "confirmedAt": now_ms,
        "confirmedBy": _normal_user(confirmed_by),
        "guesses": guesses,
        "votes": votes,
        "map": state.get("map"),
        "difficulty": state.get("difficulty"),
        "weather": state.get("weather"),
    })
    _write_leaderboard(_rebuild_leaderboard(history))
    return state, f"Actual ghost confirmed as {ghost}. Guesses: {correct_guesses} correct, {wrong_guesses} debunked. Votes: {correct_votes} correct, {wrong_votes} debunked."
