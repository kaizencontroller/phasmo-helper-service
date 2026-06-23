from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from .. import settings
from ..services.dev_admin import clear_sample_data, dev_admin_available, dev_admin_code_ok, load_sample_data

router = APIRouter()


def _page_style() -> str:
    return """
body{margin:0;background:#000;color:#f8fafc;font-family:Inter,system-ui,Segoe UI,sans-serif}main{width:min(460px,100vw);padding:10px;margin:0 auto;display:grid;gap:10px}.card,.hero{background:linear-gradient(135deg,#172235ee,#0f172aee);border:1px solid #334155;border-radius:18px;box-shadow:0 16px 40px #0007;overflow:hidden}.hero,.body{padding:14px}.head{padding:14px;border-bottom:1px solid #334155}h1,h2{margin:0}p{color:#cbd5e1;line-height:1.4}.muted{color:#94a3b8;font-size:12px}button,input{background:#0f172a;color:#f8fafc;border:1px solid #334155;border-radius:12px;padding:10px;font:inherit}button{cursor:pointer;font-weight:900}.green{background:#14532d;border-color:#22c55e}.red{background:#5b2329;border-color:#ef4444}.row{display:flex;gap:8px;flex-wrap:wrap}.status{font-size:13px;color:#93c5fd;white-space:pre-wrap}a{color:#93c5fd}
"""


@router.get("/phasmo/dev-admin")
def dev_admin_page():
    if not dev_admin_available():
        return HTMLResponse(f"""<!doctype html><html><head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><style>{_page_style()}</style></head><body><main><section class=\"hero\"><h1>Dev Admin Disabled</h1><p>Set <code>PHASMO_DEV_ADMIN_CODE</code> in Railway to enable this unlisted panel. Local development defaults to 1234.</p><p><a href=\"/phasmo\">Home</a></p></section></main></body></html>""", status_code=404)
    local_note = "Local default code is 1234." if not settings._IS_RAILWAY else "Railway requires PHASMO_DEV_ADMIN_CODE."
    return HTMLResponse(f"""<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>Phasmo Dev Admin</title><style>{_page_style()}</style></head><body><main><section class=\"hero\"><h1>Phasmo Dev Admin</h1><p class=\"muted\">Unlisted pre-launch tools. {local_note}</p><p><a href=\"/phasmo\">Home</a></p></section><section class=\"card\"><div class=\"head\"><h2>Sample Data</h2></div><div class=\"body\"><input id=\"code\" inputmode=\"numeric\" placeholder=\"admin code\"><div class=\"row\" style=\"margin-top:10px\"><button class=\"green\" id=\"load\">Load sample demo data</button><button class=\"red\" id=\"clear\">Clear sample demo data</button></div><p class=\"muted\">Creates demo-helper, demo-tracker, demo-support, demo-closed, and a seeded leaderboard.</p><div id=\"status\" class=\"status\">Ready.</div></div></section></main><script>
async function call(path){{const code=document.getElementById('code').value;const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{code}})}});const txt=await r.text();document.getElementById('status').textContent=(r.ok?'OK ':'FAILED ')+txt;}}
document.getElementById('load').onclick=()=>call('/api/phasmo/dev-admin/sample-data');
document.getElementById('clear').onclick=()=>call('/api/phasmo/dev-admin/clear-sample-data');
</script></body></html>""")


async def _require_code(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    code = str((body or {}).get("code") or "")
    if not dev_admin_code_ok(code):
        raise HTTPException(status_code=403, detail="invalid admin code")


@router.post("/api/phasmo/dev-admin/sample-data")
async def dev_admin_sample_data(request: Request):
    await _require_code(request)
    return {"ok": True, "loaded": load_sample_data()}


@router.post("/api/phasmo/dev-admin/clear-sample-data")
async def dev_admin_clear_sample_data(request: Request):
    await _require_code(request)
    return {"ok": True, "cleared": clear_sample_data()}
