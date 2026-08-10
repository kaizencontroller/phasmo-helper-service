from __future__ import annotations

import html
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from .. import settings
from ..services.banner import read_banner, write_banner
from ..services.dev_admin import clear_sample_data, dev_admin_available, dev_admin_code_ok, load_sample_data
from ..services.reports import export_bug_tracker, import_bug_tracker, read_bug_issues, update_bug_issue
from ..services.maintenance import read_maintenance, start_maintenance, end_maintenance
from ..services.usage import export_usage, import_usage, usage_csv, usage_summary
from ..content import get_registry, reload_registry
from ..services.permissions import read_permissions, write_permissions
from ..services.investigations import analytics_from_states

router = APIRouter()


def _page_style() -> str:
    return """
body{margin:0;background:#000;color:#f8fafc;font-family:Inter,system-ui,Segoe UI,sans-serif}main{width:min(460px,100vw);padding:10px;margin:0 auto;display:grid;gap:10px}.card,.hero{background:linear-gradient(135deg,#172235ee,#0f172aee);border:1px solid #334155;border-radius:18px;box-shadow:0 16px 40px #0007;overflow:hidden}.hero,.body{padding:14px}.head{padding:14px;border-bottom:1px solid #334155}h1,h2{margin:0}p{color:#cbd5e1;line-height:1.4}.muted{color:#94a3b8;font-size:12px}button,input{box-sizing:border-box;background:#0f172a;color:#f8fafc;border:1px solid #334155;border-radius:12px;padding:10px;font:inherit}input{width:100%}button{cursor:pointer;font-weight:900}.orange{background:#432919;border-color:#f97316}.green{background:#14532d;border-color:#22c55e}.red{background:#5b2329;border-color:#ef4444}.row{display:flex;gap:8px;flex-wrap:wrap}.status{font-size:13px;color:#93c5fd;white-space:pre-wrap}a{color:#93c5fd}textarea,select{box-sizing:border-box;background:#0f172a;color:#f8fafc;border:1px solid #334155;border-radius:12px;padding:10px;font:inherit;width:100%}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border-bottom:1px solid #334155;padding:8px 6px;text-align:left;vertical-align:top}td input,td select{min-width:105px;padding:7px}.site-banner-preview{border:1px solid #f97316;background:#432919;color:#fed7aa;border-radius:12px;padding:10px;margin-top:8px}.pill{display:inline-block;border:1px solid #334155;border-radius:999px;padding:3px 8px;font-size:11px;color:#cbd5e1}.grid{display:grid;gap:8px}.small{font-size:12px}.filebox{border:1px dashed #334155;border-radius:12px;padding:10px}.hidden{display:none!important}.lock-note{border:1px solid #334155;border-radius:12px;background:#020617;padding:10px;color:#cbd5e1}.danger-note{border:1px solid #f97316;background:#432919;color:#fed7aa;border-radius:12px;padding:10px;font-size:12px}.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.stat-card{border:1px solid #334155;background:#020617;border-radius:12px;padding:10px}.stat-card strong{display:block;font-size:18px}.stat-card span{color:#94a3b8;font-size:11px}.nowrap{white-space:nowrap}
"""


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _investigation_analytics():
    states = []
    settings._STATE_DIR.mkdir(parents=True, exist_ok=True)
    for path in settings._STATE_DIR.glob("*.json"):
        if path.name.startswith("__global_"):
            continue
        try:
            states.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return analytics_from_states(states)


