from __future__ import annotations

import re
import time
from typing import Dict
from .data import GHOST_ALIASES

def _slug_words(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")


def _match_setup_value(raw: str, aliases: Dict[str, str]) -> str | None:
    value = " ".join((raw or "").strip().split())
    if not value:
        return None
    key = _slug_words(value)
    if key in aliases:
        return aliases[key]
    key_compact = key.replace("-", "")
    for alias, target in aliases.items():
        if alias.replace("-", "") == key_compact:
            return target
    # Allow partial map names like "tangle" or "brown".
    matches = [target for alias, target in aliases.items() if key and (key in alias or key in _slug_words(target))]
    matches = list(dict.fromkeys(matches))
    if len(matches) == 1:
        return matches[0]
    return None

def _normalize_value(raw: str | None, kind: str) -> str:
    value = (raw or "").strip().lower()
    if kind == "evidence":
        if value in {"yes", "y", "true", "found", "confirm", "confirmed", "observed"}:
            return "yes"
        if value in {"no", "n", "false", "ruleout", "ruledout", "absent", "none"}:
            return "no"
        return "unknown"
    if kind == "behavior":
        if value in {"yes", "y", "true", "observed", "obs", "seen"}:
            return "observed"
        if value in {"no", "n", "false", "contradicted", "not"}:
            return "contradicted"
        return "unknown"
    return "unknown"


def _normal_user(raw: str | None) -> str:
    return (raw or "anonymous").strip().lstrip("@").lower() or "anonymous"


def _normal_ghost(raw: str | None) -> str | None:
    key = re.sub(r"[^a-z0-9]", "", (raw or "").lower())
    return GHOST_ALIASES.get(key)

def _now_ms() -> int:
    return int(time.time() * 1000)
