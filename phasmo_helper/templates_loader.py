from __future__ import annotations

from pathlib import Path
from . import settings

_BASE_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _BASE_DIR / "templates"
_STATIC_DIR = _BASE_DIR / "static"


def _load_template(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


HTML_TEMPLATE = _load_template("app.html").replace(
    "__PLATFORM_SUPPORT_URL__",
    settings.platform_support_url(source_url="/phasmo/control"),
)
