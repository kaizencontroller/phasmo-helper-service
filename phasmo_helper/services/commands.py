from __future__ import annotations

from typing import Any, Dict, Tuple
from ..core.config import _config_bool
from ..core.data import (
    BEHAVIOR_ALIASES, BEHAVIOR_INDEX_IDS, DIFFICULTY_ALIASES, EVIDENCE_ALIASES,
    EVIDENCE_LABELS, GHOST_NAMES, MAP_ALIASES, TIMER_ALIASES, TIMER_DEFAULT_SECONDS,
    WEATHER_ALIASES, GHOST_TESTS
)
from ..core.utils import _match_setup_value, _normalize_value, _normal_user, _normal_ghost, _now_ms
from .leaderboard import _score_contract_result
from .state import _new_reset_state

def _start_timer(state: Dict[str, Any], key: str, seconds: int | None = None):
    duration = int(seconds or TIMER_DEFAULT_SECONDS.get(key, 60))
    state.setdefault("timers", {})[key] = {
        "startedAt": _now_ms(),
        "durationSeconds": max(1, duration),
        "running": True,
    }


def _stop_timer(state: Dict[str, Any], key: str):
    state.setdefault("timers", {}).pop(key, None)


def _clear_timers(state: Dict[str, Any]):
    state["timers"] = {}


def _ghost_test_summary(ghost: str) -> str:
    checks = GHOST_TESTS.get(ghost)
    if not checks:
        return f"No quick test notes are configured for {ghost} yet."
    return f"{ghost} quick checks: " + " | ".join(checks[:3])


