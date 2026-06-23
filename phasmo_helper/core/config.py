from __future__ import annotations

import json
from typing import Any, Dict
from .. import settings

CONFIG_DESCRIPTIONS = {
    "allowSetupCommands": ("Setup/map commands", "Allows chat/API commands such as !map, !difficulty, !weather, !players, and !setup."),
    "allowEvidenceCommands": ("Evidence commands", "Allows chat/API commands that update evidence, response condition, and evidence mode."),
    "allowBehaviorCommands": ("Behavior commands", "Allows chat/API commands such as !behavior, !be, !observed, and behavior aliases."),
    "allowTimerCommands": ("Timer commands", "Allows chat/API commands for incense, hunt, cooldown, and timer clearing."),
    "allowSanityCommands": ("Sanity and hunt-threshold commands", "Allows !sanity, !huntat, and !huntnow."),
    "allowWitnessedCommands": ("Witnessed model/name clue commands", "Allows !gender, !model, !manifest, !female, !male, and related commands."),
    "allowViewerVoteCommands": ("Viewer guess/vote commands", "Allows !guess, !vote, !unguess, !unvote, !guesses, and !votes."),
    "allowManualGhostCommands": ("Manual ghost override commands", "Allows !ghost, !select, !notghost, !restoreghost, and !clearghost."),
    "allowIgnoreCommands": ("Ignore-list commands", "Allows mod/control commands such as !ignore, !unignore, !ignored, and !ignorelist."),
    "allowNextRoundCommand": ("Next Round command", "Allows !nextround to start a new round while preserving reusable setup."),
    "allowPanicCommand": ("Panic command", "Allows the harmless !panic command."),
    "allowEasterEggs": ("Easter eggs", "Allows optional joke/easter-egg behavior such as classified notes and joke awards."),
    "allowJumpscareButton": ("Don't press this button", "Shows/enables the setup-page jumpscare button and overlay jumpscare trigger."),
}


CONFIG_DEFAULTS = {
    "allowSetupCommands": True,
    "allowEvidenceCommands": True,
    "allowBehaviorCommands": settings._ALLOW_BEHAVIOR_COMMANDS,
    "allowTimerCommands": True,
    "allowSanityCommands": True,
    "allowWitnessedCommands": True,
    "allowViewerVoteCommands": True,
    "allowManualGhostCommands": True,
    "allowIgnoreCommands": True,
    "allowNextRoundCommand": True,
    "allowPanicCommand": True,
    "allowEasterEggs": True,
    "allowJumpscareButton": True,
}


def _config_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._CONFIG_FILE


def _read_config() -> Dict[str, bool]:
    config = dict(CONFIG_DEFAULTS)
    try:
        data = json.loads(_config_path().read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key in CONFIG_DEFAULTS:
                if key in data:
                    config[key] = bool(data[key])
    except Exception:
        pass
    return config


def _write_config(patch: Dict[str, Any]) -> Dict[str, bool]:
    current = _read_config()
    for key in CONFIG_DEFAULTS:
        if key in patch:
            current[key] = bool(patch[key])
    _config_path().write_text(json.dumps(current, indent=2, sort_keys=True), encoding="utf-8")
    return current


def _config_bool(key: str) -> bool:
    return bool(_read_config().get(key, CONFIG_DEFAULTS.get(key, True)))