@router.get("/phasmo/dev-admin")
def dev_admin_page():
    if not dev_admin_available():
        return HTMLResponse(f"""<!doctype html><html><head><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><style>{_page_style()}</style></head><body><main><section class=\"hero\"><h1>Dev Admin Disabled</h1><p>Set <code>PHASMO_DEV_ADMIN_CODE</code> in Railway to enable this unlisted panel. Local development defaults to 1234.</p><p><a href=\"/phasmo\">Home</a></p></section></main></body></html>""", status_code=404)

    local_note = "Local default code is 1234." if not settings._IS_RAILWAY else "Railway requires PHASMO_DEV_ADMIN_CODE."
    html_doc = f"""<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><title>Phasmo Dev Admin</title><style>{_page_style()}</style></head><body><main>
<section class=\"hero\"><h1>Phasmo Dev Admin</h1><p class=\"muted\">Unlisted pre-launch tools. {html.escape(local_note)}</p><p><a href=\"/phasmo\">Home</a></p></section>

<section class=\"card\"><div class=\"head\"><h2>Admin Code</h2></div><div class=\"body grid\"><input id=\"code\" inputmode=\"numeric\" placeholder=\"admin code\" autocomplete=\"current-password\"><div class=\"row\"><button id=\"unlock\" class=\"green\">Unlock Admin Tools</button><button id=\"lock\">Lock</button></div><p class=\"muted\">Admin tools and stored data stay hidden until this code is accepted.</p><div id=\"status\" class=\"status\">Locked.</div></div></section>

<div id=\"adminTools\" class=\"hidden\">
<section class=\"card\"><div class=\"head\"><h2>Maintenance / Release Automation</h2></div><div class=\"body grid\">
<p class=\"muted\">Manual test controls for the same maintenance state that GitHub Actions can set during scheduled releases.</p>
<div class=\"lock-note\"><strong>Current state</strong><pre id=\"maintCurrent\" style=\"white-space:pre-wrap;margin:8px 0 0;color:#cbd5e1\">Unlock to load.</pre></div>
<input id=\"maintVersion\" placeholder=\"Staged version / release SHA, example: v5.5 or abc1234\">
<input id=\"maintId\" placeholder=\"Maintenance ID, example: phasmo-v5-5-2026-06-25\">
<textarea id=\"maintMessage\" rows=\"3\" placeholder=\"Maintenance message shown to users.\"></textarea>
<label class=\"small\"><input id=\"maintReadOnly\" type=\"checkbox\" checked style=\"width:auto\"> Read-only during maintenance</label>
<label class=\"small\"><input id=\"maintBlockNew\" type=\"checkbox\" checked style=\"width:auto\"> Pause new room creation</label>
<div class=\"row\"><button id=\"startMaintenance\" class=\"orange\">Start Maintenance</button><button id=\"endMaintenance\" class=\"green\">End Maintenance Success</button><button id=\"failMaintenance\" class=\"red\">Mark Failed</button></div>
<div class=\"danger-note\">Use these buttons for local/manual testing. Scheduled deployment should normally be driven by GitHub Actions.</div>
</div></section>

<section class=\"card\"><div class=\"head\"><h2>Site Banner</h2></div><div class=\"body grid\">
<label class=\"small\"><input id=\"bannerEnabled\" type=\"checkbox\" style=\"width:auto\"> Enable public banner</label>
<select id=\"bannerLevel\"><option value=\"maintenance\">Maintenance / safety orange</option><option value=\"notice\">Notice</option><option value=\"warning\">Warning</option></select>
<textarea id=\"bannerMessage\" rows=\"4\" placeholder=\"Banner text shown at the top of Phasmo pages.\"></textarea>
<input id=\"bannerExpires\" placeholder=\"Optional expiresAt ISO timestamp\">
<div class=\"row\"><button id=\"saveBanner\" class=\"orange\">Save Banner</button><button id=\"disableBanner\">Disable Banner</button></div>
<div class=\"site-banner-preview\" id=\"bannerPreview\">Preview: scheduled maintenance / update notice will appear here.</div>
</div></section>

<section class=\"card\"><div class=\"head\"><h2>Bug Tracker</h2></div><div class=\"body grid\">
<p class=\"muted\">Triage submitted bug reports, preserve status across builds, and export/import the tracker.</p>
<div class=\"row\"><button id=\"loadIssues\">Refresh Issues</button><button id=\"exportIssues\">Export JSON</button></div>
<div class=\"filebox\"><input id=\"importFile\" type=\"file\" accept=\"application/json,.json\"><button id=\"importIssues\">Import JSON</button><p class=\"muted\">Import merges by issue id. Export before importing older files.</p></div>
<div class=\"table-wrap\"><table><thead><tr><th>ID</th><th>Issue</th><th>Status</th><th>Priority</th><th>Versions</th><th>Save</th></tr></thead><tbody id=\"issueRows\"><tr><td colspan=\"6\" class=\"muted\">Unlock, then click Refresh Issues.</td></tr></tbody></table></div>
</div></section>

<section class=\"card\"><div class=\"head\"><h2>Room Usage Log</h2></div><div class=\"body grid\">
<p class=\"muted\">See which rooms are being used, how many rounds were observed/completed, and how long sessions lasted. Export/import this log between builds until persistent storage is configured.</p>
<div class=\"stat-grid\" id=\"usageStats\"><div class=\"stat-card\"><strong>—</strong><span>rooms</span></div><div class=\"stat-card\"><strong>—</strong><span>rounds</span></div><div class=\"stat-card\"><strong>—</strong><span>completed</span></div><div class=\"stat-card\"><strong>—</strong><span>active hours</span></div></div>
<div class=\"row\"><button id=\"loadUsage\">Refresh Usage</button><button id=\"exportUsageJson\">Export JSON</button><button id=\"exportUsageCsv\">Export CSV</button></div>
<div class=\"filebox\"><input id=\"importUsageFile\" type=\"file\" accept=\"application/json,.json\"><button id=\"importUsage\">Import Usage JSON</button><p class=\"muted\">Import merges by room and round id. Export before importing older files.</p></div>
<div class=\"table-wrap\"><table><thead><tr><th>Room</th><th>Status</th><th>Rounds</th><th>Duration</th><th>Last Seen</th><th>Details</th></tr></thead><tbody id=\"usageRows\"><tr><td colspan=\"6\" class=\"muted\">Unlock, then click Refresh Usage.</td></tr></tbody></table></div>
</div></section>

<section class=\"card\"><div class=\"head\"><h2>Content Validation</h2></div><div class=\"body grid\"><p class=\"muted\">Checks IDs, references, evidence, encyclopedia fields, commands, and permissions before activation.</p><pre id=\"contentValidation\" class=\"lock-note\" style=\"white-space:pre-wrap\">Unlock to load.</pre><div class=\"row\"><button id=\"validateContent\">Validate</button><button id=\"reloadContent\" class=\"orange\">Reload Valid Content</button></div></div></section>

<section class=\"card\"><div class=\"head\"><h2>Investigation Analytics</h2></div><div class=\"body grid\"><pre id=\"investigationAnalytics\" class=\"lock-note\" style=\"white-space:pre-wrap\">Unlock to load.</pre><button id=\"loadAnalytics\">Refresh Analytics</button></div></section>

<section class=\"card\"><div class=\"head\"><h2>Permission Groups</h2></div><div class=\"body grid\"><p class=\"muted\">Create, rename, delete, import/export, assign users, and bulk edit groups as JSON.</p><textarea id=\"permissionGroups\" rows=\"12\" spellcheck=\"false\"></textarea><div class=\"row\"><button id=\"saveGroups\" class=\"green\">Save Groups</button><button id=\"exportGroups\">Export</button><input id=\"importGroupsFile\" type=\"file\" accept=\"application/json,.json\"><button id=\"importGroups\">Import</button></div></div></section>

<section class=\"card\"><div class=\"head\"><h2>Sample Data</h2></div><div class=\"body\"><div class=\"row\"><button class=\"green\" id=\"load\">Load sample demo data</button><button class=\"red\" id=\"clear\">Clear sample demo data</button></div><p class=\"muted\">Creates demo-helper, demo-tracker, demo-support, demo-closed, and a seeded leaderboard.</p></div></section>
</div>
</main><script>
const $ = (id) => document.getElementById(id);
const statusBox = $('status');
const tools = $('adminTools');
function code(){{return $('code').value.trim();}}
function setStatus(msg){{statusBox.textContent=msg;}}
function setLocked(locked){{tools.classList.toggle('hidden', locked); setStatus(locked?'Locked.':'Unlocked.');}}
async function call(path, payload={{}}){{
  const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{code:code(),...payload}})}});
  const txt=await r.text();
  let data; try{{data=JSON.parse(txt)}}catch(e){{data={{raw:txt}}}}
  setStatus((r.ok?'OK ':'FAILED ')+JSON.stringify(data,null,2));
  if(!r.ok) throw new Error(txt);
  return data;
}}
function esc(s){{return String(s??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[c]));}}
function populateBootstrap(data){{
  const banner=data.banner||{{}};
  $('bannerEnabled').checked=!!banner.enabled;
  $('bannerLevel').value=banner.level||'maintenance';
  $('bannerMessage').value=banner.message||'';
  $('bannerExpires').value=banner.expiresAt||'';
  $('bannerPreview').textContent=$('bannerMessage').value||'Preview: scheduled maintenance / update notice will appear here.';
  const maint=data.maintenance||{{}};
  $('maintCurrent').textContent=JSON.stringify(maint,null,2);
  $('maintVersion').value=maint.stagedVersion||'';
  $('maintId').value=maint.maintenanceId||'';
  $('maintMessage').value=maint.message||'Scheduled Phasmo Helper update is deploying. The app may briefly refresh or become read-only.';
  $('maintReadOnly').checked=!!(maint.readOnly ?? true);
  $('maintBlockNew').checked=!!(maint.blockNewRooms ?? true);
  $('contentValidation').textContent=JSON.stringify(data.contentValidation||{{}},null,2);
  $('investigationAnalytics').textContent=JSON.stringify(data.investigationAnalytics||{{}},null,2);
  $('permissionGroups').value=JSON.stringify((data.permissions||{{}}).groups||{{}},null,2);
}}
$('unlock').onclick=async()=>{{try{{const data=await call('/api/phasmo/dev-admin/bootstrap'); populateBootstrap(data); setLocked(false);}}catch(e){{setLocked(true);}}}};
$('lock').onclick=()=>{{$('code').value=''; setLocked(true);}};
$('code').addEventListener('keydown',e=>{{if(e.key==='Enter')$('unlock').click();}});
$('load').onclick=()=>call('/api/phasmo/dev-admin/sample-data');
$('clear').onclick=()=>call('/api/phasmo/dev-admin/clear-sample-data');
$('validateContent').onclick=async()=>{{$('contentValidation').textContent=JSON.stringify((await call('/api/phasmo/dev-admin/content/validate')).validation,null,2);}};
$('reloadContent').onclick=async()=>{{$('contentValidation').textContent=JSON.stringify((await call('/api/phasmo/dev-admin/content/reload')).validation,null,2);}};
$('loadAnalytics').onclick=async()=>{{$('investigationAnalytics').textContent=JSON.stringify((await call('/api/phasmo/dev-admin/investigation-analytics')).analytics,null,2);}};
$('saveGroups').onclick=async()=>{{const groups=JSON.parse($('permissionGroups').value||'{{}}');await call('/api/phasmo/dev-admin/permissions',{{groups}});}};
$('exportGroups').onclick=()=>{{const blob=new Blob([$('permissionGroups').value],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='phasmo-permission-groups.json';a.click();URL.revokeObjectURL(a.href);}};
$('importGroups').onclick=async()=>{{const f=$('importGroupsFile').files[0];if(!f)return alert('Choose a JSON file first.');$('permissionGroups').value=JSON.stringify(JSON.parse(await f.text()),null,2);}};
$('bannerMessage').oninput=()=>{{$('bannerPreview').textContent=$('bannerMessage').value||'Preview: scheduled maintenance / update notice will appear here.';}};
$('saveBanner').onclick=()=>call('/api/phasmo/dev-admin/banner',{{enabled:$('bannerEnabled').checked,level:$('bannerLevel').value,message:$('bannerMessage').value,expiresAt:$('bannerExpires').value}});
$('disableBanner').onclick=()=>{{$('bannerEnabled').checked=false;call('/api/phasmo/dev-admin/banner',{{enabled:false}});}};
async function refreshMaintenance(){{const data=await call('/api/phasmo/dev-admin/bootstrap'); populateBootstrap(data);}}
$('startMaintenance').onclick=async()=>{{await call('/api/phasmo/dev-admin/maintenance/start',{{stagedVersion:$('maintVersion').value,maintenanceId:$('maintId').value,message:$('maintMessage').value,readOnly:$('maintReadOnly').checked,blockNewRooms:$('maintBlockNew').checked,mode:$('maintReadOnly').checked?'read_only':($('maintBlockNew').checked?'block_new_rooms':'banner')}}); await refreshMaintenance();}};
$('endMaintenance').onclick=async()=>{{await call('/api/phasmo/dev-admin/maintenance/end',{{success:true,result:'manual maintenance complete',message:'Maintenance complete.'}}); await refreshMaintenance();}};
$('failMaintenance').onclick=async()=>{{await call('/api/phasmo/dev-admin/maintenance/end',{{success:false,result:'manual maintenance marked failed',message:'Maintenance/update did not complete successfully. Manual review may be needed.'}}); await refreshMaintenance();}};
async function loadIssues(){{
  const data=await call('/api/phasmo/dev-admin/bug-tracker/list');
  const rows=$('issueRows');
  const issues=data.issues||[];
  if(!issues.length){{rows.innerHTML='<tr><td colspan="6" class="muted">No reports yet.</td></tr>';return;}}
  rows.innerHTML=issues.map(i=>`<tr data-id="${{esc(i.id)}}">
    <td><span class="pill">${{esc(i.id)}}</span><br><span class="muted">${{esc(i.createdAt||'')}}</span></td>
    <td><b>${{esc(i.title||'Untitled')}}</b><br><span class="muted">${{esc(i.type||i.category||'')}} · room: ${{esc(i.room||'')}}</span><br><span class="small">${{esc((i.description||i.message||i.details||'').slice(0,180))}}</span><br><textarea rows="2" data-field="internalNotes" placeholder="Internal notes">${{esc(i.internalNotes||'')}}</textarea></td>
    <td><select data-field="status"><option>new</option><option>triaged</option><option>planned</option><option>in progress</option><option>fixed</option><option>won't fix</option><option>duplicate</option><option>needs info</option></select></td>
    <td><select data-field="priority"><option>low</option><option>medium</option><option>high</option><option>urgent</option></select></td>
    <td><input data-field="targetVersion" placeholder="target" value="${{esc(i.targetVersion||'')}}"><input data-field="fixedVersion" placeholder="fixed" value="${{esc(i.fixedVersion||'')}}"></td>
    <td><button class="green" onclick="saveIssue('${{esc(i.id)}}')">Save</button></td>
  </tr>`).join('');
  for(const i of issues){{
    const row=document.querySelector(`tr[data-id="${{CSS.escape(i.id)}}"]`);
    if(row){{row.querySelector('[data-field="status"]').value=i.status||'new';row.querySelector('[data-field="priority"]').value=i.priority||'medium';}}
  }}
}}
async function saveIssue(id){{
  const row=document.querySelector(`tr[data-id="${{CSS.escape(id)}}"]`); const patch={{}};
  row.querySelectorAll('[data-field]').forEach(el=>patch[el.dataset.field]=el.value);
  await call('/api/phasmo/dev-admin/bug-tracker/update',{{id,patch}});
}}
window.saveIssue=saveIssue;
$('loadIssues').onclick=loadIssues;
$('exportIssues').onclick=async()=>{{const data=await call('/api/phasmo/dev-admin/bug-tracker/export'); const blob=new Blob([JSON.stringify(data,null,2)],{{type:'application/json'}}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='phasmo_bug_tracker_export.json'; a.click();}};
$('importIssues').onclick=async()=>{{const f=$('importFile').files[0]; if(!f) return alert('Choose a JSON export first.'); const payload=JSON.parse(await f.text()); await call('/api/phasmo/dev-admin/bug-tracker/import',{{payload}}); await loadIssues();}};
function fmtMs(ms){{
  ms=Number(ms||0); const mins=Math.round(ms/60000);
  if(mins<60) return mins+'m';
  const hrs=Math.floor(mins/60); const rem=mins%60;
  if(hrs<48) return hrs+'h '+rem+'m';
  const days=Math.floor(hrs/24); return days+'d '+(hrs%24)+'h';
}}
function fmtDate(ms){{if(!ms)return '—'; try{{return new Date(Number(ms)).toLocaleString();}}catch(e){{return String(ms)}}}}
function downloadText(name, text, type){{const blob=new Blob([text],{{type:type||'text/plain'}}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href),1000);}}
async function loadUsage(){{
  const data=await call('/api/phasmo/dev-admin/usage/list');
  const totals=data.totals||{{}};
  $('usageStats').innerHTML=`<div class="stat-card"><strong>${{esc(totals.rooms??0)}}</strong><span>rooms</span></div><div class="stat-card"><strong>${{esc(totals.roundsObserved??0)}}</strong><span>rounds observed</span></div><div class="stat-card"><strong>${{esc(totals.roundsCompleted??0)}}</strong><span>completed rounds</span></div><div class="stat-card"><strong>${{esc(totals.totalActiveHours??0)}}</strong><span>active hours</span></div>`;
  const rows=$('usageRows'); const rooms=data.rooms||[];
  if(!rooms.length){{rows.innerHTML='<tr><td colspan="6" class="muted">No usage logged yet.</td></tr>'; return;}}
  rows.innerHTML=rooms.map(r=>`<tr>
    <td><b>${{esc(r.room)}}</b><br><span class="muted">${{esc(r.lastMap||'unknown')}} · ${{esc(r.lastDifficulty||'unknown')}}</span></td>
    <td><span class="pill">${{esc(r.roomStatus||'open')}}</span><br><span class="muted">${{r.roomLocked?'locked':'open access'}}${{r.supportOptIn?' · support ok':''}}</span></td>
    <td><b>${{esc(r.roundsObserved||0)}}</b> observed<br><span class="muted">${{esc(r.roundsCompleted||0)}} completed · next ${{esc(r.nextRoundCount||0)}}</span></td>
    <td class="nowrap">${{fmtMs(r.durationMs)}}<br><span class="muted">writes ${{esc(r.writeCount||0)}} · cmds ${{esc(r.commandCount||0)}}</span></td>
    <td class="nowrap">${{fmtDate(r.lastSeenAt)}}<br><span class="muted">first ${{fmtDate(r.firstSeenAt)}}</span></td>
    <td><span class="muted">last event: ${{esc(r.lastEvent||'')}}</span><br><span class="muted">channel: ${{esc(r.supportChannel||'—')}}</span></td>
  </tr>`).join('');
}}
$('loadUsage').onclick=loadUsage;
$('exportUsageJson').onclick=async()=>{{const data=await call('/api/phasmo/dev-admin/usage/export'); downloadText('phasmo_room_usage_export.json', JSON.stringify(data,null,2), 'application/json');}};
$('exportUsageCsv').onclick=async()=>{{const data=await call('/api/phasmo/dev-admin/usage/export-csv'); downloadText('phasmo_room_usage_export.csv', data.csv||'', 'text/csv');}};
$('importUsage').onclick=async()=>{{const f=$('importUsageFile').files[0]; if(!f) return alert('Choose a usage JSON export first.'); const payload=JSON.parse(await f.text()); await call('/api/phasmo/dev-admin/usage/import',{{payload}}); await loadUsage();}};

</script></body></html>"""
    return HTMLResponse(html_doc)


