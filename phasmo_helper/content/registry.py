from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONTENT_DIR = Path(__file__).resolve().parent
REQUIRED_FILES = (
    "ghosts.json", "maps.json", "objectives.json", "behavior_clues.json",
    "cursed_items.json", "evidence.json", "commands.json", "game_version.json",
)


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    code: str
    message: str
    file: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"level": self.level, "code": self.code, "message": self.message, "file": self.file}


@dataclass
class ContentRegistry:
    documents: dict[str, dict[str, Any]] = field(default_factory=dict)
    rooms: dict[str, dict[str, Any]] = field(default_factory=dict)
    issues: list[ValidationIssue] = field(default_factory=list)

    @classmethod
    def load(cls, base_dir: Path = CONTENT_DIR) -> "ContentRegistry":
        registry = cls()
        for filename in REQUIRED_FILES:
            path = base_dir / filename
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("root must be an object")
                registry.documents[filename] = payload
            except Exception as exc:
                registry.issues.append(ValidationIssue("error", "invalid_json", str(exc), filename))
        rooms_dir = base_dir / "rooms"
        for path in sorted(rooms_dir.glob("*.json")) if rooms_dir.exists() else []:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                registry.rooms[path.name] = payload
            except Exception as exc:
                registry.issues.append(ValidationIssue("error", "invalid_json", str(exc), f"rooms/{path.name}"))
        registry._validate()
        return registry

    def items(self, filename: str) -> list[dict[str, Any]]:
        values = self.documents.get(filename, {}).get("items", [])
        return values if isinstance(values, list) else []

    @property
    def ghosts(self) -> list[dict[str, Any]]:
        return self.items("ghosts.json")

    @property
    def game_version(self) -> dict[str, Any]:
        return self.documents.get("game_version.json", {})

    @property
    def valid(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)

    def report(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": sum(i.level == "error" for i in self.issues),
            "warnings": sum(i.level == "warning" for i in self.issues),
            "issues": [i.as_dict() for i in self.issues],
            "counts": {
                "ghosts": len(self.ghosts), "maps": len(self.items("maps.json")),
                "evidence": len(self.items("evidence.json")), "objectives": len(self.items("objectives.json")),
                "commands": len(self.items("commands.json")), "rooms": sum(len(v.get("items", [])) for v in self.rooms.values()),
            },
            "contentVersion": self.game_version.get("contentVersion"),
            "gameVersion": self.game_version.get("supportedVersion"),
        }

    def public_payload(self) -> dict[str, Any]:
        return {
            "ghosts": self.ghosts,
            "maps": self.items("maps.json"),
            "evidence": self.items("evidence.json"),
            "objectives": self.items("objectives.json"),
            "behaviorClues": self.items("behavior_clues.json"),
            "cursedItems": self.items("cursed_items.json"),
            "commands": self.items("commands.json"),
            "rooms": self.rooms,
            "gameVersion": self.game_version,
        }

    def _unique_ids(self, filename: str, code: str) -> set[str]:
        seen: set[str] = set()
        for index, item in enumerate(self.items(filename)):
            item_id = str(item.get("id") or item.get("name") or "").strip()
            if not item_id:
                self.issues.append(ValidationIssue("error", "missing_id", f"Item {index + 1} has no id/name", filename))
            elif item_id in seen:
                self.issues.append(ValidationIssue("error", code, f"Duplicate id: {item_id}", filename))
            seen.add(item_id)
        return seen

    def _validate(self) -> None:
        evidence_ids = self._unique_ids("evidence.json", "duplicate_evidence_id")
        ghost_ids = self._unique_ids("ghosts.json", "duplicate_ghost_id")
        map_ids = self._unique_ids("maps.json", "duplicate_map_id")
        self._unique_ids("objectives.json", "duplicate_objective_id")
        clue_ids = self._unique_ids("behavior_clues.json", "duplicate_behavior_id")
        command_names: set[str] = set()
        aliases: set[str] = set()
        for command in self.items("commands.json"):
            name = str(command.get("name", "")).lower()
            if not name or name in command_names:
                self.issues.append(ValidationIssue("error", "invalid_command", f"Duplicate or blank command: {name or '<blank>'}", "commands.json"))
            command_names.add(name)
            for alias in command.get("aliases", []):
                alias = str(alias).lower()
                if alias in aliases or alias in command_names:
                    self.issues.append(ValidationIssue("error", "duplicate_command_alias", f"Duplicate command alias: {alias}", "commands.json"))
                aliases.add(alias)
            if not command.get("permission"):
                self.issues.append(ValidationIssue("error", "permission_error", f"Command {name} has no permission", "commands.json"))
        for ghost in self.ghosts:
            for evidence in ghost.get("evidence", []) + ghost.get("extraEvidence", []):
                if evidence not in evidence_ids:
                    self.issues.append(ValidationIssue("error", "invalid_evidence", f"Ghost {ghost.get('id')} references {evidence}", "ghosts.json"))
            for field_name in ("name", "lore", "hiddenAbility", "huntThreshold", "movementSpeed", "strengths", "weaknesses", "tips", "misconceptions"):
                if not ghost.get(field_name):
                    self.issues.append(ValidationIssue("warning", "missing_localization", f"Ghost {ghost.get('id')} is missing {field_name}", "ghosts.json"))
        for clue in self.items("behavior_clues.json"):
            for ghost_id in clue.get("supports", []) + clue.get("rulesOut", []):
                if ghost_id not in ghost_ids:
                    self.issues.append(ValidationIssue("error", "broken_reference", f"Behavior {clue.get('id')} references {ghost_id}", "behavior_clues.json"))
        room_ids: set[str] = set()
        for filename, document in self.rooms.items():
            if document.get("mapId") not in map_ids:
                self.issues.append(ValidationIssue("error", "broken_reference", f"Unknown mapId {document.get('mapId')}", f"rooms/{filename}"))
            for room in document.get("items", []):
                room_id = str(room.get("id", ""))
                if room_id in room_ids:
                    self.issues.append(ValidationIssue("error", "duplicate_room_id", f"Duplicate room id: {room_id}", f"rooms/{filename}"))
                room_ids.add(room_id)
        for map_item in self.items("maps.json"):
            rooms_file = map_item.get("roomsFile")
            if rooms_file and Path(str(rooms_file)).name not in self.rooms:
                self.issues.append(ValidationIssue("error", "broken_reference", f"Missing {rooms_file}", "maps.json"))


_LOCK = threading.Lock()
_REGISTRY: ContentRegistry | None = None


def get_registry() -> ContentRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        with _LOCK:
            if _REGISTRY is None:
                _REGISTRY = ContentRegistry.load()
    return _REGISTRY


def reload_registry() -> ContentRegistry:
    global _REGISTRY
    with _LOCK:
        candidate = ContentRegistry.load()
        if candidate.valid:
            _REGISTRY = candidate
        return candidate
