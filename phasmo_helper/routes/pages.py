from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from .. import settings
from ..core.config import CONFIG_DESCRIPTIONS, _read_config
from ..core.data import GHOST_NAMES
from ..core.utils import _normal_user
from ..services.leaderboard import _read_leaderboard
from ..services.rooms import active_room_summaries
from ..services.banner import read_banner
from ..services.security import validate_room_name
from ..services.state import _room_name, _room_code_ok, read_state
from ..templates_loader import HTML_TEMPLATE

router = APIRouter()

@router.get("/")
def root():
    return RedirectResponse("/phasmo")



def _public_page_style() -> str:
    return """
body{margin:0;background:#000;color:#f8fafc;font-family:Inter,system-ui,Segoe UI,sans-serif}
main{width:min(460px,100vw);padding:10px;margin:0 auto;display:grid;gap:10px}
.hero,.card{background:linear-gradient(135deg,#172235ee,#0f172aee);border:1px solid #334155;border-radius:18px;box-shadow:0 16px 40px #0007;overflow:hidden}
.hero{padding:16px;display:grid;gap:12px}
.brand{display:flex;gap:10px;align-items:center;min-width:0}.logo{width:48px;height:48px;border-radius:16px;background:radial-gradient(circle at 30% 20%,#38bdf855,transparent 38%),linear-gradient(135deg,#0f172a,#1e293b);border:1px solid #475569;display:grid;place-items:center;font-weight:950;letter-spacing:-.08em;box-shadow:inset 0 0 22px #ffffff12}.brandcopy{min-width:0;overflow:hidden}.kicker{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.12em;font-weight:900}h1{margin:2px 0 0;font-size:28px;line-height:.95;letter-spacing:-.045em}h2{margin:0;font-size:18px}p{color:#cbd5e1;line-height:1.45;margin:0 0 10px}.muted{color:#94a3b8;font-size:12px}.actions{display:flex;gap:7px;flex-wrap:wrap;margin:8px 0 12px}.support-links{display:grid;gap:7px}.support-row{display:flex;gap:9px;flex-wrap:wrap}.support-row.meta{font-size:11px}.support-row.version-row{color:#94a3b8;font-size:11px}.support-row a{color:#93c5fd;text-decoration:none}.content h2{margin:18px 0 8px;font-size:18px}.content h2:first-child{margin-top:0}.content ul,.content ol{margin:8px 0 16px;padding-left:24px}.content p:last-child{margin-bottom:0}.button-row{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 18px}.static-hero{gap:10px}.static-hero .brand-link{display:flex;gap:10px;align-items:center}.page-title-note{margin-top:2px}a.button,button{border:1px solid #475569;background:#0f172a;color:#f8fafc;border-radius:999px;padding:9px 11px;text-decoration:none;font-weight:850;cursor:pointer;font-size:13px}a.button.primary,button.primary{border-color:#22c55e;background:#14532d}.card .head{padding:13px;border-bottom:1px solid #334155;display:flex;justify-content:space-between;gap:8px;align-items:center}.card .body{padding:13px}.room-grid{display:grid;gap:8px}.room-card{border:1px solid #334155;background:#0f172a;border-radius:14px;padding:10px}.room-card strong{display:block}.room-card span{display:block;color:#94a3b8;font-size:12px;margin-top:2px}.room-card p{font-size:13px;margin:8px 0}.room-card div:last-child{display:flex;gap:8px;flex-wrap:wrap}.room-card a{color:#93c5fd;font-size:12px;text-decoration:none}.support-note{font-size:11px;line-height:1.35;color:#94a3b8}.support-footer{border-style:dashed;opacity:.85}input,textarea,select{background:#0f172a;color:#f8fafc;border:1px solid #334155;border-radius:12px;padding:10px;font:inherit;width:100%}textarea{min-height:120px}.form-grid{display:grid;grid-template-columns:1fr;gap:10px}.status{color:#93c5fd;font-size:13px;margin-top:8px}.small{font-size:12px;color:#94a3b8}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border-bottom:1px solid #334155;padding:8px 5px;text-align:left;vertical-align:top}th{color:#94a3b8;text-transform:uppercase;letter-spacing:.08em}.table-wrap{overflow-x:auto}.locked{color:#fde68a;font-weight:900}code{color:#bae6fd;background:#020617;border:1px solid #334155;border-radius:999px;padding:2px 6px;font-size:12px}ol{color:#cbd5e1;line-height:1.45}li{margin:6px 0}.brand-link{display:block;text-decoration:none;color:inherit;cursor:pointer}.brand-link:hover{border-color:#60a5fa}.site-banner{border:1px solid #f97316;background:#432919;color:#fed7aa;border-radius:14px;padding:10px 12px;font-weight:850;line-height:1.3}.site-banner .small{color:#fdba74}.error{border:1px solid #ef4444;background:#451a20;color:#fecaca;border-radius:12px;padding:10px;font-size:13px}
"""




def _site_banner_html() -> str:
    banner = read_banner()
    if not banner.get("enabled") or not str(banner.get("message") or "").strip():
        return ""
    msg = html.escape(str(banner.get("message") or ""))
    level = html.escape(str(banner.get("level") or "notice"))
    return f"<section class='site-banner' data-level='{level}'><div>{msg}</div><div class='small'>Kaizen Controller notice</div></section>"


def _locked_room_gate(safe_room: str, target_path: str, code: str | None = None) -> HTMLResponse | None:
    safe_room = _room_name(safe_room)
    state = read_state(safe_room)
    if state.get("roomStatus") == "closed":
        return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Room Closed</title><style>{_public_page_style()}</style></head><body><main>{_site_banner_html()}<a class="hero brand-link" href="/phasmo"><div class="brand"><div class="logo">KC</div><div class="brandcopy"><div class="kicker">Kaizen Phasmo Helper</div><h1>Room Closed</h1></div></div><p>This room session has ended and is no longer accepting updates.</p></a><section class="card"><div class="body actions"><a class="button primary" href="/phasmo/room">Create Room</a><a class="button" href="/phasmo/rooms">Active Rooms</a></div></section>{_support_footer(safe_room)}</main></body></html>""", status_code=410)
    if _room_code_ok(state, code or ""):
        return None
    target = f"{target_path}?room={safe_room}"
    return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Locked Room</title><style>{_public_page_style()}</style></head><body><main>{_site_banner_html()}<a class="hero brand-link" href="/phasmo"><div class="brand"><div class="logo">KC</div><div class="brandcopy"><div class="kicker">room: {safe_room}</div><h1>Locked Room</h1></div></div><p>Enter the 4-digit room passcode before joining this room.</p></a><section class="card"><div class="body"><form id="gateForm" class="form-grid"><input id="gateCode" inputmode="numeric" maxlength="4" pattern="[0-9]*" placeholder="4-digit passcode"><button class="primary" type="submit">Enter Room</button><a class="button" href="/phasmo/rooms">Back to Active Rooms</a></form><div id="gateStatus" class="status"></div></div></section>{_support_footer(safe_room)}</main><script>
const room={safe_room!r}; const target={target!r};
function key(r){{return 'phasmoRoomCode:'+r}}
function clean(v){{return (v||'').replace(/[^0-9]/g,'').slice(0,4)}}
async function tryCode(c,go){{if(clean(c).length!==4)return false; const r=await fetch('/api/phasmo/state?room='+encodeURIComponent(room)+'&code='+encodeURIComponent(clean(c))); if(r.ok){{localStorage.setItem(key(room),clean(c)); if(go) location.href=target+'&code='+encodeURIComponent(clean(c)); return true;}} return false;}}
(async()=>{{const stored=localStorage.getItem(key(room)); if(stored) await tryCode(stored,true);}})();
document.getElementById('gateForm').addEventListener('submit',async e=>{{e.preventDefault(); const c=document.getElementById('gateCode').value; const ok=await tryCode(c,true); document.getElementById('gateStatus').textContent=ok?'Opening room…':'Passcode not accepted.';}});
</script></body></html>""", status_code=403)


