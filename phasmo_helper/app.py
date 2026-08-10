from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from .routes import api, config_api, pages, dev_admin
from . import settings
from .services.security import apply_route_rate_limit
from .content import get_registry

app = FastAPI(title="Kaizen Phasmophobia Helper")

@app.middleware("http")
async def phasmo_safety_middleware(request: Request, call_next):
    # Lightweight application-layer protection. Cloudflare/Railway should still be used
    # for edge/network protection, but this prevents obvious abuse from reaching expensive paths.
    cl = request.headers.get("content-length")
    try:
        if cl and int(cl) > settings._MAX_REQUEST_BYTES:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Request body too large."}, status_code=413)
    except Exception:
        pass
    try:
        apply_route_rate_limit(request)
    except Exception as exc:
        from fastapi import HTTPException
        from fastapi.responses import JSONResponse
        if isinstance(exc, HTTPException):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        raise
    return await call_next(request)


_STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/phasmo/static", StaticFiles(directory=str(_STATIC_DIR)), name="phasmo_static")

app.include_router(pages.router)
app.include_router(config_api.router)
app.include_router(api.router)
app.include_router(dev_admin.router)


@app.get("/health", include_in_schema=False)
def health():
    registry = get_registry()
    return {"status": "healthy" if registry.valid else "degraded", "application": "phasmo-helper", "content": registry.report()}


@app.get("/ready", include_in_schema=False)
def ready():
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "status": "ready" if get_registry().valid else "not-ready",
        "application": "phasmo-helper",
        "state_directory": str(settings._STATE_DIR),
        "content": get_registry().report(),
    }


@app.get("/version", include_in_schema=False)
def version():
    return {
        "application": "phasmo-helper",
        "application_version": settings._APP_VERSION,
        "build_commit": settings._BUILD_COMMIT or None,
        "platform_support": bool(settings._PLATFORM_BASE_URL),
        "platform_version": settings._PLATFORM_VERSION,
        "game_version": get_registry().game_version.get("supportedVersion"),
        "content_version": get_registry().game_version.get("contentVersion"),
    }
