from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import settings
from .chat import ChatIdentity


DEFAULT_ROLES = ["owner", "broadcaster", "moderator", "vip", "subscriber", "follower", "viewer", "guest"]
DEFAULT_MATRIX = {
    "evidence.edit": ["viewer"], "ghost.guess": ["viewer"], "behavior.log": ["moderator"],
    "room.create": ["moderator"], "room.close": ["moderator"], "room.reset": ["moderator"],
    "leaderboard.reset": ["broadcaster"], "developer.tools": ["owner"], "maintenance": ["owner"],
    "overlay": ["viewer"], "configuration": ["broadcaster"], "content.reload": ["owner"],
}


def _path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / "__global_permissions.json"


def default_permissions() -> dict[str, Any]:
    return {"schemaVersion": 1, "roles": DEFAULT_ROLES, "groups": {}, "users": {}, "matrix": DEFAULT_MATRIX}


def read_permissions() -> dict[str, Any]:
    data = default_permissions()
    try:
        loaded = json.loads(_path().read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            for key in ("roles", "groups", "users", "matrix"):
                if key in loaded:
                    data[key] = loaded[key]
    except Exception:
        pass
    return data


def write_permissions(payload: dict[str, Any]) -> dict[str, Any]:
    data = read_permissions()
    for key in ("roles", "groups", "users", "matrix"):
        if key in payload:
            data[key] = payload[key]
    _path().write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data


@dataclass
class PermissionDecision:
    allowed: bool
    reason: str
    matched_by: str = ""


class PermissionEngine:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or read_permissions()

    def check(self, action: str, identity: ChatIdentity, now_ms: int | None = None) -> PermissionDecision:
        rule = self.config.get("matrix", {}).get(action, [])
        if rule == "disabled" or rule is False:
            return PermissionDecision(False, "action is disabled")
        if rule == "everyone" or rule is True:
            return PermissionDecision(True, "allowed for everyone", "everyone")
        allowed = {str(value).lower() for value in (rule if isinstance(rule, list) else [rule])}
        user_rule = self.config.get("users", {}).get(identity.user_id, {})
        now_ms = now_ms or int(time.time() * 1000)
        expires = int(user_rule.get("expiresAt") or 0) if isinstance(user_rule, dict) else 0
        if isinstance(user_rule, dict) and (not expires or expires > now_ms):
            explicit = set(user_rule.get("allow", []))
            if action in explicit or "*" in explicit:
                return PermissionDecision(True, "explicit user permission", "user")
            if action in set(user_rule.get("deny", [])):
                return PermissionDecision(False, "explicit user denial", "user")
        if identity.roles & allowed:
            return PermissionDecision(True, "role permission", "role")
        for group_name, group in self.config.get("groups", {}).items():
            if identity.user_id in set(group.get("users", [])) and (action in set(group.get("permissions", [])) or group_name.lower() in allowed):
                expires_at = int(group.get("expiresAt") or 0)
                if not expires_at or expires_at > now_ms:
                    return PermissionDecision(True, "custom group permission", f"group:{group_name}")
        return PermissionDecision(False, f"requires one of: {', '.join(sorted(allowed)) or 'no permitted roles'}")
