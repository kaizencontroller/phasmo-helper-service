from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ChatIdentity:
    user_id: str
    display_name: str
    provider: str = "unknown"
    roles: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    text: str
    identity: ChatIdentity
    channel: str = ""
    message_id: str = ""


class IChatProvider(Protocol):
    """Adapter boundary for Streamer.bot, EventSub, Discord, Kick, and YouTube."""

    name: str

    def parse(self, payload: dict[str, Any]) -> ChatMessage: ...


class StreamerBotProvider:
    name = "streamerbot-twitch"

    @staticmethod
    def _truthy(value: Any) -> bool:
        return value is True or str(value or "").lower() in {"1", "true", "yes", "on"}

    def parse(self, payload: dict[str, Any]) -> ChatMessage:
        user = str(payload.get("user") or payload.get("username") or payload.get("displayName") or "anonymous").strip()
        roles = {str(role).lower() for role in payload.get("roles", []) if str(role).strip()}
        checks = {
            "owner": payload.get("isOwner"), "broadcaster": payload.get("isBroadcaster"),
            "moderator": payload.get("isMod"), "vip": payload.get("isVip"),
            "subscriber": payload.get("isSubscriber"), "follower": payload.get("isFollower"),
        }
        roles.update(role for role, enabled in checks.items() if self._truthy(enabled))
        roles.add("viewer")
        return ChatMessage(
            text=str(payload.get("command") or payload.get("rawInput") or payload.get("message") or "").strip(),
            identity=ChatIdentity(user.lower().lstrip("@"), user, self.name, roles, payload),
            channel=str(payload.get("channel") or payload.get("streamer") or ""),
            message_id=str(payload.get("messageId") or ""),
        )