def _room_gate_or_template(room: str | None, code: str | None, target_path: str, mode: str) -> HTMLResponse:
    safe_room = _room_name(room or "default")
    gate = _locked_room_gate(safe_room, target_path, code)
    if gate:
        return gate
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", mode))

def _support_footer(safe_room: str = "default") -> str:
    safe_room = _room_name(safe_room)
    quick = f'<a href="{settings._QUICKSTART_VIDEO_URL}" target="_blank" rel="noopener">Quick start video</a>' if settings._QUICKSTART_VIDEO_URL else ""
    return f"""
<section class=\"card support-footer\"><div class=\"body\">
  <div class=\"support-links\">
    <div class=\"support-row\">
      <a href=\"/phasmo/getting-started\">Getting started</a>
      <a href=\"/phasmo/commands\">Viewer commands</a>
      <a href=\"/phasmo/release-notes\">Release notes</a>
    </div>
    <div class=\"support-row\">
      <a href=\"/phasmo/streamerbot\">Streamer.bot setup</a>
      <a href=\"https://drive.google.com/drive/folders/1n7jfz7QGnkPUj3fQ715420cKHW96W97I\" target=\"_blank\" rel=\"noopener\">Support files</a>
      <a href=\"/phasmo/bug-report?room={safe_room}\">Bug reports</a>
      {quick}
    </div>
    <div class=\"support-row meta\">
      <a href=\"/phasmo/privacy\">Privacy</a>
      <a href=\"/phasmo/terms\">Terms</a>
      <a href=\"/phasmo/data-retention\">Data retention</a>
    </div>
    <div class=\"support-row version-row\">Version {html.escape(settings._APP_VERSION)}</div>
  </div>
  <div class=\"support-note\">This helper is happily provided free for the Phasmophobia community. Optional donations help keep hosting covered and support future development.</div>
</div></section>
"""



@router.get("/phasmo")
def phasmo_index(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "kaizen")
    rooms = active_room_summaries()[:6]
    room_cards = ""
    for item in rooms:
        room_name = html.escape(str(item.get("room") or "default"))
        mode = "active" if item.get("setupComplete") else "setup"
        locked = " • locked" if item.get("locked") else ""
        ghost = item.get("confirmedGhost") or "pending"
        room_cards += f"""
        <article class=\"room-card\">
          <div><strong>{room_name}</strong><span>{mode}{locked} • updated {item.get('ageMinutes')}m ago</span></div>
          <p>{html.escape(str(item.get('map') or 'unknown'))} • {html.escape(str(item.get('difficulty') or 'unknown'))} • result: {html.escape(str(ghost))}</p>
          <div><a href=\"/phasmo/control?room={room_name}\">Open</a><a href=\"/phasmo/leaderboard?room={room_name}\">Leaderboard</a></div>
        </article>
        """
    if not room_cards:
        room_cards = "<p class='muted'>No active rooms right now. Rooms expire after 4 hours without updates.</p>"
    html_doc = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>Kaizen Phasmo Helper</title><style>{_public_page_style()}</style></head>
<body><main>
{_site_banner_html()}
<section class=\"hero\">
  <a class=\"brand brand-link\" href=\"/phasmo\"><div class=\"logo\">KC</div><div class=\"brandcopy\"><div class=\"kicker\">Kaizen Controller tools</div><h1>Phasmo Helper</h1></div></a>
  <p>A lightweight group and streamer helper for Phasmophobia evidence tracking, behavior clues, chat guesses, OBS overlays, and contract result scoring.</p>
  <div class=\"actions\"><a class=\"button primary\" href=\"/phasmo/room?room={safe_room}\">Create Room</a></div>
  <div class=\"small\"><strong>New here?</strong></div>
  <div class=\"actions\"><a class=\"button\" href=\"/phasmo/getting-started?room={safe_room}\">Getting Started</a><a class=\"button\" href=\"/phasmo/commands?room={safe_room}\">Viewer Commands</a><a class=\"button\" href=\"/phasmo/rooms\">Active Rooms</a><a class=\"button\" href=\"{settings._QUICKSTART_VIDEO_URL}\" target=\"_blank\" rel=\"noopener\" style=\"display:{'inline-block' if settings._QUICKSTART_VIDEO_URL else 'none'}\">Quick Start Video</a></div>
  <p class=\"muted\">Optional room passcodes are 4 digits. Rooms are temporary and expire after 4 hours without updates.</p>
</section>
<section class=\"card\"><div class=\"head\"><h2>Active Rooms</h2><a class=\"button\" href=\"/phasmo/rooms\">All</a></div><div class=\"body\"><div class=\"room-grid\">{room_cards}</div></div></section>
{_support_footer(safe_room)}
</main></body></html>"""
    return HTMLResponse(html_doc)


@router.get("/phasmo/streamerbot")
def phasmo_streamerbot(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "kaizen")
    app_url = "https://YOUR-PHASMO-APP.example.com"
    body = f"""
<p>This page is the one-time Streamer.bot setup SOP. Do this before creating rooms. After setup, changing rooms should only require updating one variable.</p>
<h2>What this solves</h2>
<p>Every Phasmo chat command should use the same Streamer.bot action. The room name should come from a Streamer.bot variable, not from a hard-coded URL.</p>
<h2>Step 1 — Create a global variable</h2>
<p>In Streamer.bot, create or choose a global variable:</p>
<pre style="white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:10px;color:#cbd5e1;overflow:auto">Variable name: phasmoRoom
Variable value: {safe_room}</pre>
<p class="small">If you always use the same room, this may never need to change. If you play with different groups, update only this value.</p>
<h2>Step 2 — Create one command bridge action</h2>
<p>Create one Streamer.bot action named <strong>Phasmo Command Bridge</strong>.</p>
<pre style="white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:10px;color:#cbd5e1;overflow:auto">HTTP Method: POST
URL: {app_url}/api/phasmo/command
Content-Type: application/json</pre>
<h2>Step 3 — Paste the JSON body</h2>
<pre style="white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:10px;color:#cbd5e1;overflow:auto">{{
  "room": "%phasmoRoom%",
  "command": "%rawInput%",
  "user": "%userName%",
  "source": "streamerbot",
  "channel": "%broadcasterUserName%"
}}</pre>
<p class="small">Streamer.bot variable names can differ by version/action type. Use the variable picker in your install if one of these does not resolve.</p>
<h2>Step 4 — Attach chat commands to the same action</h2>
<p>Point each command trigger at <strong>Phasmo Command Bridge</strong>:</p>
<pre style="white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:10px;color:#cbd5e1;overflow:auto">!guess
!vote
!unguess
!unvote
!ev
!evidence
!beh
!be
!result
!actual</pre>
<h2>Step 5 — Test before going live</h2>
<p>Set <code>phasmoRoom</code> to your test room, open the control page, then send:</p>
<pre style="white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:10px;color:#cbd5e1;overflow:auto">!guess Deogen
!ev orbs yes
!result Deogen</pre>
<h2>Changing rooms later</h2>
<p>Do not edit every command. Just update the variable:</p>
<pre style="white-space:pre-wrap;background:#020617;border:1px solid #334155;border-radius:12px;padding:10px;color:#cbd5e1;overflow:auto">phasmoRoom = new-room-name</pre>
<p><a class="button primary" href="/phasmo/room?room={safe_room}">Create Room</a> <a class="button" href="/phasmo/control?room={safe_room}">Open control</a></p>
"""
    return _simple_info_page("Streamer.bot Setup", body, safe_room)



@router.get("/phasmo/getting-started")
def phasmo_getting_started(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "kaizen")
    body = f"""
