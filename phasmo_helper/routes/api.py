from __future__ import annotations

import json
import time
from fastapi import APIRouter, Header, HTTPException, Query, Request
from .. import settings
from ..core.config import _config_bool
from ..core.data import EVIDENCE, GHOST_NAMES
from ..core.utils import _normal_user
from ..services.commands import apply_command
from ..services.leaderboard import _score_contract_result
from ..services.reports import _bug_report_path, _feedback_path, maybe_record_support_ping
from ..services.rooms import active_room_summaries, cleanup_inactive_rooms
from ..services.banner import read_banner, write_banner
from ..services.security import ensure_valid_room_name, passcode_attempt_allowed, record_failed_passcode
from ..services.maintenance import read_maintenance, start_maintenance, end_maintenance, require_ops_token, state_dir_health, maintenance_write_blocked
from ..services.streamerbot import get_default_room, get_profile, parse_room_command, set_default_room
from ..services.state import (
    _auth_ok, _clean_room_code, _new_reset_state, _read_jumpscare_count, _room_code_ok, _room_name, _write_jumpscare_count,
    public_state, read_state, write_state, _state_path,
)

router = APIRouter()


@router.get("/api/phasmo/health")
def api_phasmo_health():
    maint = read_maintenance()
    state_dir = state_dir_health()
    ok = bool(state_dir.get("exists") and state_dir.get("writable"))
    return {
        "ok": ok,
        "status": "healthy" if ok else "degraded",
        "app": "phasmo-helper",
        "version": settings._APP_VERSION,
        "commit": settings._BUILD_COMMIT,
        "maintenance": maint,
        "stateDir": state_dir,
        "timestamp": int(time.time() * 1000),
    }


@router.get("/api/phasmo/version")
def api_phasmo_version():
    return {
        "ok": True,
        "app": "phasmo-helper",
        "version": settings._APP_VERSION,
        "commit": settings._BUILD_COMMIT,
        "railway": {
            "service": __import__("os").environ.get("RAILWAY_SERVICE_NAME", ""),
            "environment": __import__("os").environ.get("RAILWAY_ENVIRONMENT_NAME", ""),
            "publicDomain": __import__("os").environ.get("RAILWAY_PUBLIC_DOMAIN", ""),
        },
    }


@router.get("/api/phasmo/maintenance")
def api_phasmo_maintenance():
    return {"ok": True, "maintenance": read_maintenance()}


@router.post("/api/phasmo/ops/maintenance/start")
async def api_ops_maintenance_start(request: Request, authorization: str | None = Header(default=None), x_phasmo_ops_token: str | None = Header(default=None)):
    require_ops_token(authorization, x_phasmo_ops_token)
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"ok": True, "maintenance": start_maintenance(body if isinstance(body, dict) else {}, updated_by="github-actions")}


@router.post("/api/phasmo/ops/maintenance/end")
async def api_ops_maintenance_end(request: Request, authorization: str | None = Header(default=None), x_phasmo_ops_token: str | None = Header(default=None)):
    require_ops_token(authorization, x_phasmo_ops_token)
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"ok": True, "maintenance": end_maintenance(body if isinstance(body, dict) else {}, updated_by="github-actions")}


@router.post("/api/phasmo/ops/banner")
async def api_ops_banner(request: Request, authorization: str | None = Header(default=None), x_phasmo_ops_token: str | None = Header(default=None)):
    require_ops_token(authorization, x_phasmo_ops_token)
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    return {"ok": True, "banner": write_banner(body)}


@router.post("/api/phasmo/jumpscare")
def api_jumpscare(room: str | None = Query(default=None)):
    safe_room = _room_name(room)
    if not _config_bool("allowEasterEggs") or not _config_bool("allowJumpscareButton"):
        current = read_state(safe_room)
        return {"ok": False, "result": "Jumpscare button is disabled in Phasmo Helper Config.", "count": _read_jumpscare_count(), "state": current}
    with settings._STATE_LOCK:
        count = _write_jumpscare_count(_read_jumpscare_count() + 1)
        current = read_state(safe_room)
        current["jumpscareCount"] = count
        current["jumpscareUntil"] = int(time.time() * 1000) + 8500
        current["jumpscareSeq"] = int(current.get("jumpscareSeq") or 0) + 1
        write_state(safe_room, current)
    return {"ok": True, "count": count, "state": public_state(current)}


@router.get("/api/phasmo/rooms")
def api_phasmo_rooms():
    return {"ok": True, "ttlSeconds": settings._ROOM_TTL_SECONDS, "rooms": active_room_summaries()}


