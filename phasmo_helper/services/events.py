from __future__ import annotations

import logging
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable

log = logging.getLogger(__name__)
EventHandler = Callable[["AppEvent"], None]


@dataclass(frozen=True)
class AppEvent:
    name: str
    room: str
    at: int
    actor: str = ""
    source: str = "app"
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Small synchronous plugin boundary; subscribers must remain fast and isolated."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}
        self._lock = RLock()

    def subscribe(self, event_name: str, handler: EventHandler) -> Callable[[], None]:
        with self._lock:
            self._handlers.setdefault(event_name, []).append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers.get(event_name, []):
                    self._handlers[event_name].remove(handler)
        return unsubscribe

    def publish(self, event: AppEvent) -> int:
        with self._lock:
            handlers = [*self._handlers.get(event.name, []), *self._handlers.get("*", [])]
        delivered = 0
        for handler in handlers:
            try:
                handler(event)
                delivered += 1
            except Exception:
                log.exception("Phasmo event subscriber failed: %s", event.name)
        return delivered

    def subscriptions(self) -> dict[str, int]:
        with self._lock:
            return {name: len(handlers) for name, handlers in self._handlers.items()}


event_bus = EventBus()


EVENT_NAMES = {
    "room_created": "RoomCreated",
    "evidence_changed": "EvidenceAdded",
    "ghost_eliminated": "GhostEliminated",
    "contract_result": "RoundCompleted",
    "session_end": "SessionEnded",
    "streamerbot_command": "ViewerGuessSubmitted",
}