<p>Use this as the quick mental model for running a stream/session with Phasmo Helper.</p>
<h2>Basic flow</h2>
<ol>
  <li><strong>Create Room</strong> — choose a stream-safe room name and optional 4-digit passcode.</li>
  <li><strong>Config</strong> — choose Helper or Tracker behavior for the control screen and overlay.</li>
  <li><strong>Round Setup</strong> — choose map, difficulty, weather, players, response type, and evidence mode.</li>
  <li><strong>Control</strong> — track evidence, behaviors, sanity, guesses, votes, and contract result.</li>
  <li><strong>Overlay</strong> — add the overlay URL to OBS as a browser source.</li>
  <li><strong>End Session</strong> — close the room when the group is done playing.</li>
</ol>
<h2>Streamer.bot</h2>
<p>Streamer.bot setup is a one-time integration. After that, changing rooms should usually only require updating the <code>phasmoRoom</code> variable.</p>
<div class="button-row"><a class="button" href="/phasmo/streamerbot">Streamer.bot setup</a><a class="button" href="/phasmo/commands">Viewer commands</a></div>
<h2>Public beta expectations</h2>
<p>This is an early public beta tool. Daily maintenance/update windows may happen while bugs are fixed and the release workflow stabilizes.</p>
<p class="small">Do not put private information in room names. Room names may be visible on Active Rooms.</p>
"""
    return _simple_info_page("Getting Started", body, safe_room)


@router.get("/phasmo/commands")
def phasmo_commands(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "kaizen")
    body = f"""
<p>Viewer commands let chat participate without cluttering the streamer control screen. Availability can depend on the room config and Streamer.bot setup.</p>
<h2>Lucky guesses</h2>
<table><tbody>
<tr><td><code>!guess Deogen</code></td><td>Make a lucky ghost prediction.</td></tr>
<tr><td><code>!unguess</code></td><td>Remove your current lucky guess.</td></tr>
<tr><td><code>!guesses</code></td><td>Show current lucky guesses.</td></tr>
</tbody></table>
<h2>Decision votes</h2>
<table><tbody>
<tr><td><code>!vote Wraith</code></td><td>Vote when chat is helping the streamer choose.</td></tr>
<tr><td><code>!unvote</code></td><td>Remove your current vote.</td></tr>
<tr><td><code>!votes</code></td><td>Show current decision votes.</td></tr>
</tbody></table>
<h2>Evidence and behavior helpers</h2>
<table><tbody>
<tr><td><code>!ev orbs yes</code></td><td>Mark evidence as confirmed.</td></tr>
<tr><td><code>!ev freezing no</code></td><td>Mark evidence as ruled out.</td></tr>
<tr><td><code>!beh 12 yes</code></td><td>Mark a numbered behavior as observed.</td></tr>
<tr><td><code>!be 12 no</code></td><td>Mark a numbered behavior as ruled out.</td></tr>
</tbody></table>
<h2>Round result</h2>
<table><tbody>
<tr><td><code>!result Deogen</code></td><td>Confirm the actual ghost after the contract ends and score guesses.</td></tr>
<tr><td><code>!actual Deogen</code></td><td>Alias for confirming the actual ghost.</td></tr>
</tbody></table>
<h2>Streamer/mod setup commands</h2>
<table><tbody>
<tr><td><code>!phasmo-room kaizen</code></td><td>Set the remembered default room for the channel/bot profile.</td></tr>
<tr><td><code>!phasmo room kaizen</code></td><td>Alias for setting the default room.</td></tr>
</tbody></table>
<p class="small">For locked rooms, Streamer.bot command calls must include the room code or a future trusted-channel token. This prevents chat command endpoints from bypassing room protection.</p>
<div class="button-row"><a class="button" href="/phasmo/streamerbot">Streamer.bot setup</a></div>
"""
    return _simple_info_page("Viewer Commands", body, safe_room)


@router.get("/phasmo/privacy")
def phasmo_privacy(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "default")
    body = f"""
<p>This is a lightweight privacy note for the Phasmo Helper public beta.</p>
<h2>What the tool may store</h2>
<ul>
  <li>Room names, room settings, evidence state, guesses, votes, and contract results.</li>
  <li>Streamer/channel names when provided for Streamer.bot or support opt-in.</li>
  <li>Viewer display names submitted through guesses, votes, commands, bug reports, or feedback.</li>
  <li>Bug reports, contact info entered into the bug form, and internal triage notes.</li>
</ul>
<h2>What not to enter</h2>
<p>Do not enter private personal information, passwords you reuse elsewhere, addresses, payment details, or sensitive information into room names, notes, bug reports, or commands.</p>
<h2>Public visibility</h2>
<p>Room names may appear on Active Rooms. Keep room names stream-safe and avoid private information.</p>
<h2>Support and abuse handling</h2>
<p>Kaizen Controller may review bug reports, support pings, and room metadata to fix issues, prevent abuse, and keep hosting costs manageable.</p>
<div class="button-row"><a class="button" href="/phasmo/data-retention">Data retention</a><a class="button" href="/phasmo/terms">Terms</a></div>
"""
    return _simple_info_page("Privacy", body, safe_room)


@router.get("/phasmo/terms")
def phasmo_terms(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "default")
    body = f"""
<p>Phasmo Helper is a fan-made stream helper and public beta tool provided as-is.</p>
<h2>Use expectations</h2>
<ul>
  <li>Use stream-safe room names and public notes.</li>
  <li>Do not use slurs, harassment, impersonation, explicit content, URLs, or spam in public room names.</li>
  <li>Do not attack, scrape, overload, or intentionally disrupt the service.</li>
  <li>Do not rely on this tool as the source of truth for game outcomes; confirm contract results in-game.</li>
</ul>
<h2>Moderation</h2>
<p>Kaizen Controller may close, hide, or remove abusive rooms, bug reports, or usage patterns to protect the tool, the community, and hosting costs.</p>
<h2>No warranty</h2>
<p>The tool may have bugs, temporary downtime, scheduled maintenance, or data loss during beta. It is provided free for community use.</p>
<div class="button-row"><a class="button" href="/phasmo/privacy">Privacy</a><a class="button" href="/phasmo/data-retention">Data retention</a></div>
"""
    return _simple_info_page("Terms", body, safe_room)


@router.get("/phasmo/data-retention")
def phasmo_data_retention(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "default")
    body = f"""
<p>These are the intended public-beta retention rules for Phasmo Helper.</p>
<h2>Current defaults</h2>
<ul>
  <li><strong>Inactive open rooms:</strong> expire from Active Rooms after about 4 hours without updates.</li>
  <li><strong>Closed sessions:</strong> may be kept for a short period to preserve recent results and troubleshooting context.</li>
  <li><strong>Leaderboards:</strong> may be retained longer so scoring history is useful.</li>
  <li><strong>Bug reports:</strong> retained until reviewed, fixed, exported, or cleaned up.</li>
  <li><strong>Support pings:</strong> retained short-term for support and abuse prevention.</li>
