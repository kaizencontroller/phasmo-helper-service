from __future__ import annotations

import json
import re
import time
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Tuple

from fastapi import HTTPException, Request
from .. import settings

# Keep this list intentionally conservative and editable by env for production.
# Patterns are checked against a lowercased, punctuation-stripped room name.
_BLOCKED_ROOM_PATTERNS = [
    r"n[i1!]+g+", r"f[a@]g+", r"k[i1]ke", r"ch[i1]nk", r"sp[i1]c", r"tr[a@]nny",
    r"r[e3]t[a@]rd", r"n[a@]z[i1]", r"h[i1]tl[e3]r", r"kkk", r"wh[i1]t[e3]p[o0]w[e3]r",
    r"r[a@]p[e3]", r"porn", r"sex", r"suicide", r"k[i1]ll[-_ ]?yourself", r"doxx?",
]

RESERVED_ROOM_NAMES = {"admin", "administrator", "root", "support", "kaizencontroller", "kaizen-controller", "moderator", "mod", "api", "phasmo", "status", "null", "undefined"}

_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
_failed_passcodes: dict[str, deque[float]] = defaultdict(deque)


def _norm_text(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (raw or "").lower())


def validate_room_name(raw: str | None) -> Tuple[bool, str]:
    name = (raw or "").strip()
    if not name:
        return False, "Room name is required."
    if len(name) < 3 or len(name) > 32:
        return False, "Room names must be 3–32 characters."
    if re.search(r"https?://|www\.", name, re.I):
        return False, "Room names cannot contain links."
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]*", name):
        return False, "Room names may only use letters, numbers, spaces, hyphens, or underscores."
    if re.search(r"(.)\1{5,}", name):
        return False, "Room name has too many repeated characters."
    slug = re.sub(r"[^a-z0-9_-]", "-", name.lower()).strip("-")
    if slug in RESERVED_ROOM_NAMES:
        return False, "That room name is reserved. Please choose another."
    compact = _norm_text(name)
    patterns = list(_BLOCKED_ROOM_PATTERNS)
    extra = [p.strip() for p in settings._ROOM_NAME_BLOCKLIST_EXTRA.split(",") if p.strip()]
    patterns.extend(extra)
    for pat in patterns:
        try:
            if re.search(pat, compact, re.I):
                return False, "Please choose a different stream-safe room name."
        except re.error:
            continue
    return True, ""


def ensure_valid_room_name(raw: str | None) -> None:
    ok, msg = validate_room_name(raw)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)


def _client_ip(request: Request) -> str:
    # Trust Cloudflare/proxy headers only as a best-effort identifier. Cloudflare should do primary edge protection.
    hdr = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for") or ""
    if hdr:
        return hdr.split(",")[0].strip()[:80]
    return request.client.host if request.client else "unknown"


def check_rate_limit(key: str, limit: int, seconds: int) -> None:
    now = time.time()
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        retry_after = max(1, math.ceil(seconds - (now - bucket[0]))) if bucket else seconds
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down and try again shortly.", headers={"Retry-After": str(retry_after)})
    bucket.append(now)


def apply_route_rate_limit(request: Request) -> None:
    ip = _client_ip(request)
    path = request.url.path
    method = request.method.upper()
    if settings._ABUSE_MODE:
        if method == "POST" and (path.endswith("/bug-report") or path.endswith("/feedback")):
            raise HTTPException(status_code=503, detail="Phasmo Helper is in temporary abuse-protection mode. Nonessential submissions are paused.")
    if path.endswith("/api/phasmo/state") and method == "GET":
        # Control + OBS overlay are commonly open together. Their normal polling
        # must fit comfortably without weakening write/command limits.
        limit, window = (30, 60) if settings._ABUSE_MODE else ((60, 60) if settings._DEGRADED_MODE else (120, 60))
        room = request.query_params.get("room") or "default"
        check_rate_limit(f"state-get:{ip}:{room}", limit, window)
    elif path.endswith("/api/phasmo/state") and method == "POST":
        room = request.query_params.get("room") or "default"
        check_rate_limit(f"state-post:{ip}:{room}", 25, 60)
    elif path.endswith("/api/phasmo/command"):
        check_rate_limit(f"command:{ip}", 80, 60)
    elif path.endswith("/api/phasmo/bug-report"):
        check_rate_limit(f"bug:{ip}", 3, 3600)
    elif path.endswith("/api/phasmo/feedback"):
        check_rate_limit(f"feedback:{ip}", 10, 3600)
    elif "/api/phasmo/dev-admin" in path:
        check_rate_limit(f"dev-admin:{ip}", 30, 3600)
    else:
        check_rate_limit(f"general:{ip}", 180, 60)


def record_failed_passcode(request: Request, room: str) -> None:
    ip = _client_ip(request)
    key = f"passcode:{ip}:{room}"
    now = time.time()
    bucket = _failed_passcodes[key]
    while bucket and now - bucket[0] > 600:
        bucket.popleft()
    bucket.append(now)
    if len(bucket) >= 5:
        raise HTTPException(status_code=429, detail="Too many failed passcode attempts. Try again later.")


def passcode_attempt_allowed(request: Request, room: str) -> None:
    ip = _client_ip(request)
    key = f"passcode:{ip}:{room}"
    now = time.time()
    bucket = _failed_passcodes[key]
    while bucket and now - bucket[0] > 600:
        bucket.popleft()
    if len(bucket) >= 5:
        raise HTTPException(status_code=429, detail="Too many failed passcode attempts. Try again later.")


def write_rate_event(payload: Dict[str, Any]) -> None:
    try:
        settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
        path = settings._STATE_DIR / settings._RATE_LIMIT_FILE
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
