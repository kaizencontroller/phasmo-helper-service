from __future__ import annotations

import csv
import io
import json
import time
from collections import Counter
from typing import Any


def append_timeline(state: dict[str, Any], event: str, *, source: str = "app", actor: str = "", details: dict[str, Any] | None = None) -> None:
    timeline = state.setdefault("timeline", [])
    timeline.append({
        "id": f"evt-{int(time.time() * 1000)}-{len(timeline) + 1}", "at": int(time.time() * 1000),
        "event": event, "source": source, "actor": actor, "details": details or {},
    })
    state["timeline"] = timeline[-1000:]


def session_summary(state: dict[str, Any]) -> dict[str, Any]:
    history = state.get("sessionHistory") or state.get("roundHistory") or []
    result = state.get("contractResult") or {}
    timeline = state.get("timeline") or []
    started = min((int(item.get("at") or 0) for item in timeline if item.get("at")), default=int(state.get("updatedAt") or 0))
    ended = int(state.get("closedAt") or state.get("updatedAt") or time.time() * 1000)
    ghosts = [str(item.get("confirmedGhost")) for item in history if item.get("confirmedGhost")]
    if result.get("confirmedGhost") and result.get("confirmedGhost") not in ghosts:
        ghosts.append(str(result["confirmedGhost"]))
    guesses = state.get("guesses") or {}
    votes = state.get("votes") or {}
    evidence = state.get("evidence") or {}
    return {
        "schemaVersion": 1, "room": state.get("room"), "roundsPlayed": max(len(history), 1 if timeline else 0),
        "durationMs": max(0, ended - started), "map": state.get("map"), "difficulty": state.get("difficulty"),
        "ghostStatistics": dict(Counter(ghosts)),
        "viewerParticipation": {"uniqueViewers": len(set(guesses) | set(votes)), "guesses": len(guesses), "votes": len(votes)},
        "evidenceUsage": {key: value for key, value in evidence.items() if value != "unknown"},
        "timelineEvents": len(timeline), "generatedAt": int(time.time() * 1000),
    }


def summary_markdown(summary: dict[str, Any]) -> str:
    ghosts = ", ".join(f"{name}: {count}" for name, count in summary.get("ghostStatistics", {}).items()) or "None confirmed"
    participation = summary.get("viewerParticipation", {})
    return "\n".join([
        f"# Investigation Summary - {summary.get('room', 'room')}", "",
        f"- Rounds played: {summary.get('roundsPlayed', 0)}", f"- Duration: {round(summary.get('durationMs', 0) / 60000, 1)} minutes",
        f"- Map: {summary.get('map', 'unknown')}", f"- Difficulty: {summary.get('difficulty', 'unknown')}",
        f"- Ghosts: {ghosts}", f"- Viewer participants: {participation.get('uniqueViewers', 0)}", "",
        "## Evidence used", "",
        *[f"- {key}: {value}" for key, value in summary.get("evidenceUsage", {}).items()], "",
    ])


def summary_csv(summary: dict[str, Any]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["room", "rounds_played", "duration_ms", "map", "difficulty", "viewer_participants", "timeline_events"])
    writer.writerow([summary.get("room"), summary.get("roundsPlayed"), summary.get("durationMs"), summary.get("map"), summary.get("difficulty"), summary.get("viewerParticipation", {}).get("uniqueViewers"), summary.get("timelineEvents")])
    return output.getvalue()


def analytics_from_states(states: list[dict[str, Any]]) -> dict[str, Any]:
    summaries = [session_summary(state) for state in states]
    completed = [state for state in states if (state.get("contractResult") or {}).get("confirmedGhost")]
    durations = [summary["durationMs"] for summary in summaries if summary["durationMs"] > 0]
    maps = Counter(str(state.get("map") or "unknown") for state in states)
    difficulties = Counter(str(state.get("difficulty") or "unknown") for state in states)
    ghosts = Counter((state.get("contractResult") or {}).get("confirmedGhost") for state in completed)
    correct = sum(int((state.get("contractResult") or {}).get("correctGuesses") or 0) for state in states)
    wrong = sum(int((state.get("contractResult") or {}).get("wrongGuesses") or 0) for state in states)
    return {
        "lifetimeInvestigations": len(states), "completedInvestigations": len(completed),
        "successRate": round((correct / (correct + wrong)) * 100, 1) if correct + wrong else 0,
        "averageInvestigationTimeMs": round(sum(durations) / len(durations)) if durations else 0,
        "favoriteMaps": maps.most_common(5), "favoriteDifficulties": difficulties.most_common(5),
        "ghostFrequency": ghosts.most_common(), "longestInvestigationMs": max(durations, default=0),
        "fastestInvestigationMs": min(durations, default=0),
        "mostCorrectGhost": ghosts.most_common(1)[0][0] if ghosts else None,
    }