</ul>
<h2>Persistence note</h2>
<p>Until persistent Railway storage or a database is configured, app data may depend on the current deployment filesystem and should be treated as beta data.</p>
<h2>Export/import</h2>
<p>The Dev Admin bug tracker supports JSON export/import so issue history can survive builds and storage changes.</p>
<div class="button-row"><a class="button" href="/phasmo/privacy">Privacy</a><a class="button" href="/phasmo/terms">Terms</a></div>
"""
    return _simple_info_page("Data Retention", body, safe_room)


@router.get("/phasmo/bug-report")
def phasmo_bug_report(room: str | None = Query(default=None)):
    safe_room = _room_name(room or "default")
    html_doc = f"""<!doctype html>
<html lang=\"en\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>Bug Reports - Kaizen Phasmo Helper</title><style>{_public_page_style()}</style></head>
<body><main>
{_site_banner_html()}
<section class=\"hero\"><a class=\"brand brand-link\" href=\"/phasmo\"><div class=\"logo\">KC</div><div class=\"brandcopy\"><div class=\"kicker\">Kaizen Phasmo Helper</div><h1>Bug Reports</h1></div></a><p>Send corrections, broken commands, confusing behavior, or feature ideas.</p></section>
<section class=\"card\"><div class=\"head\"><h2>Fix Request</h2><span class=\"muted\">room: {safe_room}</span></div><div class=\"body\"><form id=\"bugForm\" class=\"form-grid\"><input name=\"name\" placeholder=\"Name / Twitch username\"><input name=\"contact\" placeholder=\"Optional contact info\"><select name=\"category\"><option value=\"bug\">Bug</option><option value=\"feature\">Feature request</option><option value=\"correction\">Correction</option><option value=\"other\">Other</option></select><input name=\"room\" value=\"{safe_room}\" placeholder=\"Room name\"><textarea name=\"message\" required placeholder=\"What happened? What should it have done instead?\"></textarea><button class=\"primary\" type=\"submit\">Send Report</button></form><div id=\"bugStatus\" class=\"status\"></div></div></section>
{_support_footer(safe_room)}
</main><script>
document.getElementById('bugForm').addEventListener('submit',async(e)=>{{e.preventDefault();const data=Object.fromEntries(new FormData(e.target).entries());data.pageUrl=location.href;const r=await fetch('/api/phasmo/bug-report',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});document.getElementById('bugStatus').textContent=r.ok?'Thanks — report saved.':'Report failed to save.';if(r.ok)e.target.reset();}});
</script></body></html>"""
    return HTMLResponse(html_doc)


@router.get("/phasmo/rooms")
def phasmo_rooms():
    rooms = active_room_summaries()
    cards = ""
    for item in rooms:
        room = html.escape(str(item.get("room") or "default"))
        ghost = html.escape(str(item.get("confirmedGhost") or "pending"))
        locked = "<span class='locked'>locked</span> • " if item.get("locked") else ""
        cards += f"""
        <article class=\"room-card\"><div><strong>{room}</strong><span>{locked}{'active' if item.get('setupComplete') else 'setup'}{' • support welcome' if item.get('supportOptIn') else ''} • updated {item.get('ageMinutes')}m ago</span></div><p>{html.escape(str(item.get('map') or 'unknown'))} • {html.escape(str(item.get('difficulty') or 'unknown'))} • guesses {item.get('guesses',0)} • votes {item.get('votes',0)} • result {ghost}</p><div><a href=\"/phasmo/control?room={room}\">Open</a><a href=\"/phasmo/leaderboard?room={room}\">Leaderboard</a></div></article>
        """
    if not cards:
        cards = "<p class='muted'>No active rooms. Rooms expire after 4 hours without updates.</p>"
    body = f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>Active Rooms - Kaizen Phasmo Helper</title><style>{_public_page_style()}</style></head><body><main>{_site_banner_html()}<section class=\"hero\"><a class=\"brand brand-link\" href=\"/phasmo\"><div class=\"logo\">KC</div><div class=\"brandcopy\"><div class=\"kicker\">Kaizen Phasmo Helper</div><h1>Active Rooms</h1></div></a><p>Rooms disappear after 4 hours without updates so old lobbies do not pile up.</p><div class=\"actions\"><a class=\"button primary\" href=\"/phasmo/room\">Create Room</a><a class=\"button\" href=\"/phasmo\">Home</a></div></section><section class=\"card\"><div class=\"head\"><h2>Lobbies</h2><span class=\"muted\">{len(rooms)} active</span></div><div class=\"body\"><div class=\"room-grid\">{cards}</div></div></section>{_support_footer('default')}</main></body></html>"""
    return HTMLResponse(body)


def _simple_info_page(title: str, body: str, room: str = "default") -> HTMLResponse:
    """Render static/help pages without room status chrome.

    These pages are evergreen docs/policy pages, so they should not imply the
    visitor is inside a specific active room or setup flow.
    """
    safe_room = _room_name(room or "default")
    html_doc = f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\" /><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" /><title>{html.escape(title)} - Phasmo Helper</title><style>{_public_page_style()}</style></head><body><main>{_site_banner_html()}<section class=\"hero static-hero\"><a class=\"brand-link\" href=\"/phasmo\" aria-label=\"Return to Phasmo Helper home\"><div class=\"logo\">KC</div><div class=\"brandcopy\"><div class=\"kicker\">Kaizen Controller Tools</div><h1>{html.escape(title)}</h1><div class=\"muted page-title-note\">Phasmo Helper</div></div></a><div class=\"actions\"><a class=\"button\" href=\"/phasmo\">Home</a></div></section><section class=\"card\"><div class=\"body content\">{body}</div></section>{_support_footer(safe_room)}</main></body></html>"""
    return HTMLResponse(html_doc)