def apply_command(state: Dict[str, Any], command: str, user: str | None = None) -> Tuple[Dict[str, Any], str]:
    text = (command or "").strip()
    parts = text.split()
    lower_parts = text.lower().split()
    if not parts:
        return state, "No command entered."
    cmd = lower_parts[0]
    # Streamer.bot can provide the triggered command without the leading "!".
    # Normalize both "!behavior 7 yes" and "behavior 7 yes" to the same internal command.
    if cmd and not cmd.startswith("!"):
        cmd = "!" + cmd
        lower_parts[0] = cmd
        parts[0] = "!" + parts[0].lstrip("!")

    def _disabled(setting: str, label: str) -> Tuple[Dict[str, Any], str] | None:
        if not _config_bool(setting):
            return state, f"{label} are disabled in Phasmo Helper Config."
        return None

    setup_cmds = {"!setup", "!map", "!level", "!difficulty", "!diff", "!weather", "!players", "!playercount"}
    evidence_cmds = {"!mode", "!evidencemode", "!responds", "!response", "!interact", "!yes", "!no", "!maybe", "!clear", "!ev", "!evidence"}
    behavior_cmds = {"!b", "!beh", "!behavior", "!behaviour", "!be", "!behaviorentry", "!behaviorline", "!observed"}
    timer_cmds = {"!timer", "!timers", "!starttimer", "!stoptimer", "!incense", "!smudge", "!hunt", "!cooldown", "!cd"}
    sanity_cmds = {"!sanity", "!sane", "!huntat", "!huntsanity", "!huntnow", "!loghunt"}
    witnessed_cmds = {"!manifest", "!presentation", "!gender", "!model", "!witnessed", "!nameclue", "!name", "!female", "!male", "!unknownmodel"}
    viewer_vote_cmds = {"!guess", "!vote", "!unguess", "!clearguess", "!unvote", "!clearvote", "!guesses", "!votes"}
    manual_ghost_cmds = {"!ghost", "!select", "!notghost", "!restoreghost", "!clearghost", "!actual", "!actualghost", "!confirmghost", "!result"}
    ignore_cmds = {"!ignore", "!unignore", "!ignored", "!ignorelist"}
    next_round_cmds = {"!nextround", "!nextcontract", "!newround"}

    for setting, label, group in (
        ("allowSetupCommands", "Setup/map commands", setup_cmds),
        ("allowEvidenceCommands", "Evidence commands", evidence_cmds),
        ("allowBehaviorCommands", "Behavior commands", behavior_cmds),
        ("allowTimerCommands", "Timer commands", timer_cmds),
        ("allowSanityCommands", "Sanity commands", sanity_cmds),
        ("allowWitnessedCommands", "Witnessed model/name clue commands", witnessed_cmds),
        ("allowViewerVoteCommands", "Viewer guess/vote commands", viewer_vote_cmds),
        ("allowManualGhostCommands", "Manual ghost override commands", manual_ghost_cmds),
        ("allowIgnoreCommands", "Ignore-list commands", ignore_cmds),
        ("allowNextRoundCommand", "Next Round commands", next_round_cmds),
    ):
        if cmd in group:
            blocked = _disabled(setting, label)
            if blocked:
                return blocked

    if cmd == "!panic":
        if not _config_bool("allowPanicCommand") or not _config_bool("allowEasterEggs"):
            return state, "Panic/easter-egg commands are disabled in Phasmo Helper Config."

    sender = _normal_user(user)
    ignored_set = set(state.get("ignoredUsers") or [])
    if sender in ignored_set and cmd not in {"!unignore", "!ignored", "!ignorelist"}:
        return state, f"{sender} is ignored for this room."

    if cmd in {"!ignore", "!unignore", "!ignored", "!ignorelist"}:
        if cmd in {"!ignored", "!ignorelist"}:
            ignored = sorted(set(state.get("ignoredUsers") or []))
            return state, "Ignored users: " + (", ".join(ignored) if ignored else "none.")
        if len(parts) < 2:
            return state, f"Use {cmd} username."
        target = _normal_user(parts[1])
        ignored = set(state.get("ignoredUsers") or [])
        if cmd == "!ignore":
            ignored.add(target)
            state["ignoredUsers"] = sorted(ignored)
            state.setdefault("guesses", {}).pop(target, None)
            state.setdefault("votes", {}).pop(target, None)
            return state, f"{target} is now ignored for Phasmo Helper chat inputs. Their guess/vote was cleared."
        ignored.discard(target)
        state["ignoredUsers"] = sorted(ignored)
        return state, f"{target} is no longer ignored."

    if cmd in {"!reset", "!phasmoreset"}:
        previous_ignored = state.get("ignoredUsers", []) or []
        previous_code = state.get("roomCode", "") or ""
        new_state = _new_reset_state(state.get("room", "default"))
        new_state["ignoredUsers"] = previous_ignored
        new_state["roomCode"] = previous_code
        return new_state, f"Run reset. Setup required. Ignored users preserved."

    if cmd in {"!nextround", "!nextcontract", "!newround"}:
        previous = dict(state)
        new_state = _new_reset_state(state.get("room", "default"))
        new_state["setupComplete"] = False
        new_state["playerCount"] = previous.get("playerCount", 4)
        new_state["difficulty"] = previous.get("difficulty", "unknown")
        new_state["responds"] = previous.get("responds", "unknown")
        new_state["evidenceMode"] = previous.get("evidenceMode", "3")
        new_state["controlMode"] = previous.get("controlMode", "helper")
        new_state["overlayMode"] = previous.get("overlayMode", "helper")
        new_state["ignoredUsers"] = previous.get("ignoredUsers", []) or []
        new_state["roomCode"] = previous.get("roomCode", "") or ""
        new_state["map"] = "unknown"
        new_state["weather"] = "unknown"
        return new_state, "Next round started. Preserved players, difficulty, response, evidence mode, and ignored users; cleared map and weather."

    if cmd in {"!setup"}:
        # Basic setup helper:
        #   !setup
        #   !setup start
        #   !setup tanglewood professional sunrise everyone 4
        if len(parts) == 1 or (len(lower_parts) > 1 and lower_parts[1] in {"start", "save", "ready", "go"}):
            state["setupComplete"] = True
            return state, "Setup marked complete."
        raw = " ".join(parts[1:])
        # Try a loose positional parse: map difficulty weather responds players.
        if len(parts) >= 2:
            # Map may be multiple words; do best-effort lookup from all non-option words first.
            for cut in range(len(parts), 1, -1):
                candidate = _match_setup_value(" ".join(parts[1:cut]), MAP_ALIASES)
                if candidate:
                    state["map"] = candidate
                    rest = [p.lower() for p in parts[cut:]]
                    for token in rest:
                        if token in DIFFICULTY_ALIASES:
                            state["difficulty"] = DIFFICULTY_ALIASES[token]
                        elif token in WEATHER_ALIASES:
                            state["weather"] = WEATHER_ALIASES[token]
                        elif token in {"alone", "solo"}:
                            state["responds"] = "alone"
                        elif token in {"everyone", "all", "group"}:
                            state["responds"] = "everyone"
                        elif token.isdigit():
                            state["playerCount"] = max(1, min(4, int(token)))
                    state["setupComplete"] = True
                    return state, f"Setup saved: {state.get('map', 'unknown')} • {state.get('difficulty', 'unknown')} • {state.get('weather', 'unknown')} • Responds: {state.get('responds', 'unknown')} • {state.get('playerCount', 4)} player(s)."
        return state, "Use !setup, or set fields with !map, !difficulty, !weather, !responds, and !players."

    if cmd in {"!map", "!level"}:
        value = _match_setup_value(" ".join(parts[1:]), MAP_ALIASES)
        if not value:
            return state, "Map not recognized. Try !map tanglewood, !map ridgeview, !map willow, !map edgefield, !map nells, !map grafton, !map woodwind, !map point hope, !map bleasdale, !map restricted, !map prison, !map maple, !map brownstone, or !map sunny."
        state["map"] = value
        return state, f"Map set to {value}."

    if cmd in {"!difficulty", "!diff"}:
        value = _match_setup_value(" ".join(parts[1:]), DIFFICULTY_ALIASES)
        if not value:
            return state, "Difficulty not recognized. Try amateur, intermediate, professional, nightmare, insanity, or custom."
        state["difficulty"] = value
        # Keep evidence mode roughly aligned unless user overrides it manually later.
        if value in {"nightmare"}:
            state["evidenceMode"] = "2"
        elif value in {"insanity"}:
            state["evidenceMode"] = "1"
        elif value in {"amateur", "intermediate", "professional"}:
            state["evidenceMode"] = "3"
        return state, f"Difficulty set to {value}."

    if cmd in {"!weather"}:
        value = _match_setup_value(" ".join(parts[1:]), WEATHER_ALIASES)
        if not value:
            return state, "Weather not recognized. Try sunrise, clear, fog, blood moon, light rain, heavy rain, windy, or snow."
        state["weather"] = value
        return state, f"Weather set to {value}."

    if cmd in {"!players", "!playercount"}:
        try:
            count = max(1, min(4, int(lower_parts[1])))
        except Exception:
            return state, "Use !players 1, !players 2, !players 3, or !players 4."
        state["playerCount"] = count
        return state, f"Player count set to {count}."

    if cmd in {"!panic"}:
        now_ms = int(time.time() * 1000)
        cooldown_until = int(state.get("panicCooldownUntil") or 0)
        if cooldown_until > now_ms:
            remaining = max(1, round((cooldown_until - now_ms) / 1000))
            return state, f"Panic is on cooldown for {remaining}s."
        state["panicCount"] = int(state.get("panicCount") or 0) + 1
        user_name = (user or "chat").strip() or "chat"
        state["panicUser"] = user_name
        state["panicNote"] = "PANIC DECLARED"
        state["panicTakeoverUntil"] = now_ms + 5000
        state["panicUntil"] = now_ms + 15000
        state["panicCooldownUntil"] = now_ms + 60000
        state["panicSeq"] = int(state.get("panicSeq") or 0) + 1
        return state, "Panic declared. Overlay takeover: 5s. Note: 10s. Cooldown: 60s."

    if cmd in {"!mode", "!evidencemode"}:
        mode = lower_parts[1] if len(lower_parts) > 1 else ""
        if mode in {"0", "1", "2", "3"}:
            state["evidenceMode"] = mode
            return state, f"Evidence mode set to {mode}."
        return state, "Use !mode 3, !mode 2, !mode 1, or !mode 0."

    if cmd in {"!responds", "!response", "!interact"}:
        value = lower_parts[1] if len(lower_parts) > 1 else "unknown"
        if value in {"alone", "solo"}:
            state["responds"] = "alone"
        elif value in {"everyone", "all", "group"}:
            state["responds"] = "everyone"
        else:
            state["responds"] = "unknown"
        return state, f"Responds set to {state['responds']}."

    if cmd in {"!sanity", "!sane"}:
        vals = []
        for raw in parts[1:5]:
            try:
                vals.append(max(0, min(100, int(round(float(raw))))))
            except Exception:
                vals.append(None)
        if not vals:
            return state, "Use !sanity 90 85 80 75."
        state["sanityValues"] = vals + [None] * max(0, 4 - len(vals))
        state["sanityTouched"] = any(v is not None for v in state["sanityValues"][: int(state.get("playerCount") or 4)])
        active = [v for v in state["sanityValues"][: int(state.get("playerCount") or 4)] if v is not None]
        avg = round(sum(active) / len(active)) if active else None
        return state, f"Sanity updated. Average: {avg if avg is not None else 'unknown'}%."

    if cmd in {"!huntat", "!huntsanity"}:
        try:
            state["huntSanity"] = max(0, min(100, int(round(float(lower_parts[1])))))
            return state, f"Hunt sanity logged at {state['huntSanity']}%."
        except Exception:
            return state, "Use !huntat 65."

    if cmd in {"!huntnow", "!loghunt"}:
        vals = state.get("sanityValues") or []
        active = [v for v in vals[: int(state.get("playerCount") or 4)] if isinstance(v, (int, float))]
        if not active:
            return state, "No sanity values saved. Use !sanity first."
        state["huntSanity"] = round(sum(active) / len(active))
        return state, f"Hunt logged at {state['huntSanity']}% average sanity."

    if cmd in {"!manifest", "!presentation", "!gender", "!model", "!witnessed", "!nameclue", "!name", "!female", "!male", "!unknownmodel"}:
        if cmd == "!female":
            value = "female"
        elif cmd == "!male":
            value = "male"
        elif cmd == "!unknownmodel":
            value = "unknown"
        else:
            value = lower_parts[1] if len(lower_parts) > 1 else "unknown"
        if value in {"female", "f", "woman", "girl", "girl-name", "fem"}:
            state["presentation"] = "female"
        elif value in {"male", "m", "man", "boy", "boy-name", "masc"}:
            state["presentation"] = "male"
        else:
            state["presentation"] = "unknown"
        return state, f"Witnessed model/name clue set to {state['presentation']}."

    if cmd in {"!yes", "!no", "!maybe", "!clear"}:
        # Streamer.bot import compatibility. These apply to the next best unknown evidence.
        # Prefer explicit !ev orb yes for serious use.
        ev_order = ["dots", "emf5", "freezing", "orbs", "writing", "box", "uv"]
        target = next((ev for ev in ev_order if state.get("evidence", {}).get(ev, "unknown") == "unknown"), None)
        if not target:
            return state, "No unknown evidence found. Use !ev [evidence] [yes/no/unknown] to change a specific item."
        value = {"!yes": "yes", "!no": "no", "!maybe": "unknown", "!clear": "unknown"}[cmd]
        state.setdefault("evidence", {})[target] = value
        return state, f"{EVIDENCE_LABELS.get(target, target)} set to {value}. For better control use !ev [evidence] [yes/no]."

    if cmd in {"!ev", "!evidence"}:
        key = EVIDENCE_ALIASES.get(lower_parts[1], "") if len(lower_parts) > 1 else ""
        if not key:
            return state, f"Unknown evidence: {parts[1] if len(parts) > 1 else 'blank'}."
        value = _normalize_value(lower_parts[2] if len(lower_parts) > 2 else "unknown", "evidence")
        state.setdefault("evidence", {})[key] = value
        return state, f"{EVIDENCE_LABELS[key]} set to {value}."

    if cmd in {"!timer", "!timers", "!starttimer", "!stoptimer"}:
        if len(lower_parts) == 1:
            return state, "Use !timer incense start, !timer hunt start, !timer cooldown start, or !timer clear."
        if cmd in {"!starttimer", "!stoptimer"}:
            key = TIMER_ALIASES.get(lower_parts[1])
            if not key:
                return state, f"Unknown timer: {parts[1]}. Use incense, hunt, or cooldown."
            if cmd == "!starttimer":
                seconds = int(lower_parts[2]) if len(lower_parts) > 2 and lower_parts[2].isdigit() else None
                _start_timer(state, key, seconds)
                return state, f"{key.title()} timer started."
            _stop_timer(state, key)
            return state, f"{key.title()} timer cleared."
        if lower_parts[1] in {"clear", "reset", "stopall"}:
            _clear_timers(state)
            return state, "All timers cleared."
        key = TIMER_ALIASES.get(lower_parts[1])
        if not key:
            return state, f"Unknown timer: {parts[1]}. Use incense, hunt, or cooldown."
        action = lower_parts[2] if len(lower_parts) > 2 else "start"
        custom_seconds = None
        if len(lower_parts) > 3 and lower_parts[3].isdigit():
            custom_seconds = int(lower_parts[3])
        if action in {"start", "go", "begin", "restart"}:
            _start_timer(state, key, custom_seconds)
            return state, f"{key.title()} timer started."
        if action in {"stop", "clear", "reset", "done"}:
            _stop_timer(state, key)
            return state, f"{key.title()} timer cleared."
        if action.isdigit():
            _start_timer(state, key, int(action))
            return state, f"{key.title()} timer started for {action} seconds."
        return state, "Use start, stop, clear, or a duration in seconds."

    if cmd in {"!incense", "!smudge"}:
        _start_timer(state, "incense")
        return state, "Incense timer started."

    if cmd in {"!hunt"}:
        _start_timer(state, "hunt")
        return state, "Hunt timer started."

    if cmd in {"!cooldown", "!cd"}:
        _start_timer(state, "cooldown")
        return state, "Cooldown timer started."

    if cmd in {"!tests", "!test"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown ghost for quick tests: {ghost_text or 'blank'}."
        return state, _ghost_test_summary(ghost)

    if cmd in {"!ghost", "!select", "!notghost", "!restoreghost", "!clearghost"}:
        action = lower_parts[1] if len(lower_parts) > 1 else ""
        manual = state.setdefault("manualGhosts", {"selected": None, "excluded": []})
        manual.setdefault("excluded", [])

        if cmd == "!clearghost":
            action = "clear"
            ghost_text = ""
        elif cmd == "!notghost":
            action = "not"
            ghost_text = " ".join(parts[1:])
        elif cmd == "!restoreghost":
            action = "restore"
            ghost_text = " ".join(parts[1:])
        elif cmd == "!select":
            action = "select"
            ghost_text = " ".join(parts[1:])
        else:
            ghost_text = " ".join(parts[2:]) if action in {"not", "exclude", "out", "restore", "select", "force", "clear"} else " ".join(parts[1:])

        if action in {"clear", "reset"}:
            state["manualGhosts"] = {"selected": None, "excluded": []}
            return state, "Manual ghost overrides cleared."

        if action in {"not", "exclude", "out"}:
            ghost = _normal_ghost(ghost_text)
            if not ghost:
                return state, f"Unknown ghost to exclude: {ghost_text or 'blank'}."
            if ghost not in manual["excluded"]:
                manual["excluded"].append(ghost)
            if manual.get("selected") == ghost:
                manual["selected"] = None
            return state, f"{ghost} manually excluded."

        if action == "restore":
            ghost = _normal_ghost(ghost_text)
            if not ghost:
                return state, f"Unknown ghost to restore: {ghost_text or 'blank'}."
            manual["excluded"] = [g for g in manual.get("excluded", []) if g != ghost]
            return state, f"{ghost} restored to the candidate pool."

        if action in {"select", "force"}:
            ghost = _normal_ghost(ghost_text)
            if not ghost:
                return state, f"Unknown ghost to select: {ghost_text or 'blank'}."
            manual["selected"] = ghost
            manual["excluded"] = [g for g in manual.get("excluded", []) if g != ghost]
            return state, f"{ghost} manually selected."

        # If !ghost is not being used as an override, treat it as a viewer guess.
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown ghost guess: {ghost_text or 'blank'}."
        voter = _normal_user(user)
        state.setdefault("votes", {})[voter] = ghost
        return state, f"{voter} voted for {ghost}."

    if cmd in {"!actual", "!actualghost", "!confirmghost", "!result"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown actual ghost: {ghost_text or 'blank'}."
        return _score_contract_result(state, ghost, confirmed_by=user or "control")

    if cmd in {"!guess"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown lucky guess: {ghost_text or 'blank'}."
        voter = _normal_user(user)
        state.setdefault("guesses", {})[voter] = ghost
        return state, f"{voter} locked in a lucky guess for {ghost}."

    if cmd in {"!vote"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown decision vote: {ghost_text or 'blank'}."
        voter = _normal_user(user)
        state.setdefault("votes", {})[voter] = ghost
        return state, f"{voter} voted for {ghost} as decision input."

    if cmd in {"!unvote", "!clearvote"}:
        voter = _normal_user(user)
        state.setdefault("votes", {}).pop(voter, None)
        return state, f"{voter}'s decision vote was cleared."

    if cmd in {"!unguess", "!clearguess"}:
        voter = _normal_user(user)
        state.setdefault("guesses", {}).pop(voter, None)
        return state, f"{voter}'s lucky guess was cleared."

    if cmd in {"!votes"}:
        votes = state.get("votes", {}) or {}
        if not votes:
            return state, "No decision votes yet."
        counts: dict[str, int] = {}
        for ghost in votes.values():
            counts[ghost] = counts.get(ghost, 0) + 1
        summary = ", ".join(f"{ghost}: {count}" for ghost, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))
        return state, f"Decision votes: {summary}."

    if cmd in {"!guesses"}:
        guesses = state.get("guesses", {}) or {}
        if not guesses:
            return state, "No lucky guesses yet."
        counts: dict[str, int] = {}
        for ghost in guesses.values():
            counts[ghost] = counts.get(ghost, 0) + 1
        summary = ", ".join(f"{ghost}: {count}" for ghost, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))
        return state, f"Lucky guesses: {summary}."

    if cmd in {"!b", "!beh", "!behavior", "!behaviour", "!be", "!behaviorentry", "!behaviorline", "!observed"}:
        if not _config_bool("allowBehaviorCommands"):
            return state, "Behavior chat commands are disabled in Phasmo Helper Config."
        if len(lower_parts) <= 1:
            return state, "Use !behavior 7 yes, !behavior 7 no, !observed 7, or !behavior wraith yes."

        target = lower_parts[1]
        raw_value = lower_parts[2] if len(lower_parts) > 2 else "observed"

        # Streamer.bot import has a dedicated !observed command, so default it to yes/observed.
        if cmd == "!observed" and len(lower_parts) == 2:
            raw_value = "observed"

        # Numbered behavior rows shown in the Behavior Branches UI.
        if target.isdigit():
            entry_num = int(target)
            if entry_num < 1 or entry_num > len(BEHAVIOR_INDEX_IDS):
                return state, f"Behavior number must be between 1 and {len(BEHAVIOR_INDEX_IDS)}."
            key = BEHAVIOR_INDEX_IDS[entry_num - 1]
            value = _normalize_value(raw_value, "behavior")
            state.setdefault("behaviors", {})[key] = value
            return state, f"Behavior #{entry_num} set to {value}."

        # Alias-based behavior commands, such as !behavior wraith yes or !b no-salt yes.
        key = BEHAVIOR_ALIASES.get(target, "")
        if not key:
            # Common typo helper: allow labels pasted with spaces after !behavior by joining everything except final yes/no.
            maybe_value = lower_parts[-1] if len(lower_parts) > 2 else "observed"
            maybe_alias = "-".join(lower_parts[1:-1]) if len(lower_parts) > 2 else target
            key = BEHAVIOR_ALIASES.get(maybe_alias, "")
            raw_value = maybe_value if key else raw_value
        if not key:
            return state, f"Unknown behavior: {parts[1] if len(parts) > 1 else 'blank'}. Use the visible row number, e.g. !behavior 7 yes."
        value = _normalize_value(raw_value, "behavior")
        state.setdefault("behaviors", {})[key] = value
        return state, f"Behavior {key} set to {value}."

    return state, "Command not recognized. Try !map tanglewood, !difficulty professional, !weather fog, !players 4, !setup, !ev emf yes, !behavior 12 yes, !observed 12, !gender male, !sanity 90 85 80 75, !huntat 65, !manifest male, !timer incense start, !ghost not Wraith, !tests Deogen, !guess Deogen, !vote Wraith, or !reset."