@router.get("/api/phasmo/banner")
def api_phasmo_banner():
    return {"ok": True, "banner": read_banner()}


@router.post("/api/phasmo/bug-report")
async def api_bug_report(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="bug report body must be JSON")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="bug report body must be an object")
    message = str(body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    now_ms = int(time.time() * 1000)
    payload = {
        "id": f"BR-{now_ms}-{_room_name(str(body.get('room') or 'default'))}",
        "createdAt": now_ms,
        "updatedAt": now_ms,
        "status": "new",
        "priority": "medium",
        "targetVersion": "",
        "fixedVersion": "",
        "internalNotes": "",
        "publicNotes": "",
        "name": str(body.get("name") or "")[:120],
        "contact": str(body.get("contact") or "")[:200],
        "category": str(body.get("category") or "bug")[:60],
        "room": _room_name(str(body.get("room") or "default")),
        "pageUrl": str(body.get("pageUrl") or body.get("page_url") or "")[:500],
        "message": message[:5000],
    }
    with settings._STATE_LOCK:
        with _bug_report_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return {"ok": True}


@router.post("/api/phasmo/feedback")
async def api_phasmo_feedback(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="feedback body must be JSON")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="feedback body must be an object")
    rating = str(body.get("rating") or "").strip().lower()
    if rating not in {"up", "down"}:
        raise HTTPException(status_code=400, detail="rating must be up or down")
    payload = {
        "createdAt": int(time.time() * 1000),
        "rating": rating,
        "room": _room_name(str(body.get("room") or "default")),
        "user": str(body.get("user") or "")[:120],
        "clientId": str(body.get("clientId") or "")[:160],
        "pageUrl": str(body.get("pageUrl") or body.get("page_url") or "")[:500],
    }
    with settings._STATE_LOCK:
        with _feedback_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return {"ok": True}


@router.get("/api/phasmo/state")
def api_get_state(request: Request, room: str | None = Query(default=None), code: str | None = Query(default=None)):
    ensure_valid_room_name(room or "default")
    safe_room = _room_name(room)
    with settings._STATE_LOCK:
        cleanup_inactive_rooms()
        current = read_state(safe_room)
        if current.get("roomStatus") == "closed":
            raise HTTPException(status_code=410, detail="room is closed")
        if not _room_code_ok(current, code or ""):
            record_failed_passcode(request, safe_room)
            raise HTTPException(status_code=403, detail="room passcode required")
        return public_state(current)