@router.get("/phasmo/release-notes")
def phasmo_release_notes(room: str | None = Query(default=None)):
    safe_room = _room_name(room)
    body = f"""
<p class="small">Release notes are updated with each packaged build so testers can see what changed without checking GitHub.</p>
<h2>v5.5.2 — Static Page Layout and Footer Cleanup</h2>
<ul>
  <li><strong>Fixed:</strong> Static help and policy pages no longer show room/session status in their headers.</li>
  <li><strong>Fixed:</strong> Getting Started and Terms page spacing so buttons no longer collide with the next section.</li>
  <li><strong>Changed:</strong> Footer links are simplified and grouped for mobile readability.</li>
  <li><strong>Changed:</strong> Removed duplicate and low-priority footer links from the always-visible footer.</li>
  <li><strong>Changed:</strong> Default app version updated to <code>v5.5.2</code>.</li>
</ul>
<h2>v5.5.1 — Homepage and Release Notes Cleanup</h2>
<ul>
  <li><strong>Fixed:</strong> Simplified the home page so Create Room is the clear primary action.</li>
  <li><strong>Fixed:</strong> Updated the visible Release Notes page with the v5.5 and v5.5.1 entries.</li>
  <li><strong>Added:</strong> App version now appears in the footer on public/helper pages.</li>
  <li><strong>Changed:</strong> Secondary links such as Leaderboard, Streamer.bot Setup, Config, Privacy, and Terms stay in footer/support navigation instead of crowding the hero card.</li>
  <li><strong>Changed:</strong> Default app version updated to <code>v5.5.1</code>.</li>
</ul>
<h2>v5.5 — Public Beta Help and Policy Pages</h2>
<ul>
  <li><strong>Added:</strong> Getting Started page for new streamers and testers.</li>
  <li><strong>Added:</strong> Viewer Commands page covering guesses, votes, evidence, behavior, result, and room routing commands.</li>
  <li><strong>Added:</strong> Privacy, Terms, and Data Retention pages for public-beta usage expectations.</li>
  <li><strong>Changed:</strong> Home page and footer now link to the new user-facing help and policy pages.</li>
  <li><strong>Changed:</strong> Default app version updated to <code>v5.5</code>.</li>
  <li><strong>Maintenance:</strong> Build package excludes Python cache files so staged release commits stay cleaner.</li>
</ul>
<h2>v5.4.1 — Dev Admin Privacy and Release Setup Cleanup</h2>
<ul>
  <li><strong>Fixed:</strong> Dev Admin tools now stay hidden until the admin code is accepted.</li>
  <li><strong>Added:</strong> Dev Admin bootstrap check so banner, maintenance, and tracker data are loaded only after unlock.</li>
  <li><strong>Added:</strong> Maintenance / Release Automation test controls on the Dev Admin page.</li>
  <li><strong>Changed:</strong> Release automation docs now call out that the <code>release</code> branch must be created and pushed once before GitHub can show or deploy it.</li>
  <li><strong>Changed:</strong> Default app version updated to <code>v5.4.1</code>.</li>
</ul>
<h2>v5.4 — Scheduled Release / Maintenance Automation</h2>
<ul>
  <li><strong>Added:</strong> Protected ops endpoints for GitHub Actions: health, version, maintenance start/end, and banner control.</li>
  <li><strong>Added:</strong> <code>PHASMO_OPS_TOKEN</code> support for CI/CD automation.</li>
  <li><strong>Added:</strong> GitHub Actions scheduled release workflow for the 9 PM Pacific maintenance window.</li>
  <li><strong>Added:</strong> Discord maintenance/deployment notice support through GitHub Secrets.</li>
  <li><strong>Added:</strong> Maintenance mode can temporarily make the app read-only and pause new room creation.</li>
  <li><strong>Changed:</strong> Acknowledgements now list play testers as clickable links, with project-owner credit removed from the list.</li>
</ul>
<h2>v5.3 — Public Beta Hardening</h2>
<ul>
  <li><strong>Fixed:</strong> Locked rooms require passcode access for room pages, reads, writes, and Streamer.bot commands.</li>
  <li><strong>Added:</strong> End Session / Close Room flow.</li>
  <li><strong>Added:</strong> Button guardrails for Next Round, Reset Current Round, End Session, and destructive actions.</li>
  <li><strong>Added:</strong> Room-name validation/content filtering for public Active Rooms.</li>
  <li><strong>Added:</strong> Dev Admin bug tracker table with triage fields and JSON export/import.</li>
  <li><strong>Added:</strong> Editable safety-orange public banner.</li>
  <li><strong>Added:</strong> Overlay remaining-ghost news reel.</li>
  <li><strong>Fixed:</strong> Header/home link behavior and Round Setup navigation.</li>
</ul>
<h2>Earlier Development Notes</h2>
<ul>
  <li>Added multi-room/session support for parallel groups.</li>
  <li>Added setup fields for room/session name and number of players.</li>
  <li>Changed Quick Timers into Quick Trackers.</li>
  <li>Added team sanity tracking and hunt-trigger logging.</li>
  <li>Moved witnessed model/name clue tracking into Behavior Branches.</li>
  <li>Added separate <span class="badge">!guess</span> and <span class="badge">!vote</span> boards.</li>
  <li>Added numbered behavior entries with <span class="badge">!be # yes/no</span> support.</li>
  <li>Expanded loading-screen cards, cursed possession helper, and location hints.</li>
</ul>
<p><a href="/phasmo/acknowledgements?room={safe_room}">View acknowledgements</a></p>
<p class="small"><a href="/phasmo/config?room={safe_room}">Configuration</a> • <a href="https://drive.google.com/drive/folders/1n7jfz7QGnkPUj3fQ715420cKHW96W97I" target="_blank" rel="noopener">User manual and support files</a></p>
"""
    return _simple_info_page("Release Notes", body, safe_room)


@router.get("/phasmo/acknowledgements")
def phasmo_acknowledgements(room: str | None = Query(default=None)):
    safe_room = _room_name(room)
    body = f"""
<p>This tool exists because people test it, break it, correct it, and suggest better ways to make it useful during real play.</p>
<h2>Play Testers</h2>
<ul>
  <li><strong><a href="https://twitch.tv/sheikhyabootie" target="_blank" rel="noopener">SheikYaBootie</a></strong></li>
  <li><strong><a href="https://twitch.tv/imestrellas" target="_blank" rel="noopener">imestrellas</a></strong></li>
  <li><strong><a href="https://twitch.tv/Cybertraz" target="_blank" rel="noopener">Cybertraz</a></strong></li>
  <li><strong><a href="https://www.twitch.tv/xmysticalnerissa" target="_blank" rel="noopener">xmysticalnerissa</a></strong></li>
</ul>
<h2>Media / Asset Credits</h2>
<ul>
  <li><strong><a href="https://www.youtube.com/watch?v=l4SFiMrYplM" target="_blank" rel="noopener">Jumpscare video source / creator</a></strong> — video used for the optional “Don’t press this button” gag.</li>
  <li><a href="https://pixabay.com/illustrations/clown-horror-scary-royalty-free-stock-7280647/" target="_blank" rel="noopener"><strong>DangrafArt / Pixabay</strong></a> — clown image used for the optional “Don’t press this button” gag.</li>
  <li><a href="https://pixabay.com/sound-effects/fuzzy-jumpscare-80560/" target="_blank" rel="noopener"><strong>freesound_community / Pixabay</strong></a> — “Fuzzy Jumpscare” sound effect used for the optional “Don’t press this button” gag.</li>
</ul>
<h2>Community Contributors</h2>
<p>Thanks to everyone submitting bug reports, cursed possession corrections, ghost behavior notes, overlay readability feedback, and command ideas.</p>
<h2>Want to Support Development?</h2>
<p>This helper is happily provided free for the Phasmophobia community. Optional donations help cover hosting and support further development.</p>
<p><a href="https://ko-fi.com/kaizencontroller" target="_blank" rel="noopener">Support development on Ko-fi</a></p>
<p><a href="https://drive.google.com/drive/folders/1n7jfz7QGnkPUj3fQ715420cKHW96W97I" target="_blank" rel="noopener">User manual and support files</a></p>
<p class="small"><a href="/phasmo/release-notes?room={safe_room}">View release notes</a></p>
"""
    return _simple_info_page("Acknowledgements", body, safe_room)


