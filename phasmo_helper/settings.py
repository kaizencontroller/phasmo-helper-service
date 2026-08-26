from __future__ import annotations

import os
import threading
from pathlib import Path

_STATE_LOCK = threading.Lock()
_DEFAULT_STATE_DIR = (
    "/tmp/phasmo_state"
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID")
    else str(Path(__file__).resolve().parents[1] / ".kaizen-data")
)
_STATE_DIR = Path(os.getenv("PHASMO_STATE_DIR", _DEFAULT_STATE_DIR))
_PLATFORM_BASE_URL = os.getenv("KAIZEN_PLATFORM_URL", "").strip().rstrip("/")
_ADMIN_TOKEN = os.getenv("PHASMO_ADMIN_TOKEN", "").strip()
_ALLOW_BEHAVIOR_COMMANDS = os.getenv("PHASMO_ALLOW_BEHAVIOR_COMMANDS", "true").strip().lower() in {"1", "true", "yes", "on"}
_JUMPSCARE_FILE = Path(os.getenv("PHASMO_JUMPSCARE_FILE", "jumpscare.mp4"))
_JUMPSCARE_URL = os.getenv("PHASMO_JUMPSCARE_URL", "").strip()

_JUMPSCARE_COUNTER_FILE = "__global_jumpscare_counter.json"
_CONFIG_FILE = "__global_config.json"
_ROOM_TTL_SECONDS = int(os.getenv("PHASMO_ROOM_TTL_SECONDS", str(4 * 60 * 60)))
_CLOSED_ROOM_RETENTION_SECONDS = int(os.getenv("PHASMO_CLOSED_ROOM_RETENTION_SECONDS", str(7 * 24 * 60 * 60)))
_BUG_REPORT_FILE = "__global_bug_reports.jsonl"
_FEEDBACK_FILE = "__global_feedback.jsonl"
_LEADERBOARD_FILE = "__global_leaderboard.json"
_MAX_LEADERBOARD_HISTORY = int(os.getenv("PHASMO_MAX_LEADERBOARD_HISTORY", "500"))
_SUPPORT_PINGS_FILE = "__global_support_pings.jsonl"
_SUPPORT_WEBHOOK_URL = os.getenv("PHASMO_SUPPORT_WEBHOOK_URL", "").strip()
_SUPPORT_PING_COOLDOWN_SECONDS = int(os.getenv("PHASMO_SUPPORT_PING_COOLDOWN_SECONDS", "1800"))

_QUICKSTART_VIDEO_URL = os.getenv("PHASMO_QUICKSTART_VIDEO_URL", "").strip()
_STREAMERBOT_PROFILES_FILE = "__global_streamerbot_profiles.json"


# Unlisted local/prelaunch admin panel. Local defaults to 1234; Railway requires an explicit code.
_IS_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID") or os.getenv("RAILWAY_SERVICE_ID"))
_DEV_ADMIN_CODE = os.getenv("PHASMO_DEV_ADMIN_CODE", "").strip()
if not _IS_RAILWAY and not _DEV_ADMIN_CODE:
    _DEV_ADMIN_CODE = "1234"
_DEV_ADMIN_ENABLED = bool(_DEV_ADMIN_CODE) and (not _IS_RAILWAY or bool(os.getenv("PHASMO_DEV_ADMIN_CODE", "").strip()))

# Public safety / cost controls
_ABUSE_MODE = os.getenv("PHASMO_ABUSE_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
_DEGRADED_MODE = os.getenv("PHASMO_DEGRADED_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
_MAX_REQUEST_BYTES = int(os.getenv("PHASMO_MAX_REQUEST_BYTES", "10000"))
_RATE_LIMIT_FILE = "__global_rate_limit_events.jsonl"
_SITE_BANNER_FILE = "__global_site_banner.json"
_ROOM_NAME_BLOCKLIST_EXTRA = os.getenv("PHASMO_ROOM_NAME_BLOCKLIST_EXTRA", "")

# Release / maintenance automation. The packaged release is the source of
# truth; keep the configured value visible for diagnosing stale deployment variables.
_APP_VERSION = "v5.8.2"
_CONFIGURED_APP_VERSION = os.getenv("PHASMO_APP_VERSION", "").strip()
_PLATFORM_VERSION = os.getenv("KAIZEN_PLATFORM_VERSION", "contract-1.0").strip() or "contract-1.0"
_BUILD_COMMIT = os.getenv("PHASMO_BUILD_COMMIT", os.getenv("RAILWAY_GIT_COMMIT_SHA", "")).strip()
_OPS_TOKEN = os.getenv("PHASMO_OPS_TOKEN", "").strip()
_MAINTENANCE_FILE = "__global_maintenance.json"
_MAINTENANCE_DEFAULT_WARNING_HOURS = int(os.getenv("PHASMO_MAINTENANCE_WARNING_HOURS", "24"))


def platform_support_url(*, source_url: str = "") -> str:
    """Return the shared Platform support form, or the legacy local form."""
    from urllib.parse import urlencode

    if not _PLATFORM_BASE_URL:
        return "/phasmo/bug-report"
    query = urlencode(
        {
            "application_id": "phasmo-helper",
            "application_name": "Phasmo Helper",
            "application_version": _APP_VERSION,
            "source_url": source_url,
            "theme": "phasmo",
        }
    )
    return f"{_PLATFORM_BASE_URL}/support/report?{query}"