@router.post("/api/phasmo/state")
async def api_post_state(
    request: Request,
    room: str | None = Query(default=None),
    token: str | None = Query(default=None),
    code: str | None = Query(default=None),
    x_phasmo_token: str | None = Header(default=None),
):
    if not _auth_ok(x_phasmo_token, token):
        raise HTTPException(status_code=401, detail="unauthorized")
    ensure_valid_room_name(room or "default")
    safe_room = _room_name(room)
    body = await request.json()
    existing_room = _state_path(safe_room).exists()
    maintenance_msg = maintenance_write_blocked(existing_room)
    if maintenance_msg:
        raise HTTPException(status_code=503, detail=maintenance_msg)
    with settings._STATE_LOCK:
        cleanup_inactive_rooms()
        current = read_state(safe_room)
        # Authenticate locked-room edits with the existing code from the query/body.
        # Do not use the incoming roomPasscode as the auth value because that field
        # is also how the owner changes or clears the room passcode.
        supplied_code = code or body.get("currentRoomPasscode") or body.get("authRoomPasscode") or body.get("code") or ""
        if current.get("roomStatus") == "closed" and not body.get("reopenRoom"):
            raise HTTPException(status_code=410, detail="room is closed")
        if not _room_code_ok(current, supplied_code):
            record_failed_passcode(request, safe_room)
            raise HTTPException(status_code=403, detail="room passcode required")
        if body.get("endSession") is True or body.get("closeRoom") is True:
            current["roomStatus"] = "closed"
            current["closedAt"] = int(time.time() * 1000)
            current["closedBy"] = str(body.get("closedBy") or "control")[:120]
            current["lastCommand"] = "End Session"
            current["lastCommandResult"] = "Room closed. It has been removed from Active Rooms; scored history is preserved."
        elif body.get("reopenRoom") is True:
            current["roomStatus"] = "open"
            current["closedAt"] = 0
            current["closedBy"] = ""
            current["lastCommand"] = "Reopen Room"
            current["lastCommandResult"] = "Room reopened."
        elif body.get("reset") is True:
            previous = dict(current)
            current = _new_reset_state(safe_room)
            current["ignoredUsers"] = previous.get("ignoredUsers", []) or []
            current["roomCode"] = previous.get("roomCode", "") or ""
        elif body.get("nextRound") is True:
            previous = dict(current)
            current = _new_reset_state(safe_room)
            # Preserve reusable setup, but force map/weather back to unknown for the new contract.
            current["setupComplete"] = False
            current["playerCount"] = previous.get("playerCount", 4)
            current["difficulty"] = previous.get("difficulty", "unknown")
            current["responds"] = previous.get("responds", "unknown")
            current["evidenceMode"] = previous.get("evidenceMode", "3")
            current["controlMode"] = previous.get("controlMode", "helper")
            current["overlayMode"] = previous.get("overlayMode", "helper")
            current["ignoredUsers"] = previous.get("ignoredUsers", []) or []
            current["roomCode"] = previous.get("roomCode", "") or ""
            current["map"] = "unknown"
            current["weather"] = "unknown"
            current["lastCommand"] = "Next Round"
            current["lastCommandResult"] = "New round started. Preserved players, difficulty, response, evidence mode, and ignored chatters; cleared map and weather."
        else:
            if "evidence" in body and isinstance(body["evidence"], dict):
                current["evidence"].update({k: v for k, v in body["evidence"].items() if k in EVIDENCE and v in {"yes", "no", "unknown"}})
            if "behaviors" in body and isinstance(body["behaviors"], dict):
                current["behaviors"].update(body["behaviors"] or {})
            if "votes" in body and isinstance(body["votes"], dict):
                current["votes"].update(body["votes"] or {})
            if "guesses" in body and isinstance(body["guesses"], dict):
                current.setdefault("guesses", {}).update(body["guesses"] or {})
            if "timers" in body and isinstance(body["timers"], dict):
                current["timers"].update(body["timers"] or {})
            if "manualGhosts" in body and isinstance(body["manualGhosts"], dict):
                manual = body["manualGhosts"] or {}
                current.setdefault("manualGhosts", {"selected": None, "excluded": []})
                if "selected" in manual:
                    current["manualGhosts"]["selected"] = manual["selected"] if manual["selected"] in GHOST_NAMES else None
                if "excluded" in manual and isinstance(manual["excluded"], list):
                    current["manualGhosts"]["excluded"] = [g for g in manual["excluded"] if g in GHOST_NAMES]
            if "responds" in body:
                current["responds"] = body["responds"] if body["responds"] in {"unknown", "alone", "everyone"} else "unknown"
            if "evidenceMode" in body and str(body["evidenceMode"]) in {"0", "1", "2", "3"}:
                current["evidenceMode"] = str(body["evidenceMode"])
            if "controlMode" in body and str(body.get("controlMode")) in {"helper", "tracker"}:
                current["controlMode"] = str(body.get("controlMode"))
            if "overlayMode" in body and str(body.get("overlayMode")) in {"helper", "tracker"}:
                current["overlayMode"] = str(body.get("overlayMode"))
            if "setupComplete" in body:
                current["setupComplete"] = bool(body["setupComplete"])
            if "roomPasscode" in body or "roomCode" in body:
                # Empty or invalid values leave the room unlocked. A 4-digit value locks it.
                current["roomCode"] = _clean_room_code(body.get("roomPasscode") or body.get("roomCode"))
            if "classifiedUntil" in body:
                try:
                    current["classifiedUntil"] = max(0, int(float(body.get("classifiedUntil") or 0)))
                except Exception:
                    current["classifiedUntil"] = 0
            if "map" in body:
                current["map"] = str(body.get("map") or "unknown")[:120]
            if "difficulty" in body:
                current["difficulty"] = str(body.get("difficulty") or "unknown")[:40]
            if "weather" in body:
                current["weather"] = str(body.get("weather") or "unknown")[:40]
            if "playerCount" in body:
                try:
                    current["playerCount"] = max(1, min(4, int(body.get("playerCount") or 4)))
                except Exception:
                    current["playerCount"] = 4
            if "sanityValues" in body and isinstance(body["sanityValues"], list):
                vals = []
                for item in body["sanityValues"][:4]:
                    try:
                        vals.append(max(0, min(100, int(round(float(item))))) if item not in {None, ""} else None)
                    except Exception:
                        vals.append(None)
                current["sanityValues"] = vals + [None] * max(0, 4 - len(vals))
                current["sanityTouched"] = any(v is not None for v in current["sanityValues"][: int(current.get("playerCount") or 4)])
            if "huntSanity" in body:
                try:
                    current["huntSanity"] = None if body.get("huntSanity") in {None, ""} else max(0, min(100, int(round(float(body.get("huntSanity"))))))
                except Exception:
                    current["huntSanity"] = None
            if "presentation" in body:
                current["presentation"] = body.get("presentation") if body.get("presentation") in {"unknown", "female", "male"} else "unknown"
            if "cursedItems" in body and isinstance(body["cursedItems"], dict):
                current.setdefault("cursedItems", {})
                for k, v in body["cursedItems"].items():
                    key = str(k).lower()[:80]
                    if str(v) in {"found", "out", "unknown"}:
                        current["cursedItems"][key] = str(v)
            if "ignoredUsers" in body and isinstance(body["ignoredUsers"], list):
                current["ignoredUsers"] = sorted({_normal_user(u) for u in body["ignoredUsers"] if str(u).strip()})
            if "supportOptIn" in body:
                current["supportOptIn"] = bool(body.get("supportOptIn"))
            if "supportChannel" in body:
                current["supportChannel"] = str(body.get("supportChannel") or "")[:160]
            if "supportContact" in body:
                current["supportContact"] = str(body.get("supportContact") or "")[:200]
            if "supportNote" in body:
                current["supportNote"] = str(body.get("supportNote") or "")[:500]
            if "contractResult" in body and isinstance(body["contractResult"], dict):
                result_patch = body.get("contractResult") or {}
                confirmed = result_patch.get("confirmedGhost")
                if confirmed:
                    current, score_msg = _score_contract_result(current, str(confirmed), str(result_patch.get("confirmedBy") or "control"))
                    current["lastCommand"] = "Confirm Result"
                    current["lastCommandResult"] = score_msg
        write_state(safe_room, current)
    return {"ok": True, "state": public_state(current)}




