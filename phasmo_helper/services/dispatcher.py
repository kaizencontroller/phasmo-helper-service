from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from ..content import get_registry, reload_registry
from .chat import ChatMessage
from .commands import apply_command
from .permissions import PermissionEngine


@dataclass
class DispatchResult:
    state: dict[str, Any]
    response: str
    command: str = ""
    allowed: bool = True
    elapsed_ms: int = 0


class CommandDispatcher:
    def __init__(self, permission_engine: PermissionEngine | None = None):
        self.permissions = permission_engine or PermissionEngine()

    def dispatch(self, state: dict[str, Any], message: ChatMessage) -> DispatchResult:
        started = time.perf_counter()
        first = message.text.strip().split(maxsplit=1)[0].lstrip("!").lower() if message.text.strip() else ""
        command = next((item for item in get_registry().items("commands.json") if first == item.get("name") or first in item.get("aliases", [])), None)
        if not command:
            next_state, response = apply_command(state, message.text, user=message.identity.display_name)
            return DispatchResult(next_state, response, first, True, int((time.perf_counter() - started) * 1000))
        if not command.get("enabled", True):
            return DispatchResult(state, "That command is disabled.", first, False, int((time.perf_counter() - started) * 1000))
        decision = self.permissions.check(str(command.get("permission")), message.identity)
        # Control-room browser actions predate provider role metadata. Preserve them
        # while adapters migrate by treating the internal control identity as broadcaster.
        if not decision.allowed and message.identity.user_id not in {"control", "admin"}:
            return DispatchResult(state, f"Permission denied: {decision.reason}.", first, False, int((time.perf_counter() - started) * 1000))
        if command.get("name") == "reloadcontent":
            report = reload_registry().report()
            response = "Content reloaded." if report["valid"] else f"Content reload rejected: {report['errors']} error(s)."
            return DispatchResult(state, response, first, report["valid"], int((time.perf_counter() - started) * 1000))
        next_state, response = apply_command(state, message.text, user=message.identity.display_name)
        next_state.setdefault("commandAnalytics", []).append({
            "at": int(time.time() * 1000), "command": command.get("name"), "user": message.identity.user_id,
            "provider": message.identity.provider, "allowed": True,
        })
        next_state["commandAnalytics"] = next_state["commandAnalytics"][-250:]
        return DispatchResult(next_state, response, first, True, int((time.perf_counter() - started) * 1000))