async def _require_code(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    code = str((body or {}).get("code") or "")
    if not dev_admin_code_ok(code):
        raise HTTPException(status_code=403, detail="invalid admin code")
    return body or {}


@router.post("/api/phasmo/dev-admin/bootstrap")
async def dev_admin_bootstrap(request: Request):
    await _require_code(request)
    return {
        "ok": True, "banner": read_banner(), "maintenance": read_maintenance(),
        "contentValidation": get_registry().report(), "permissions": read_permissions(),
        "investigationAnalytics": _investigation_analytics(),
    }


@router.post("/api/phasmo/dev-admin/content/validate")
async def dev_admin_content_validate(request: Request):
    await _require_code(request)
    return {"ok": True, "validation": get_registry().report()}


@router.post("/api/phasmo/dev-admin/content/reload")
async def dev_admin_content_reload(request: Request):
    await _require_code(request)
    candidate = reload_registry()
    return {"ok": candidate.valid, "validation": candidate.report()}


@router.post("/api/phasmo/dev-admin/investigation-analytics")
async def dev_admin_investigation_analytics(request: Request):
    await _require_code(request)
    return {"ok": True, "analytics": _investigation_analytics()}


@router.post("/api/phasmo/dev-admin/permissions")
async def dev_admin_permissions(request: Request):
    body = await _require_code(request)
    return {"ok": True, "permissions": write_permissions(body)}


@router.post("/api/phasmo/dev-admin/sample-data")
async def dev_admin_sample_data(request: Request):
    await _require_code(request)
    return {"ok": True, "loaded": load_sample_data()}


@router.post("/api/phasmo/dev-admin/clear-sample-data")
async def dev_admin_clear_sample_data(request: Request):
    await _require_code(request)
    return {"ok": True, "cleared": clear_sample_data()}


@router.post("/api/phasmo/dev-admin/banner")
async def dev_admin_banner(request: Request):
    body = await _require_code(request)
    return {"ok": True, "banner": write_banner(body)}


@router.post("/api/phasmo/dev-admin/bug-tracker/list")
async def dev_admin_bug_tracker_list(request: Request):
    await _require_code(request)
    return {"ok": True, "issues": read_bug_issues()}


@router.post("/api/phasmo/dev-admin/bug-tracker/update")
async def dev_admin_bug_tracker_update(request: Request):
    body = await _require_code(request)
    try:
        issue = update_bug_issue(str(body.get("id") or ""), body.get("patch") or {})
    except KeyError:
        raise HTTPException(status_code=404, detail="issue not found")
    return {"ok": True, "issue": issue}


@router.post("/api/phasmo/dev-admin/bug-tracker/export")
async def dev_admin_bug_tracker_export(request: Request):
    await _require_code(request)
    return export_bug_tracker()


@router.post("/api/phasmo/dev-admin/bug-tracker/import")
async def dev_admin_bug_tracker_import(request: Request):
    body = await _require_code(request)
    return {"ok": True, "result": import_bug_tracker(body.get("payload") or {})}


@router.post("/api/phasmo/dev-admin/maintenance/start")
async def dev_admin_maintenance_start(request: Request):
    body = await _require_code(request)
    return {"ok": True, "maintenance": start_maintenance(body, updated_by="dev-admin")}


@router.post("/api/phasmo/dev-admin/maintenance/end")
async def dev_admin_maintenance_end(request: Request):
    body = await _require_code(request)
    return {"ok": True, "maintenance": end_maintenance(body, updated_by="dev-admin")}

@router.post("/api/phasmo/dev-admin/usage/list")
async def dev_admin_usage_list(request: Request):
    await _require_code(request)
    return usage_summary()


@router.post("/api/phasmo/dev-admin/usage/export")
async def dev_admin_usage_export(request: Request):
    await _require_code(request)
    return export_usage()


@router.post("/api/phasmo/dev-admin/usage/export-csv")
async def dev_admin_usage_export_csv(request: Request):
    await _require_code(request)
    return {"ok": True, "csv": usage_csv()}


@router.post("/api/phasmo/dev-admin/usage/import")
async def dev_admin_usage_import(request: Request):
    body = await _require_code(request)
    return {"ok": True, "result": import_usage(body.get("payload") or {})}