@router.get("/api/phasmo/command")
def api_get_command(
    request: Request,
    room: str | None = Query(default=None),
    command: str | None = Query(default=""),
    user: str | None = Query(default=None),
    username: str | None = Query(default=None),
    userName: str | None = Query(default=None),
    displayName: str | None = Query(default=None),
    source: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    streamer: str | None = Query(default=None),
    bot: str | None = Query(default=None),
    botAccount: str | None = Query(default=None),
    token: str | None = Query(default=None),
    code: str | None = Query(default=None),
    x_phasmo_token: str | None = Header(default=None),
):
    """Compatibility endpoint for Streamer.bot imports that send commands as a GET URL.

    Room routing priority: explicit ?room=, stored Streamer.bot default room for channel/bot,
    then "default". Use !phasmo-room <room> to update the stored default room.
    """
    if not _auth_ok(x_phasmo_token, token):
        raise HTTPException(status_code=401, detail="unauthorized")
    cmd_text = (command or "").strip()
    sender = user or username or userName or displayName or "anonymous"
    channel_name = channel or streamer or ""
    bot_name = botAccount or bot or ""
    requested_room = parse_room_command(cmd_text)
    with settings._STATE_LOCK:
        if requested_room:
            ensure_valid_room_name(requested_room)
            profile = set_default_room(requested_room, channel=channel_name, bot_account=bot_name, user=sender)
            safe_room = requested_room
            state = read_state(safe_room)
            state["lastCommand"] = cmd_text
            state["lastCommandResult"] = f"Streamer.bot default room set to {safe_room}."
            write_state(safe_room, state)
            return {"ok": True, "room": safe_room, "result": f"Phasmo room set to {safe_room}.", "profile": profile, "state": public_state(state)}
        selected_room = room or get_default_room(channel=channel_name, bot_account=bot_name, user=sender) or "default"
        ensure_valid_room_name(str(selected_room))
        safe_room = _room_name(str(selected_room))
        state = read_state(safe_room)
        if state.get("roomStatus") == "closed":
            raise HTTPException(status_code=410, detail="room is closed")
        maintenance_msg = maintenance_write_blocked(_state_path(safe_room).exists())
        if maintenance_msg:
            raise HTTPException(status_code=503, detail=maintenance_msg)
        if not _room_code_ok(state, code or ""):
            record_failed_passcode(request, safe_room)
            raise HTTPException(status_code=403, detail="room passcode required")
        state, result = apply_command(state, cmd_text, user=sender)
        state["lastCommand"] = cmd_text
        state["lastCommandResult"] = result
        support_ping = maybe_record_support_ping(
            state,
            room=safe_room,
            user=sender,
            command=cmd_text,
            source=source or "streamerbot-get",
            channel=channel_name,
            bot_account=bot_name,
        )
        write_state(safe_room, state)
    return {"ok": True, "room": safe_room, "result": result, "supportPing": bool(support_ping), "state": public_state(state)}