@router.get("/phasmo/config")
def phasmo_config(room: str | None = Query(default=None), token: str | None = Query(default=None), code: str | None = Query(default=None)):
    safe_room = _room_name(room)
    gate = _locked_room_gate(safe_room, "/phasmo/config", code)
    if gate:
        return gate
    state = read_state(safe_room)
    rows = ""
    config = _read_config()
    for key, (label, desc) in CONFIG_DESCRIPTIONS.items():
        checked = "checked" if config.get(key) else ""
        rows += f"""
        <label class="toggle-row">
          <span><strong>{label}</strong><small>{desc}</small><code>{key}</code></span>
          <input class="global-toggle" type="checkbox" data-key="{key}" {checked}>
        </label>
        """
    def mode_checked(key: str, value: str) -> str:
        return "checked" if str(state.get(key) or "helper") == value else ""
    support_checked = "checked" if state.get("supportOptIn") else ""
    support_channel = html.escape(str(state.get("supportChannel") or ""))
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Phasmo Helper Config</title>
<style>{_public_page_style()}
.switch-row{{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid #334155}}
.switch-row strong{{display:block}}
.switch-row small{{display:block;color:#94a3b8;margin-top:3px;line-height:1.35}}
.segmented{{display:inline-grid;grid-template-columns:1fr 1fr;background:#020617;border:1px solid #334155;border-radius:999px;padding:3px;gap:3px}}
.segmented label{{position:relative;display:block}}
.segmented input{{position:absolute;opacity:0;pointer-events:none}}
.segmented span{{display:block;border-radius:999px;padding:7px 10px;color:#94a3b8;font-size:12px;font-weight:900;white-space:nowrap}}
.segmented input:checked + span{{background:#14532d;border:1px solid #22c55e;color:#dcfce7}}
.toggle-row{{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center;padding:12px 0;border-bottom:1px solid #334155}}
.toggle-row:last-child,.switch-row:last-child{{border-bottom:0}}
.toggle-row strong{{display:block;font-size:14px}}
.toggle-row small{{display:block;color:#94a3b8;line-height:1.35;margin-top:3px}}
.toggle-row code{{display:inline-block;margin-top:5px;color:#bae6fd;background:#020617;border:1px solid #334155;border-radius:999px;padding:2px 7px;font-size:11px}}
input[type=checkbox].global-toggle{{width:52px;height:30px;accent-color:#22c55e}}
.status{{color:#93c5fd;font-size:13px;margin-top:8px}}
.err{{color:#fecaca}}
</style>
</head>
<body><main>
{_site_banner_html()}
<section class="hero"><a href="/phasmo" style="text-decoration:none;color:#f8fafc"><div class="brand"><div class="logo">KC</div><div class="brandcopy"><div class="kicker">room: {safe_room}</div><h1>Config</h1></div></div></a><p>Use this page for room/tool behavior. Contract-specific details stay on Round Setup.</p><div class="actions"><a class="button" id="configRoundLink" href="/phasmo/round?room={safe_room}">Round Setup</a><a class="button" id="configControlLink" href="/phasmo/control?room={safe_room}">Control</a><a class="button" href="/phasmo">Home</a></div></section>
<section class="card"><div class="head"><h2>Display Modes</h2><span class="muted">room-level</span></div><div class="body">
  <div class="switch-row"><span><strong>Control Screen Mode</strong><small>Helper shows next-best-test suggestions. Tracker hides those suggestions and behaves more like a shared evidence board.</small></span><span class="segmented"><label><input type="radio" name="controlMode" value="helper" {mode_checked('controlMode','helper')}><span>Helper</span></label><label><input type="radio" name="controlMode" value="tracker" {mode_checked('controlMode','tracker')}><span>Tracker</span></label></span></div>
  <div class="switch-row"><span><strong>Overlay Mode</strong><small>Helper overlay suggests the next test. Tracker overlay shows simplified game state.</small></span><span class="segmented"><label><input type="radio" name="overlayMode" value="helper" {mode_checked('overlayMode','helper')}><span>Helper</span></label><label><input type="radio" name="overlayMode" value="tracker" {mode_checked('overlayMode','tracker')}><span>Tracker</span></label></span></div>
  <div id="roomStatus" class="status">Ready.</div>
</div></section>
<section class="card"><div class="head"><h2>Support Opt-In</h2><span class="muted">optional</span></div><div class="body">
  <label class="toggle-row"><span><strong>Invite KaizenController support drop-ins</strong><small>Opt-in only. If Streamer.bot commands come through, this can flag the room as open for help/testing.</small></span><input class="global-toggle" type="checkbox" id="supportOptIn" {support_checked}></label>
  <label style="display:grid;gap:5px;margin-top:10px"><span class="muted">Streamer / Channel Name</span><input id="supportChannel" value="{support_channel}" placeholder="optional Twitch channel"></label>
  <div id="supportStatus" class="status">Ready.</div>
</div></section>
<section class="card"><div class="head"><h2>Command Permissions</h2><span class="muted">global</span></div><div class="body">{rows}<div id="globalStatus" class="status">Ready.</div></div></section>
{_support_footer(safe_room)}
</main>
<script>
const room='{safe_room}';
const initialCode='{html.escape(str(code or ""))}';
function cleanCode(raw){{return (raw||'').replace(/[^0-9]/g,'').slice(0,4)}}
function codeKey(){{return 'phasmoRoomCode:'+room}}
if(cleanCode(initialCode).length===4)localStorage.setItem(codeKey(),cleanCode(initialCode));
function codeSuffix(){{const code=cleanCode(localStorage.getItem(codeKey())||initialCode); return code.length===4?'&code='+encodeURIComponent(code):''}}
function rememberCode(raw){{const code=cleanCode(raw); if(code.length===4)localStorage.setItem(codeKey(),code); return code}}
function updateConfigLinks(){{document.getElementById('configRoundLink').href='/phasmo/round?room='+encodeURIComponent(room)+codeSuffix();document.getElementById('configControlLink').href='/phasmo/control?room='+encodeURIComponent(room)+codeSuffix();}}
updateConfigLinks();
async function saveRoomPatch(patch){{
  const status=document.getElementById('roomStatus'); if(status)status.textContent='Saving...';
  let r=await fetch('/api/phasmo/state?room='+encodeURIComponent(room)+codeSuffix(),{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(patch)}});
  if(r.status===403){{const entered=prompt('This room is locked. Enter the 4-digit room passcode.'); if(rememberCode(entered).length===4){{updateConfigLinks(); r=await fetch('/api/phasmo/state?room='+encodeURIComponent(room)+codeSuffix(),{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(patch)}});}}}}
  if(!r.ok){{if(status){{status.className='status err';status.textContent='Save blocked. The room passcode was not accepted.';}} return false;}}
  if(status){{status.className='status';status.textContent='Saved.';}}
  return true;
}}
document.querySelectorAll('input[name="controlMode"]').forEach(el=>el.addEventListener('change',()=>saveRoomPatch({{controlMode:el.value}})));
document.querySelectorAll('input[name="overlayMode"]').forEach(el=>el.addEventListener('change',()=>saveRoomPatch({{overlayMode:el.value}})));
document.getElementById('supportOptIn').addEventListener('change',e=>{{document.getElementById('supportStatus').textContent='Saving...';saveRoomPatch({{supportOptIn:e.target.checked}}).then(ok=>document.getElementById('supportStatus').textContent=ok?'Saved.':'Save failed.')}});
document.getElementById('supportChannel').addEventListener('change',e=>{{document.getElementById('supportStatus').textContent='Saving...';saveRoomPatch({{supportChannel:e.target.value}}).then(ok=>document.getElementById('supportStatus').textContent=ok?'Saved.':'Save failed.')}});
async function saveGlobal(key,val){{
  const status=document.getElementById('globalStatus'); status.className='status'; status.textContent='Saving...';
  const r=await fetch('/api/phasmo/config',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{[key]:val}})}});
  if(!r.ok){{status.className='status err';status.textContent='Save blocked. Please try again.'; return;}}
  const data=await r.json(); status.textContent='Saved. '+key+' = '+(data.config[key]?'on':'off');
}}
document.querySelectorAll('[data-key]').forEach(el=>el.addEventListener('change',()=>saveGlobal(el.dataset.key,el.checked)));
</script>
</body></html>"""
    return HTMLResponse(html_doc)


@router.get("/phasmo/room")
def phasmo_room_setup(room: str | None = Query(default=None), code: str | None = Query(default=None)):
    # Room creation/setup remains available. If the room already exists and is locked, gate it.
    if room:
        return _room_gate_or_template(room, code, "/phasmo/room", "room")
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "room"))


@router.get("/phasmo/setup-room")
def phasmo_setup_room_alias(room: str | None = Query(default=None), code: str | None = Query(default=None)):
    if room:
        return _room_gate_or_template(room, code, "/phasmo/setup-room", "room")
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "room"))


@router.get("/phasmo/round")
def phasmo_round_setup(room: str | None = Query(default=None), code: str | None = Query(default=None)):
    return _room_gate_or_template(room, code, "/phasmo/round", "setup")


@router.get("/phasmo/setup")
def phasmo_setup_alias(room: str | None = Query(default=None), code: str | None = Query(default=None)):
    return _room_gate_or_template(room, code, "/phasmo/setup", "setup")


@router.get("/phasmo/control")
def phasmo_control(room: str | None = Query(default=None), code: str | None = Query(default=None), token: str | None = Query(default=None)):
    safe_room = _room_name(room)
    gate = _locked_room_gate(safe_room, "/phasmo/control", code)
    if gate:
        return gate
    state = read_state(safe_room)
    if not state.get("setupComplete"):
        suffix = f"?room={safe_room}" + (f"&code={code}" if code else "")
        return RedirectResponse(f"/phasmo/round{suffix}")
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "control"))


@router.get("/phasmo/overlay")
def phasmo_overlay(room: str | None = Query(default=None), code: str | None = Query(default=None)):
    return _room_gate_or_template(room, code, "/phasmo/overlay", "overlay")




@router.get("/phasmo/leaderboard")
def phasmo_leaderboard(room: str | None = Query(default=None), code: str | None = Query(default=None), token: str | None = Query(default=None)):
    safe_room = _room_name(room)
    gate = _locked_room_gate(safe_room, "/phasmo/leaderboard", code)
    if gate:
        return gate
    state = read_state(safe_room)
    result = state.get("contractResult") or {}
    confirmed_ghost = result.get("confirmedGhost")
    board = _read_leaderboard()
    history = board.get("history") or []
    local_history = [item for item in history if item.get("room") == safe_room]

    def status_cell(ghost: str, correct: bool | None) -> str:
        if correct is True:
            return "<span class='good'>correct</span>"
        if correct is False:
            return "<span class='bad'>debunked</span>"
        if confirmed_ghost:
            return "<span class='bad'>debunked</span>" if ghost != confirmed_ghost else "<span class='good'>correct</span>"
        return "<span class='muted'>pending result</span>"

    def make_session_rows(source: dict[str, str], empty_text: str) -> str:
        rows = ""
        for user, ghost in sorted((source or {}).items(), key=lambda item: (str(item[1]), str(item[0]))):
            correctness = None if not confirmed_ghost else (ghost == confirmed_ghost)
            rows += f"<tr><td>{html.escape(str(user))}</td><td>{html.escape(str(ghost))}</td><td>{status_cell(str(ghost), correctness)}</td></tr>"
        if not rows:
            rows = f"<tr><td colspan='3'>{empty_text}</td></tr>"
        return rows

    def aggregate(history_items: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        players: Dict[str, Dict[str, Any]] = {}
        for item in history_items:
            confirmed = item.get("confirmedGhost")
            if not confirmed:
                continue
            for user, ghost in (item.get("guesses") or {}).items():
                username = _normal_user(str(user))
                row = players.setdefault(username, {
                    "guessTotal": 0, "guessCorrect": 0, "guessWrong": 0,
                    "voteTotal": 0, "voteCorrect": 0, "voteWrong": 0,
                    "points": 0, "lastCorrectAt": 0,
                })
                row["guessTotal"] += 1
                if ghost == confirmed:
                    row["guessCorrect"] += 1
                    row["points"] += 3
                    row["lastCorrectAt"] = max(int(row.get("lastCorrectAt") or 0), int(item.get("confirmedAt") or 0))
                else:
                    row["guessWrong"] += 1
            for user, ghost in (item.get("votes") or {}).items():
                username = _normal_user(str(user))
                row = players.setdefault(username, {
                    "guessTotal": 0, "guessCorrect": 0, "guessWrong": 0,
                    "voteTotal": 0, "voteCorrect": 0, "voteWrong": 0,
                    "points": 0, "lastCorrectAt": 0,
                })
                row["voteTotal"] += 1
                if ghost == confirmed:
                    row["voteCorrect"] += 1
                    row["points"] += 1
                    row["lastCorrectAt"] = max(int(row.get("lastCorrectAt") or 0), int(item.get("confirmedAt") or 0))
                else:
                    row["voteWrong"] += 1
        for stats in players.values():
            gt = int(stats.get("guessTotal") or 0)
            gc = int(stats.get("guessCorrect") or 0)
            vt = int(stats.get("voteTotal") or 0)
            vc = int(stats.get("voteCorrect") or 0)
            guess_accuracy = (gc / gt) if gt else 0.0
            vote_accuracy = (vc / vt) if vt else 0.0
            stats["guessAccuracy"] = guess_accuracy
            stats["voteAccuracy"] = vote_accuracy
            # Confidence-adjusted ranking: enough volume matters, but 8/10 should outrank 24/240.
            stats["rankScore"] = (guess_accuracy * min(1.0, gt / 10.0)) + (vote_accuracy * 0.05)
        return players

    def make_leaderboard_rows(history_items: list[Dict[str, Any]], empty_text: str) -> str:
        players = aggregate(history_items)
        rows = ""
        def sort_key(item):
            user, stats = item
            return (-(float(stats.get("rankScore") or 0)), -(int(stats.get("guessCorrect") or 0)), int(stats.get("guessTotal") or 0), user)
        for rank, (user, stats) in enumerate(sorted(players.items(), key=sort_key)[:50], start=1):
            gt = int(stats.get("guessTotal") or 0)
            gc = int(stats.get("guessCorrect") or 0)
            gw = int(stats.get("guessWrong") or 0)
            vt = int(stats.get("voteTotal") or 0)
            vc = int(stats.get("voteCorrect") or 0)
            vw = int(stats.get("voteWrong") or 0)
            acc = f"{(gc / gt) * 100:.1f}%" if gt else "—"
            precision = f"{float(stats.get('rankScore') or 0) * 100:.1f}"
            rows += f"<tr><td>{rank}</td><td>{html.escape(str(user))}</td><td>{gc}</td><td>{gt}</td><td>{acc}</td><td>{precision}</td><td>{gw}</td><td>{vc}/{vt}</td><td>{vw}</td></tr>"
        if not rows:
            rows = f"<tr><td colspan='9'>{empty_text}</td></tr>"
        return rows

    session_guess_rows = make_session_rows(state.get("guesses", {}) or {}, "No lucky guesses yet. Viewers can use <strong>!guess GhostName</strong>.")
    session_vote_rows = make_session_rows(state.get("votes", {}) or {}, "No decision votes yet. Use <strong>!vote GhostName</strong> when chat is helping make a call.")
    local_rows = make_leaderboard_rows(local_history, "No scored rounds for this room yet.")
    global_rows = make_leaderboard_rows(history, "No scored rounds yet. Confirm the actual ghost after a contract to start the leaderboard.")
    control_url = f"/phasmo/control?room={safe_room}"
    setup_url = f"/phasmo/round?room={safe_room}"
    overlay_url = f"/phasmo/overlay?room={safe_room}"
    rooms_url = "/phasmo/rooms"
    is_ready = bool(state.get("setupComplete"))
    home_url = control_url if is_ready else setup_url
    home_label = "Back to Control" if is_ready else "Back to Setup"
    mode_label = "active run" if is_ready else "setup needed"
    confirmed_line = f"Actual ghost confirmed: <strong>{html.escape(str(confirmed_ghost))}</strong>. Lucky guesses: <strong>{int(result.get('correctGuesses') or 0)}</strong> correct, <strong>{int(result.get('wrongGuesses') or 0)}</strong> debunked." if confirmed_ghost else "Actual ghost not confirmed yet. Use the Contract Result panel in Control after the game reveals the real ghost."
    history_count = len(history)
    local_count = len(local_history)
    html_doc = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Phasmo Chat Board</title>
        <style>
          body {{ margin:0; background:#000; color:#f8fafc; font-family:Inter,system-ui,Segoe UI,sans-serif; }}
          .app {{ width:min(460px,100vw); padding:10px; display:grid; gap:10px; margin:0 auto; }}
          .panel {{ background:#172235ee; border:1px solid #334155; border-radius:16px; overflow:hidden; box-shadow:0 16px 40px #0007; }}
          .head {{ padding:14px; border-bottom:1px solid #334155; display:flex; justify-content:space-between; gap:8px; align-items:center; flex-wrap:wrap; }}
          .body {{ padding:14px; }}
          a {{ color:#38bdf8; }}
          .muted {{ color:#94a3b8; font-size:12px; }}
          .good {{ color:#86efac; font-weight:900; }}
          .bad {{ color:#fca5a5; font-weight:900; }}
          table {{ width:100%; border-collapse:collapse; }}
          th,td {{ border-bottom:1px solid #334155; padding:10px; text-align:left; vertical-align:top; }}
          th {{ color:#94a3b8; font-size:12px; text-transform:uppercase; letter-spacing:.12em; }}
          .badge {{ border:1px solid #334155; background:#0f172a; border-radius:999px; padding:6px 9px; font-size:12px; display:inline-block; margin:3px; text-decoration:none; }}
          .brandbar {{ display:grid; grid-template-columns:1fr auto; align-items:center; gap:14px; background:linear-gradient(135deg,#172235ee,#0f172aee); border:1px solid #334155; border-radius:18px; box-shadow:0 18px 50px #0008; padding:12px 14px; text-decoration:none; color:#f8fafc; }}
          .brandleft {{ display:flex; align-items:center; gap:12px; min-width:0; }}
          .logo {{ width:48px; height:48px; border-radius:16px; background:radial-gradient(circle at 30% 20%,#38bdf855,transparent 38%),linear-gradient(135deg,#0f172a,#1e293b); border:1px solid #475569; display:grid; place-items:center; box-shadow:inset 0 0 22px #ffffff12; flex:0 0 auto; }}
          .logo span {{ font-weight:950; letter-spacing:-.08em; color:#fff; text-shadow:0 2px 0 #000; }}
          .brandtitle {{ font-size:18px; font-weight:950; line-height:1.05; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
          .brandsub {{ font-size:12px; color:#94a3b8; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
          .brandcta {{ border:1px solid #475569; background:#0f172a; border-radius:999px; padding:8px 11px; color:#bfdbfe; font-size:12px; font-weight:850; white-space:nowrap; }}
          .twocol {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
          .note {{ border:1px solid #334155; background:#0f172a; border-radius:12px; padding:10px; color:#cbd5e1; font-size:13px; line-height:1.35; }}
          @media(max-width:800px){{ .app{{padding:12px}} .twocol{{grid-template-columns:1fr}} table{{font-size:12px}} th,td{{padding:8px 6px}} .brandbar{{grid-template-columns:1fr}} }}
        </style>
      </head>
      <body>
        <main class="app">
          <a class="brandbar" href="/phasmo" aria-label="Return to Phasmo Helper home">
            <span class="brandleft"><span class="logo"><span>KC</span></span><span><span class="brandtitle">Kaizen Phasmo Helper</span><br><span class="brandsub">room: {safe_room} • {mode_label}</span></span></span>
            <span class="brandcta">{home_label}</span>
          </a>
          <section class="panel">
            <div class="head"><div><strong>Phasmo Chat Board</strong><div class="muted">room: {safe_room} • local scored rounds: {local_count} • global scored rounds: {history_count}</div></div><div><a class="badge" href="{control_url}">Control</a><a class="badge" href="{overlay_url}">Overlay</a><a class="badge" href="{rooms_url}">Rooms</a></div></div>
            <div class="body"><p class="muted">{confirmed_line}</p><p class="note"><strong>Session</strong> shows the current room's active guesses/votes. <strong>Local</strong> scores this room only. <strong>Global</strong> scores everyone across rooms. Precision Score is confidence-adjusted, so 8/10 ranks better than 24/240.</p></div>
          </section>
          <section class="panel" id="session"><div class="head"><strong>Current Session</strong><span class="muted">active room, pending or just-scored round</span></div><div class="body twocol"><div><h3>Lucky Guesses</h3><table><thead><tr><th>User</th><th>Guess</th><th>Status</th></tr></thead><tbody>{session_guess_rows}</tbody></table></div><div><h3>Decision Votes</h3><table><thead><tr><th>User</th><th>Vote</th><th>Status</th></tr></thead><tbody>{session_vote_rows}</tbody></table></div></div></section>
          <section class="panel" id="local"><div class="head"><strong>Local Room Leaderboard</strong><span class="muted">room: {safe_room}</span></div><div class="body"><table><thead><tr><th>Rank</th><th>User</th><th>Correct</th><th>Total</th><th>Accuracy</th><th>Precision Score</th><th>Debunked</th><th>Vote Correct</th><th>Vote Debunked</th></tr></thead><tbody>{local_rows}</tbody></table></div></section>
          <section class="panel" id="global"><div class="head"><strong>Global Leaderboard</strong><span class="muted">all rooms / all scored contracts</span></div><div class="body"><table><thead><tr><th>Rank</th><th>User</th><th>Correct</th><th>Total</th><th>Accuracy</th><th>Precision Score</th><th>Debunked</th><th>Vote Correct</th><th>Vote Debunked</th></tr></thead><tbody>{global_rows}</tbody></table></div></section>
        </main>
      </body>
    </html>
    """
    return HTMLResponse(html_doc)

@router.get("/phasmo/jumpscare-video")
def phasmo_jumpscare_video():
    if settings._JUMPSCARE_URL:
        return RedirectResponse(settings._JUMPSCARE_URL)
    path = settings._JUMPSCARE_FILE
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Jumpscare video not found. Add jumpscare.mp4 beside main.py or set PHASMOsettings._JUMPSCARE_FILE / PHASMOsettings._JUMPSCARE_URL.")
    return FileResponse(path)

