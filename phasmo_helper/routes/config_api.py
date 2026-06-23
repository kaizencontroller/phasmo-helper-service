from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query, Request
from ..core.config import CONFIG_DESCRIPTIONS, _read_config, _write_config
from ..services.state import _auth_ok

router = APIRouter()

@router.get("/api/phasmo/config")
def api_get_config():
    return {"ok": True, "config": _read_config(), "descriptions": CONFIG_DESCRIPTIONS}


@router.post("/api/phasmo/config")
async def api_post_config(
    request: Request,
    token: str | None = Query(default=None),
    x_phasmo_token: str | None = Header(default=None),
):
    if not _auth_ok(x_phasmo_token, token):
        raise HTTPException(status_code=401, detail="unauthorized")
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="config body must be an object")
    return {"ok": True, "config": _write_config(body)}