@router.post("/api/phasmo/command")
async def api_post_command(
    request: Request,
    room: str | None = Query(default=None),
    token: str | None = Query(default=None),
    code: str | None = Query(default=None),
    x_phasmo_token: str | None = Header(default=None),
):
    if not _auth_ok(x_phasmo_token, token):
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        body = await request.json()
    except Exception:
        raw = (await request.body()).decode("utf-8", errors="ignore")
        body = {"command": raw}
    if not isinstance(body, dict):
        body = {"command": str(body)}
    command = body.get("command") or body.get("rawInput") or body.get("message") or ""
    user = body.get("user") or body.get("username") or body.get("displayName") or body.get("userName") or "anonymous"
    source = body.get("source") or body.get("client") or "streamerbot-post"
    channel = body.get("channel") or body.get("streamer") or body.get("broadcaster") or ""
    bot_account = body.get("botAccount") or body.get("bot") or body.get("botUser") or ""
    requested_room = parse_room_command(str(command))
    with settings._STATE_LOCK:
        if requested_room:
            ensure_valid_room_name(requested_room)
            profile = set_default_room(requested_room, channel=channel, bot_account=bot_account, user=user)
            state = read_state(requested_room)
            state["lastCommand"] = command
            state["lastCommandResult"] = f"Streamer.bot default room set to {requested_room}."
            write_state(requested_room, state)
            return {"ok": True, "room": requested_room, "result": f"Phasmo room set to {requested_room}.", "profile": profile, "state": public_state(state)}
        selected_room = room or body.get("room") or body.get("phasmoRoom") or body.get("roomName") or get_default_room(channel=channel, bot_account=bot_account, user=user) or "default"
        ensure_valid_room_name(str(selected_room))
        safe_room = _room_name(str(selected_room))
        state = read_state(safe_room)
        if state.get("roomStatus") == "closed":
            raise HTTPException(status_code=410, detail="room is closed")
        maintenance_msg = maintenance_write_blocked(_state_path(safe_room).exists())
        if maintenance_msg:
            raise HTTPException(status_code=503, detail=maintenance_msg)
        supplied_code = body.get("roomPasscode") or body.get("roomCode") or body.get("code") or code or ""
        if not _room_code_ok(state, supplied_code):
            record_failed_passcode(request, safe_room)
            raise HTTPException(status_code=403, detail="room passcode required")
        state, result = apply_command(state, command, user=user)
        state["lastCommand"] = command
        state["lastCommandResult"] = result
        support_ping = maybe_record_support_ping(
            state,
            room=safe_room,
            user=user,
            command=command,
            source=source,
            channel=channel,
            bot_account=bot_account,
            base_url=str(request.base_url).rstrip("/"),
        )
        write_state(safe_room, state)
    return {"ok": True, "room": safe_room, "result": result, "supportPing": bool(support_ping), "state": public_state(state)}


@router.get("/api/phasmo/streamerbot/profile")
def api_streamerbot_profile(
    channel: str | None = Query(default=None),
    streamer: str | None = Query(default=None),
    bot: str | None = Query(default=None),
    botAccount: str | None = Query(default=None),
    user: str | None = Query(default=None),
):
    channel_name = channel or streamer or ""
    bot_name = botAccount or bot or ""
    profile = get_profile(channel=channel_name, bot_account=bot_name, user=user)
    return {"ok": True, "profile": profile, "defaultRoom": profile.get("defaultRoom") if isinstance(profile, dict) else ""}


@router.post("/api/phasmo/streamerbot/profile")
async def api_streamerbot_profile_post(request: Request):
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="profile body must be JSON object")
    room_value = body.get("room") or body.get("defaultRoom") or body.get("phasmoRoom") or ""
    if not str(room_value).strip():
        raise HTTPException(status_code=400, detail="room is required")
    ensure_valid_room_name(str(room_value))
    profile = set_default_room(
        str(room_value),
        channel=str(body.get("channel") or body.get("streamer") or body.get("broadcaster") or ""),
        bot_account=str(body.get("botAccount") or body.get("bot") or body.get("botUser") or ""),
        user=str(body.get("user") or body.get("username") or body.get("displayName") or ""),
    )
    return {"ok": True, "profile": profile, "defaultRoom": profile.get("defaultRoom")}
