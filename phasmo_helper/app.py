from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .routes import api, config_api, pages, dev_admin

app = FastAPI(title="Kaizen Phasmophobia Helper")

_STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/phasmo/static", StaticFiles(directory=str(_STATIC_DIR)), name="phasmo_static")

app.include_router(pages.router)
app.include_router(config_api.router)
app.include_router(api.router)
app.include_router(dev_admin.router)
