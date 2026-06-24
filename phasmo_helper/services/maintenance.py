from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import Header, HTTPException, Request
from .. import settings
from .banner import write_banner


def _maintenance_path() -> Path:
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return settings._STATE_DIR / settings._MAINTENANCE_FILE


def _now_ms() -> int:
    return int(time.time() * 1000)


def default_maintenance() -> Dict[str, Any]:
    return {
        "enabled": False,
        "status": "operational",  # operational / maintenance_scheduled / maintenance_active / deploying / deployment_failed
        "mode": "normal",          # normal / banner / read_only / block_new_rooms / full
        "message": "",
        "expectedImpact": "",
        "maintenanceId": "",
        "stagedVersion": "",
        "productionVersion": settings._APP_VERSION,
        "deploymentId": "",
        "readOnly": False,
        "blockNewRooms": False,
        "startedAt": 0,
        "scheduledStart": 0,
        "scheduledEnd": 0,
        "completedAt": 0,
        "lastResult": "",
        "lastError": "",
        "updatedAt": 0,
        "updatedBy": "",
    }


def read_maintenance() -> Dict[str, Any]:
    data = default_maintenance()
    try:
        loaded = json.loads(_maintenance_path().read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data.update(loaded)
    except Exception:
        pass
    data["productionVersion"] = settings._APP_VERSION
    for key in ["message", "expectedImpact", "maintenanceId", "stagedVersion", "deploymentId", "lastResult", "lastError", "updatedBy", "status", "mode"]:
        data[key] = str(data.get(key) or "")[:1000]
    data["enabled"] = bool(data.get("enabled"))
    data["readOnly"] = bool(data.get("readOnly"))
    data["blockNewRooms"] = bool(data.get("blockNewRooms"))
    for key in ["startedAt", "scheduledStart", "scheduledEnd", "completedAt", "updatedAt"]:
        try:
            data[key] = max(0, int(float(data.get(key) or 0)))
        except Exception:
            data[key] = 0
    if data.get("status") not in {"operational", "maintenance_scheduled", "maintenance_active", "deploying", "degraded", "outage", "deployment_failed"}:
        data["status"] = "maintenance_active" if data.get("enabled") else "operational"
    if data.get("mode") not in {"normal", "banner", "read_only", "block_new_rooms", "full"}:
        data["mode"] = "normal"
    return data


def write_maintenance(patch: Dict[str, Any]) -> Dict[str, Any]:
    data = read_maintenance()
    allowed = set(default_maintenance().keys())
    for key, value in (patch or {}).items():
        if key in allowed:
            data[key] = value
    data["updatedAt"] = _now_ms()
    _maintenance_path().write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return read_maintenance()


def _parse_ms(value: Any) -> int:
    if value in {None, ""}:
        return 0
    try:
        # Accept milliseconds, seconds, or numeric strings. ISO parsing is intentionally
        # left to GitHub/status tooling for now so local UI stays simple.
        num = float(value)
        if num < 10_000_000_000:
            num *= 1000
        return max(0, int(num))
    except Exception:
        return 0


def start_maintenance(payload: Dict[str, Any] | None = None, updated_by: str = "ops") -> Dict[str, Any]:
    payload = payload or {}
    status = str(payload.get("status") or "maintenance_active")
    mode = str(payload.get("mode") or "read_only")
    read_only = bool(payload.get("readOnly", mode in {"read_only", "full"}))
    block_new = bool(payload.get("blockNewRooms", mode in {"block_new_rooms", "full", "read_only"}))
    message = str(payload.get("message") or "Scheduled Phasmo Helper maintenance is active. The app may briefly refresh or become read-only.")[:500]
    expected = str(payload.get("expectedImpact") or "Brief downtime or read-only behavior may occur while the Railway service refreshes.")[:500]
    data = write_maintenance({
        "enabled": True,
        "status": status if status in {"maintenance_active", "deploying", "maintenance_scheduled"} else "maintenance_active",
        "mode": mode if mode in {"banner", "read_only", "block_new_rooms", "full"} else "read_only",
        "message": message,
        "expectedImpact": expected,
        "maintenanceId": str(payload.get("maintenanceId") or f"phasmo-maint-{_now_ms()}")[:160],
        "stagedVersion": str(payload.get("stagedVersion") or "")[:80],
        "deploymentId": str(payload.get("deploymentId") or "")[:160],
        "readOnly": read_only,
        "blockNewRooms": block_new,
        "startedAt": _now_ms(),
        "scheduledStart": _parse_ms(payload.get("scheduledStart")),
        "scheduledEnd": _parse_ms(payload.get("scheduledEnd")),
        "completedAt": 0,
        "lastResult": "maintenance started",
        "lastError": "",
        "updatedBy": updated_by[:120],
    })
    write_banner({"enabled": True, "level": "maintenance", "message": message})
    return data


def end_maintenance(payload: Dict[str, Any] | None = None, updated_by: str = "ops") -> Dict[str, Any]:
    payload = payload or {}
    success = bool(payload.get("success", True))
    result = str(payload.get("result") or ("deployment complete" if success else "deployment failed"))[:500]
    status = "operational" if success else "deployment_failed"
    msg = str(payload.get("message") or ("Phasmo Helper maintenance is complete." if success else "Phasmo Helper deployment did not complete successfully. Manual review may be needed."))[:500]
    data = write_maintenance({
        "enabled": False,
        "status": status,
        "mode": "normal",
        "message": msg,
        "readOnly": False,
        "blockNewRooms": False,
        "completedAt": _now_ms(),
        "lastResult": result,
        "lastError": str(payload.get("error") or "")[:500],
        "updatedBy": updated_by[:120],
    })
    # On success, clear the banner. On failure, leave a warning banner visible.
    if success:
        write_banner({"enabled": False, "message": ""})
    else:
        write_banner({"enabled": True, "level": "warning", "message": msg})
    return data


def maintenance_write_blocked(existing_room: bool) -> str:
    data = read_maintenance()
    if not data.get("enabled"):
        return ""
    if data.get("readOnly"):
        return "Phasmo Helper is temporarily read-only for scheduled maintenance. Please try again after the update window."
    if data.get("blockNewRooms") and not existing_room:
        return "New room creation is paused for scheduled maintenance. Existing rooms may continue after the window."
    return ""


def require_ops_token(authorization: str | None = Header(default=None), x_phasmo_ops_token: str | None = Header(default=None)) -> None:
    expected = settings._OPS_TOKEN
    if not expected:
        raise HTTPException(status_code=404, detail="ops automation disabled; set PHASMO_OPS_TOKEN")
    supplied = ""
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization.split(" ", 1)[1].strip()
    supplied = supplied or (x_phasmo_ops_token or "").strip()
    if supplied != expected:
        raise HTTPException(status_code=403, detail="invalid ops token")


def state_dir_health() -> Dict[str, Any]:
    out = {"path": str(settings._STATE_DIR), "exists": False, "writable": False, "error": ""}
    try:
        settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
        out["exists"] = settings._STATE_DIR.exists()
        test = settings._STATE_DIR / "__healthcheck.tmp"
        test.write_text(str(_now_ms()), encoding="utf-8")
        out["writable"] = True
        try:
            test.unlink()
        except Exception:
            pass
    except Exception as exc:
        out["error"] = str(exc)[:300]
    return out
