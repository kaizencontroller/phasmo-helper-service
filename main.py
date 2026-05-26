from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, Tuple

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="Kaizen Phasmophobia Helper")

_STATE_LOCK = threading.Lock()
_STATE_DIR = Path(os.getenv("PHASMO_STATE_DIR", "/tmp/phasmo_state"))
_ADMIN_TOKEN = os.getenv("PHASMO_ADMIN_TOKEN", "").strip()
_ALLOW_BEHAVIOR_COMMANDS = os.getenv("PHASMO_ALLOW_BEHAVIOR_COMMANDS", "true").strip().lower() in {"1", "true", "yes", "on"}

EVIDENCE = ["dots", "emf5", "freezing", "orbs", "writing", "box", "uv"]

EVIDENCE_LABELS = {
    "dots": "D.O.T.S Projector",
    "emf5": "EMF Level 5",
    "freezing": "Freezing Temperatures",
    "orbs": "Ghost Orb",
    "writing": "Ghost Writing",
    "box": "Spirit Box",
    "uv": "Ultraviolet",
}

EVIDENCE_ALIASES = {
    "dots": "dots", "dot": "dots", "projector": "dots", "d.o.t.s": "dots",
    "emf": "emf5", "emf5": "emf5", "emf-5": "emf5", "emf_5": "emf5",
    "freezing": "freezing", "freeze": "freezing", "temps": "freezing", "temp": "freezing",
    "orb": "orbs", "orbs": "orbs", "ghostorb": "orbs", "ghostorbs": "orbs",
    "writing": "writing", "book": "writing",
    "box": "box", "spirit": "box", "spiritbox": "box", "spirit-box": "box",
    "uv": "uv", "ultraviolet": "uv", "fingerprints": "uv", "prints": "uv",
}

GHOST_NAMES = [
    "Aswang", "Banshee", "Dayan", "Demon", "Deogen", "Gallu", "Goryo", "Hantu", "Jinn", "Kormos",
    "Mare", "Moroi", "Myling", "Obake", "Obambo", "Oni", "Onryo", "Phantom", "Poltergeist", "Raiju",
    "Revenant", "Shade", "Spirit", "Thaye", "The Mimic", "The Twins", "Wraith", "Yokai", "Yurei",
]

GHOST_ALIASES = {re.sub(r"[^a-z0-9]", "", name.lower()): name for name in GHOST_NAMES}
GHOST_ALIASES.update({
    "mimic": "The Mimic",
    "twins": "The Twins",
    "twin": "The Twins",
    "polty": "Poltergeist",
    "polter": "Poltergeist",
    "rev": "Revenant",
    "deo": "Deogen",
})

BEHAVIOR_ALIASES = {
    "40-hunt": "deogen-late-hunt",
    "active-early": "thaye-high-activity-early",
    "age": "thaye-aging-speed",
    "aggressive": "obambo-state-speed",
    "aggressive-hunt": "obambo-aggressive-hunts",
    "aging": "thaye-aging-speed",
    "airball": "oni-no-mist",
    "always-knows": "deogen-knows-location",
    "aswang": "aswang-los-ramp",
    "aswang-grace": "aswang-zero-grace",
    "aswang-hidden-spares": "aswang-hidden-spares",
    "aswang-hide": "aswang-hidden-spares",
    "aswang-los-ramp": "aswang-los-ramp",
    "aswang-speed": "aswang-los-ramp",
    "aswang-zero-grace": "aswang-zero-grace",
    "banshee-scream": "banshee-scream",
    "banshee-singing": "banshee-singing",
    "banshee-song": "banshee-singing",
    "banshee-target": "banshee-target",
    "blind-ghost": "kormos-no-los",
    "blink": "oni-full-visible",
    "blowout": "onryo-third-blowout",
    "box-alone-mismatch": "box-alone-mismatch",
    "box-condition": "box-alone-mismatch",
    "breaker": "breaker-off-direct",
    "breaker-off": "breaker-off-direct",
    "breaker-off-direct": "breaker-off-direct",
    "breaker-on": "breaker-on-benefit",
    "breaker-on-benefit": "breaker-on-benefit",
    "breaker-speed": "jinn-breaker-speed",
    "breakeroff": "breaker-off-direct",
    "breakeron": "breaker-on-benefit",
    "breathing": "deogen-spiritbox-breath",
    "bulb": "light-shatter-event",
    "bulb-burst": "light-shatter-event",
    "calm": "obambo-state-speed",
    "camdots": "goryo-camera-dots",
    "camera-dots": "goryo-camera-dots",
    "candle": "onryo-flame-prevent",
    "changing-tells": "mimic-changing-tells",
    "cold": "hantu-temperature-speed",
    "cold-breath": "hantu-breath-breaker-off",
    "cold-fast": "hantu-temperature-speed",
    "constant-throws": "polter-hunt-throw-rate",
    "crucifix-enrage": "gallu-crucifix-enraged",
    "crucifix-range": "demon-crucifix-range",
    "curse": "moroi-curse",
    "dark": "mare-lights-off",
    "dayan": "dayan-moving-speed",
    "dayan-moving": "dayan-moving-speed",
    "dayan-moving-speed": "dayan-moving-speed",
    "dayan-still": "dayan-still-slow",
    "dayan-still-slow": "dayan-still-slow",
    "deaf": "yokai-short-hearing",
    "demon-ability": "demon-ability-hunt",
    "demon-ability-hunt": "demon-ability-hunt",
    "demon-crucifix": "demon-crucifix-range",
    "demon-crucifix-range": "demon-crucifix-range",
    "demon-hunt": "demon-ability-hunt",
    "demon-short-incense": "demon-short-incense",
    "demon-smudge": "demon-short-incense",
    "deo": "deogen-distance-speed",
    "deo-breath": "deogen-spiritbox-breath",
    "deogen": "deogen-distance-speed",
    "deogen-box": "deogen-spiritbox-breath",
    "deogen-distance-speed": "deogen-distance-speed",
    "deogen-knows": "deogen-knows-location",
    "deogen-knows-location": "deogen-knows-location",
    "deogen-late-hunt": "deogen-late-hunt",
    "deogen-speed": "deogen-distance-speed",
    "deogen-spiritbox-breath": "deogen-spiritbox-breath",
    "deogen-threshold": "deogen-late-hunt",
    "different-ghost": "mimic-changing-tells",
    "disappear": "phantom-photo-disappear",
    "door": "yurei-door-room",
    "door-slam": "yurei-door-room",
    "double-interaction": "twins-double-interaction",
    "double-print": "obake-unique-print",
    "double-speed": "twins-speed-profiles",
    "early": "early-hunt",
    "early-hunt": "early-hunt",
    "electric": "raiju-electronics-speed",
    "electronics": "raiju-electronics-speed",
    "electronics-fast": "raiju-electronics-speed",
    "enraged": "gallu-state-thresholds",
    "enraged-salt": "gallu-no-salt-enraged",
    "fake-orbs": "mimic-fake-orbs",
    "fakeorb": "mimic-fake-orbs",
    "fast-accel": "aswang-los-ramp",
    "fast-los": "revenant-los-speed",
    "favorite-room": "goryo-room-stable",
    "feet-emf": "wraith-teleport",
    "fire": "onryo-flame-prevent",
    "flame": "onryo-flame-prevent",
    "footprints": "salt-footprints",
    "footsteps": "myling-quiet-footsteps",
    "freezing-breath": "hantu-breath-breaker-off",
    "full-form": "oni-full-visible",
    "fusebox-emf": "jinn-sanity-drain",
    "gallu": "gallu-state-thresholds",
    "gallu-crucifix": "gallu-crucifix-enraged",
    "gallu-crucifix-enraged": "gallu-crucifix-enraged",
    "gallu-no-salt-enraged": "gallu-no-salt-enraged",
    "gallu-nosalt": "gallu-no-salt-enraged",
    "gallu-salt": "gallu-no-salt-enraged",
    "gallu-state": "gallu-state-thresholds",
    "gallu-state-thresholds": "gallu-state-thresholds",
    "goryo": "goryo-camera-dots",
    "goryo-camera-dots": "goryo-camera-dots",
    "goryo-dots": "goryo-camera-dots",
    "goryo-room": "goryo-room-stable",
    "goryo-room-stable": "goryo-room-stable",
    "hantu": "hantu-temperature-speed",
    "hantu-breath": "hantu-breath-breaker-off",
    "hantu-breath-breaker-off": "hantu-breath-breaker-off",
    "hantu-temperature-speed": "hantu-temperature-speed",
    "head-emf": "phantom-travel",
    "hidden": "aswang-hidden-spares",
    "hidden-prints": "obake-hides-prints",
    "hiding-spot": "aswang-hidden-spares",
    "high-sanity": "early-hunt",
    "hunt": "early-hunt",
    "impossible-combo": "mimic-fake-orbs",
    "interference": "raiju-wide-interference",
    "jinn": "breaker-on-benefit",
    "jinn-breaker-speed": "jinn-breaker-speed",
    "jinn-drain": "jinn-sanity-drain",
    "jinn-los": "jinn-breaker-speed",
    "jinn-sanity-drain": "jinn-sanity-drain",
    "jinn-speed": "jinn-breaker-speed",
    "knows": "deogen-knows-location",
    "kormos": "kormos-sprint-threshold",
    "kormos-event": "kormos-no-mist-chase",
    "kormos-los": "kormos-no-los",
    "kormos-no-los": "kormos-no-los",
    "kormos-no-mist-chase": "kormos-no-mist-chase",
    "kormos-sprint": "kormos-sprint-threshold",
    "kormos-sprint-threshold": "kormos-sprint-threshold",
    "late-hunt": "deogen-late-hunt",
    "light-shatter": "light-shatter-event",
    "light-shatter-event": "light-shatter-event",
    "lights": "light-shatter-event",
    "lights-off": "mare-lights-off",
    "lights-on-roam": "mare-long-roam-lights-on",
    "lineofsight": "revenant-los-speed",
    "long-incense": "spirit-long-incense",
    "long-smudge": "spirit-long-incense",
    "look-drain": "phantom-sanity-look",
    "los-speed": "revenant-los-speed",
    "low-activity": "shade-low-interaction",
    "mare": "mare-lights-off",
    "mare-dark": "mare-lights-off",
    "mare-light-switch": "mare-no-lights-on",
    "mare-lights-off": "mare-lights-off",
    "mare-long-roam-lights-on": "mare-long-roam-lights-on",
    "mare-no-lights-on": "mare-no-lights-on",
    "mare-roam": "mare-long-roam-lights-on",
    "mimic": "mimic-fake-orbs",
    "mimic-change": "mimic-changing-tells",
    "mimic-changing-tells": "mimic-changing-tells",
    "mimic-check": "mimic-fake-orbs",
    "mimic-fake-orbs": "mimic-fake-orbs",
    "model-swap": "obake-shapeshift",
    "moroi": "moroi-curse",
    "moroi-curse": "moroi-curse",
    "moving": "dayan-moving-speed",
    "moving-speed": "dayan-moving-speed",
    "myling": "myling-quiet-footsteps",
    "myling-quiet": "myling-quiet-footsteps",
    "myling-quiet-footsteps": "myling-quiet-footsteps",
    "near-electronics": "raiju-electronics-speed",
    "no-chase-event": "kormos-no-mist-chase",
    "no-fingerprint": "obake-hides-prints",
    "no-footprints": "wraith-no-salt",
    "no-lights-on": "mare-no-lights-on",
    "no-los": "kormos-no-los",
    "no-mist": "oni-no-mist",
    "no-prints": "wraith-no-salt",
    "no-room-change": "goryo-room-stable",
    "no-salt": "wraith-no-salt",
    "no-sanity-hunt": "demon-ability-hunt",
    "nograce": "aswang-zero-grace",
    "nohunt": "shade-shy",
    "nosalt": "wraith-no-salt",
    "notphantom": "photo-visible",
    "obake": "obake-unique-print",
    "obake-hide": "obake-hides-prints",
    "obake-hides-prints": "obake-hides-prints",
    "obake-shape": "obake-shapeshift",
    "obake-shapeshift": "obake-shapeshift",
    "obake-unique-print": "obake-unique-print",
    "obambo": "obambo-state-speed",
    "obambo-aggressive-hunts": "obambo-aggressive-hunts",
    "obambo-hunt": "obambo-aggressive-hunts",
    "obambo-state-speed": "obambo-state-speed",
    "oni": "oni-no-mist",
    "oni-full-visible": "oni-full-visible",
    "oni-no-mist": "oni-no-mist",
    "oni-visible": "oni-full-visible",
    "onryo": "onryo-flame-prevent",
    "onryo-flame-prevent": "onryo-flame-prevent",
    "onryo-third-blowout": "onryo-third-blowout",
    "para": "banshee-scream",
    "parabolic": "banshee-scream",
    "phantom-drain": "phantom-sanity-look",
    "phantom-photo": "phantom-photo-disappear",
    "phantom-photo-disappear": "phantom-photo-disappear",
    "phantom-sanity-look": "phantom-sanity-look",
    "phantom-travel": "phantom-travel",
    "photo": "phantom-photo-disappear",
    "photo-disappear": "phantom-photo-disappear",
    "photo-visible": "photo-visible",
    "polter": "polter-multi-throw",
    "polter-hunt": "polter-hunt-throw-rate",
    "polter-hunt-throw-rate": "polter-hunt-throw-rate",
    "polter-multi-throw": "polter-multi-throw",
    "polter-throw": "polter-multi-throw",
    "polty": "polter-multi-throw",
    "poweroff": "breaker-off-direct",
    "poweron": "breaker-on-benefit",
    "prints": "salt-footprints",
    "quiet": "myling-quiet-footsteps",
    "raiju": "raiju-electronics-speed",
    "raiju-electronics-speed": "raiju-electronics-speed",
    "raiju-interference": "raiju-wide-interference",
    "raiju-wide-interference": "raiju-wide-interference",
    "responds": "box-alone-mismatch",
    "response": "box-alone-mismatch",
    "rev": "revenant-los-speed",
    "revenant": "revenant-los-speed",
    "revenant-los-speed": "revenant-los-speed",
    "revenant-speed": "revenant-los-speed",
    "room-trap": "yurei-incense-trap",
    "salt-footprints": "salt-footprints",
    "salt-prints": "salt-footprints",
    "saltprints": "salt-footprints",
    "same-room-block": "shade-shy",
    "sanity-drain": "jinn-sanity-drain",
    "scream": "banshee-scream",
    "shade": "shade-shy",
    "shade-activity": "shade-low-interaction",
    "shade-low-interaction": "shade-low-interaction",
    "shade-shy": "shade-shy",
    "shapeshift": "obake-shapeshift",
    "short-hearing": "yokai-short-hearing",
    "short-hunt": "obambo-aggressive-hunts",
    "short-incense": "demon-short-incense",
    "short-smudge": "demon-short-incense",
    "shy": "shade-shy",
    "singing": "banshee-singing",
    "single-target": "banshee-target",
    "six-finger": "obake-unique-print",
    "six-fingers": "obake-unique-print",
    "sixfinger": "obake-unique-print",
    "slam": "yurei-door-room",
    "slow-close": "deogen-distance-speed",
    "smudge": "spirit-long-incense",
    "song": "banshee-singing",
    "spares-hidden": "aswang-hidden-spares",
    "spirit": "spirit-long-incense",
    "spirit-long-incense": "spirit-long-incense",
    "sprint": "kormos-sprint-threshold",
    "sprinting": "kormos-sprint-threshold",
    "standing-still": "dayan-still-slow",
    "state-swap": "obambo-state-speed",
    "still": "dayan-still-slow",
    "talk-hunt": "yokai-talking-hunt",
    "talking": "yokai-talking-hunt",
    "target": "banshee-target",
    "teleport": "wraith-teleport",
    "temperature": "hantu-temperature-speed",
    "thaye": "thaye-aging-speed",
    "thaye-activity": "thaye-high-activity-early",
    "thaye-age": "thaye-aging-speed",
    "thaye-aging-speed": "thaye-aging-speed",
    "thaye-high-activity-early": "thaye-high-activity-early",
    "third-blowout": "onryo-third-blowout",
    "three-candles": "onryo-third-blowout",
    "throw": "polter-multi-throw",
    "throws": "polter-multi-throw",
    "turns-lights-off": "mare-no-lights-on",
    "twin": "twins-speed-profiles",
    "twins": "twins-speed-profiles",
    "twins-double-interaction": "twins-double-interaction",
    "twins-interaction": "twins-double-interaction",
    "twins-speed-profiles": "twins-speed-profiles",
    "two-interactions": "twins-double-interaction",
    "two-speeds": "twins-speed-profiles",
    "unique-print": "obake-unique-print",
    "visible": "oni-full-visible",
    "visible-photo": "photo-visible",
    "voice": "yokai-talking-hunt",
    "warm-room": "hantu-temperature-speed",
    "weakened": "gallu-state-thresholds",
    "wide-interference": "raiju-wide-interference",
    "wraith": "wraith-no-salt",
    "wraith-no-salt": "wraith-no-salt",
    "wraith-teleport": "wraith-teleport",
    "yokai": "yokai-talking-hunt",
    "yokai-hearing": "yokai-short-hearing",
    "yokai-short-hearing": "yokai-short-hearing",
    "yokai-talking-hunt": "yokai-talking-hunt",
    "yurei": "yurei-door-room",
    "yurei-door-room": "yurei-door-room",
    "yurei-incense": "yurei-incense-trap",
    "yurei-incense-trap": "yurei-incense-trap",
    "yurei-smudge": "yurei-incense-trap",
    "zero-grace": "aswang-zero-grace"
}

HTML_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Kaizen Phasmophobia Helper</title>
<style>
:root{--bg:#000;--panel:#172235ee;--soft:#213149;--text:#f8fafc;--muted:#94a3b8;--line:#334155;--orange:#f97316;--green:#22c55e;--red:#ef4444;--blue:#38bdf8;--grey:#64748b}*{box-sizing:border-box}body{margin:0;background:#000;color:var(--text);font-family:Inter,system-ui,Segoe UI,sans-serif}.app{width:min(460px,100vw);height:100vh;overflow:auto;padding:10px;background:#000}.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;margin-bottom:10px;box-shadow:0 16px 40px #0007}.head{padding:12px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:8px}.body{padding:10px}.muted{color:var(--muted);font-size:12px}.badge,.chip{border:1px solid var(--line);background:#0f172a;border-radius:999px;padding:5px 8px;font-size:12px}button,select,input{background:#0f172a;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:9px 10px;font:inherit}button{cursor:pointer;touch-action:manipulation;user-select:none}button:disabled{opacity:.45;cursor:not-allowed}.green{background:#14532d;border-color:#22c55e}.red{background:#5b2329;border-color:#ef4444}.blue{background:#123247;border-color:#38bdf8}.orange{background:#432919;border-color:#f97316}.grey{background:#273244;border-color:#64748b;color:#cbd5e1}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.spread{display:flex;justify-content:space-between;align-items:center;gap:8px}.next{border-color:#f97316;background:#2a2330}.big{font-weight:950;font-size:28px;line-height:1}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}.evrow{display:grid;grid-template-columns:1fr 48px 48px 48px;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid #33415588}.evrow:last-child{border-bottom:0}.evname{font-weight:850;font-size:15px}.state{height:46px;padding:0;font-size:24px;font-weight:900}.state.active.yes{background:#14532d;border-color:#22c55e;box-shadow:0 0 0 2px #22c55e66}.state.active.no{background:#5b2329;border-color:#ef4444;box-shadow:0 0 0 2px #ef444466}.state.active.unk{background:#123247;border-color:#38bdf8;box-shadow:0 0 0 2px #38bdf866}.state.inactive{background:#1f2937;border-color:#475569;color:#94a3b8;opacity:.55}.ghosts{display:grid;grid-template-columns:1fr 1fr;gap:7px;max-height:260px;overflow:auto}.ghost{border:1px solid var(--line);border-radius:12px;padding:8px;background:#111a2b}.ghost.top{border-color:#22c55e;background:#132a24}.ghost h4{margin:0 0 5px;font-size:14px}.tags{display:flex;gap:4px;flex-wrap:wrap}.chip{font-size:10px;padding:3px 5px}.vote-grid{display:grid;gap:7px}.vote-row{display:flex;justify-content:space-between;align-items:center;gap:8px;border:1px solid var(--line);border-radius:10px;background:#0f172a;padding:8px}.vote-name{font-weight:900}.vote-users{color:var(--muted);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.branch{border:1px solid var(--line);border-radius:13px;overflow:hidden;margin-bottom:8px;background:#111a2b}.branch-title{width:100%;border:0;border-bottom:1px solid var(--line);border-radius:0;display:flex;justify-content:space-between}.branch-body{padding:8px;display:grid;gap:7px}.option{border:1px solid #334155;border-radius:11px;padding:8px;background:#0f172a}.option-label{font-weight:800;font-size:13px;margin-bottom:5px}.selected{padding:8px;background:#163425}.selected.bad{background:#3a1d24}.error{border-color:#ef4444;color:#fecaca;background:#3a1d24;padding:8px;border-radius:10px}.overlay{width:430px;height:170px;display:flex;align-items:flex-start;justify-content:flex-start;padding:8px;background:#000;overflow:hidden}.ov-card{width:414px;height:154px;background:linear-gradient(180deg,#172235f7,#0f172af2);border:1px solid #f9731688;border-radius:16px;padding:10px 12px;overflow:hidden;box-shadow:0 14px 32px #000b}.ov-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:4px}.ov-kicker{font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:var(--muted);font-weight:950}.ov-ghosts{display:flex;justify-content:flex-end;gap:4px;flex-wrap:wrap;max-width:190px;max-height:34px;overflow:hidden}.ov-ghosts .badge{font-size:9px;padding:3px 6px;background:#0b1220;border-color:#334155}.ov-step{font-size:28px;font-weight:950;line-height:1;letter-spacing:-.04em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:4px}.ov-sub{font-size:11px;color:#dbeafe;line-height:1.18;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:26px}.ov-bottom{display:grid;grid-template-columns:214px 1fr;gap:8px;margin-top:7px;align-items:end}.ov-evidence{display:flex;gap:4px}.ev-dot{width:26px;height:26px;border-radius:8px;border:1px solid #475569;background:#1d293a;color:#cbd5e1;display:grid;place-items:center;font-size:14px;font-weight:900;line-height:1}.ev-dot.yes{background:#123d29;border-color:#22c55e;color:#dcfce7}.ev-dot.no{background:#4a1f26;border-color:#ef4444;color:#fee2e2}.ov-notes{border-left:1px solid #334155aa;padding-left:8px;min-width:0}.ov-notes-title{font-size:8px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);font-weight:950;margin-bottom:2px}.ov-note-text{font-size:10px;color:#cbd5e1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ov-note-good{color:#bbf7d0}.ov-note-bad{color:#fecaca}.ov-note-vote{color:#dbeafe}.hidden{display:none!important}@media(max-width:700px){.app{width:100vw}.ghosts{grid-template-columns:1fr}.evrow{grid-template-columns:1fr 52px 52px 52px}.state{height:50px}}
</style>
</head>
<body>
<div id="control" class="app hidden">
  <div class="panel"><div class="head"><div><strong>Phasmo Control</strong><div class="muted">shared room: <span id="roomLabel"></span></div></div><span class="badge" id="countBadge">0</span></div>
    <div class="body"><div id="authMessage" class="error hidden"></div><div class="spread"><span class="muted">Evidence mode</span><select id="mode"><option value="3">3 evidence</option><option value="2">2 evidence</option><option value="1">1 evidence</option><option value="0">0 evidence</option></select></div></div>
  </div>
  <div class="panel"><div class="body"><div class="spread"><strong>Responds: <span id="respondsText">Unknown</span></strong><button id="changeResponds">Change</button></div><div id="respondsChoices" class="grid3" style="margin-top:8px"><button data-responds="unknown">Unknown</button><button data-responds="everyone">Everyone</button><button data-responds="alone">Alone</button></div><div class="muted" id="respondsHint" style="margin-top:8px"></div></div></div>
  <div class="panel next"><div class="body"><div class="muted" style="letter-spacing:.12em;font-weight:900">NEXT</div><div class="big" id="nextName">Loading</div><p class="muted" id="nextWhy"></p><div class="grid2"><button class="green" id="confirmNext">Confirm</button><button class="red" id="denyNext">No</button></div></div></div>
  <div class="panel"><div class="body row"><button class="orange" id="reset">Reset</button><button class="blue" id="copyOverlay">Copy Overlay URL</button></div></div>
  <div class="panel"><div class="body" id="evidenceRows"></div></div>
  <div class="panel"><div class="head"><strong>Candidates</strong><span class="muted" id="summary"></span></div><div class="body"><div class="ghosts" id="ghosts"></div></div></div>
  <div class="panel"><div class="head"><strong>Chat Ghost Votes</strong><span class="muted">!vote ghostname</span></div><div class="body"><div id="votes" class="vote-grid"></div><p class="muted" style="margin-top:8px">Commands: !vote Wraith, !guess Deogen, !unvote, !votes</p></div></div>
  <div class="panel"><div class="head"><strong>Behavior Branches</strong></div><div class="body"><input id="behaviorFilter" placeholder="filter: speed, salt, photo" style="width:100%;margin-bottom:8px"><div id="behaviors"></div></div></div>
</div>
<div id="overlay" class="overlay hidden"><section class="ov-card"><div class="ov-top"><div class="ov-kicker" id="ovKicker">Next Best Test</div><div class="ov-ghosts" id="ovGhosts"></div></div><div class="ov-step" id="ovStep">Loading</div><p class="ov-sub" id="ovSub"></p><div class="ov-bottom"><div class="ov-evidence" id="ovEvidence"></div><div class="ov-notes"><div class="ov-notes-title">Notes / Chat</div><div class="ov-note-text" id="ovNotes">No behaviors or guesses.</div></div></div></section></div>
<script>
const MODE='__MODE__';
const params=new URLSearchParams(location.search);
const room=params.get('room')||'default';
const token=params.get('token')||localStorage.getItem('phasmoAdminToken')||'';
if(token){ localStorage.setItem('phasmoAdminToken', token); }
const API='/api/phasmo';
const E=['dots','emf5','freezing','orbs','writing','box','uv'];
const EL={dots:'D.O.T.S Projector',emf5:'EMF Level 5',freezing:'Freezing Temperatures',orbs:'Ghost Orb',writing:'Ghost Writing',box:'Spirit Box',uv:'Ultraviolet'};
const G=[
['Aswang',['freezing','writing','dots']],['Banshee',['dots','orbs','uv']],['Dayan',['emf5','orbs','box']],['Demon',['writing','uv','freezing']],['Deogen',['dots','writing','box']],['Gallu',['emf5','box','uv']],['Goryo',['dots','emf5','uv']],['Hantu',['orbs','uv','freezing']],['Jinn',['emf5','uv','freezing']],['Kormos',['orbs','box','uv']],['Mare',['writing','orbs','box']],['Moroi',['writing','freezing','box']],['Myling',['writing','emf5','uv']],['Obake',['emf5','orbs','uv']],['Obambo',['uv','writing','dots']],['Oni',['dots','emf5','freezing']],['Onryo',['orbs','freezing','box']],['Phantom',['dots','uv','box']],['Poltergeist',['writing','uv','box']],['Raiju',['dots','emf5','orbs']],['Revenant',['writing','orbs','freezing']],['Shade',['writing','emf5','freezing']],['Spirit',['writing','emf5','box']],['Thaye',['dots','writing','orbs']],['The Mimic',['uv','freezing','box']],['The Twins',['emf5','freezing','box']],['Wraith',['dots','emf5','box']],['Yokai',['dots','orbs','box']],['Yurei',['dots','orbs','freezing']]
].map(([name,ev])=>({name,ev}));
const B=[{"id":"hantu-temperature-speed","cat":"Movement Speed","label":"Speed changes with room temperature","up":["Hantu"],"down":[],"w":48,"rel":"High"},{"id":"raiju-electronics-speed","cat":"Movement Speed","label":"Speeds up near active electronics","up":["Raiju"],"down":[],"w":48,"rel":"High"},{"id":"revenant-los-speed","cat":"Movement Speed","label":"Slow searching, extremely fast after detecting a player","up":["Revenant"],"down":[],"w":52,"rel":"High"},{"id":"deogen-distance-speed","cat":"Movement Speed","label":"Very fast far away, very slow when close","up":["Deogen"],"down":[],"w":56,"rel":"High"},{"id":"dayan-moving-speed","cat":"Movement Speed","label":"Fast when a nearby player is moving","up":["Dayan"],"down":[],"w":44,"rel":"High"},{"id":"dayan-still-slow","cat":"Movement Speed","label":"Slow when nearby player stands still","up":["Dayan"],"down":[],"w":40,"rel":"High"},{"id":"twins-speed-profiles","cat":"Movement Speed","label":"Two different hunt speed profiles","up":["The Twins"],"down":[],"w":38,"rel":"Med"},{"id":"thaye-aging-speed","cat":"Movement Speed","label":"Starts fast/hyperactive, calms and slows over time","up":["Thaye"],"down":[],"w":44,"rel":"High"},{"id":"obambo-state-speed","cat":"Movement Speed","label":"Alternates calm/aggressive speed and hunt behavior","up":["Obambo"],"down":[],"w":40,"rel":"Med"},{"id":"aswang-los-ramp","cat":"Movement Speed","label":"Lower base speed but faster line-of-sight acceleration","up":["Aswang"],"down":[],"w":34,"rel":"Med"},{"id":"wraith-no-salt","cat":"Salt / Ultraviolet","label":"Does not disturb salt at all","up":["Wraith"],"down":[],"w":58,"rel":"High"},{"id":"salt-footprints","cat":"Salt / Ultraviolet","label":"Salt disturbed and UV footprints appear","up":[],"down":["Wraith"],"w":45,"rel":"High"},{"id":"gallu-no-salt-enraged","cat":"Salt / Ultraviolet","label":"Cannot disturb salt while enraged","up":["Gallu"],"down":[],"w":36,"rel":"Med"},{"id":"obake-unique-print","cat":"Salt / Ultraviolet","label":"Unique UV print such as six fingers or double switch print","up":["Obake"],"down":[],"w":58,"rel":"High"},{"id":"obake-hides-prints","cat":"Salt / Ultraviolet","label":"Repeated valid UV interactions sometimes leave no print","up":["Obake"],"down":[],"w":32,"rel":"Med"},{"id":"breaker-off-direct","cat":"Electricity / Breaker / Lights","label":"Ghost turns breaker off directly","up":["Hantu","Mare"],"down":["Jinn"],"w":30,"rel":"Med"},{"id":"breaker-on-benefit","cat":"Electricity / Breaker / Lights","label":"Performs better with breaker on","up":["Jinn","Raiju"],"down":["Hantu"],"w":22,"rel":"Low"},{"id":"jinn-breaker-speed","cat":"Electricity / Breaker / Lights","label":"Fast with breaker on, line of sight, and target over 3m away","up":["Jinn"],"down":[],"w":46,"rel":"High"},{"id":"jinn-sanity-drain","cat":"Electricity / Breaker / Lights","label":"Nearby sanity drain with EMF at fuse box","up":["Jinn"],"down":[],"w":38,"rel":"Med"},{"id":"hantu-breath-breaker-off","cat":"Electricity / Breaker / Lights","label":"Freezing breath during hunts when breaker is off or broken","up":["Hantu"],"down":[],"w":48,"rel":"High"},{"id":"mare-lights-off","cat":"Electricity / Breaker / Lights","label":"More dangerous when current room lights are off or broken","up":["Mare"],"down":[],"w":32,"rel":"Med"},{"id":"mare-no-lights-on","cat":"Electricity / Breaker / Lights","label":"Never turns lights on and may immediately turn them off","up":["Mare"],"down":[],"w":34,"rel":"Med"},{"id":"light-shatter-event","cat":"Electricity / Breaker / Lights","label":"Prefers light-shattering events","up":["Mare"],"down":[],"w":24,"rel":"Low"},{"id":"raiju-wide-interference","cat":"Electricity / Breaker / Lights","label":"Electronic interference range feels larger than normal","up":["Raiju"],"down":[],"w":34,"rel":"Med"},{"id":"yokai-short-hearing","cat":"Electricity / Breaker / Lights","label":"During hunts, only hears voice/electronics very close","up":["Yokai"],"down":[],"w":42,"rel":"High"},{"id":"early-hunt","cat":"Hunt Timing / Threshold","label":"Hunts earlier than normal sanity threshold","up":["Demon","Mare","Onryo","Thaye","Raiju","Yokai","Dayan","Kormos","Gallu","Obambo"],"down":["Shade","Deogen"],"w":30,"rel":"Med"},{"id":"demon-ability-hunt","cat":"Hunt Timing / Threshold","label":"Very early hunt that may ignore sanity","up":["Demon"],"down":[],"w":46,"rel":"Med"},{"id":"shade-shy","cat":"Hunt Timing / Threshold","label":"Will not hunt or interact while players are in the same room","up":["Shade"],"down":["Demon","Oni"],"w":42,"rel":"Med"},{"id":"yokai-talking-hunt","cat":"Hunt Timing / Threshold","label":"Talking in same room appears to enable earlier hunt","up":["Yokai"],"down":[],"w":38,"rel":"Med"},{"id":"kormos-sprint-threshold","cat":"Hunt Timing / Threshold","label":"Player sprinting in same room appears to enable earlier hunt","up":["Kormos"],"down":[],"w":36,"rel":"Med"},{"id":"aswang-zero-grace","cat":"Hunt Timing / Threshold","label":"Hunt sometimes appears to start with no grace period","up":["Aswang"],"down":[],"w":36,"rel":"Med"},{"id":"gallu-state-thresholds","cat":"Hunt Timing / Threshold","label":"Hunt threshold changes with normal/enraged/weakened state","up":["Gallu"],"down":[],"w":32,"rel":"Med"},{"id":"obambo-aggressive-hunts","cat":"Hunt Timing / Threshold","label":"Aggressive state hunts earlier but may be shorter","up":["Obambo"],"down":[],"w":34,"rel":"Med"},{"id":"deogen-late-hunt","cat":"Hunt Timing / Threshold","label":"Does not hunt until lower sanity than normal","up":["Deogen"],"down":[],"w":26,"rel":"Low"},{"id":"onryo-flame-prevent","cat":"Fire / Incense / Crucifix","label":"Lit flame nearby prevents hunts like a crucifix","up":["Onryo"],"down":[],"w":48,"rel":"High"},{"id":"onryo-third-blowout","cat":"Fire / Incense / Crucifix","label":"Hunt attempt after third flame blowout with no nearby flame","up":["Onryo"],"down":[],"w":52,"rel":"High"},{"id":"spirit-long-incense","cat":"Fire / Incense / Crucifix","label":"Incense prevents hunts much longer than normal","up":["Spirit"],"down":["Demon"],"w":48,"rel":"High"},{"id":"demon-short-incense","cat":"Fire / Incense / Crucifix","label":"Incense protection seems shorter than normal","up":["Demon"],"down":["Spirit"],"w":46,"rel":"High"},{"id":"demon-crucifix-range","cat":"Fire / Incense / Crucifix","label":"Crucifix blocks hunt from farther away than expected","up":["Demon"],"down":[],"w":32,"rel":"Med"},{"id":"gallu-crucifix-enraged","cat":"Fire / Incense / Crucifix","label":"Crucifix burn causes enraged Gallu behavior","up":["Gallu"],"down":[],"w":38,"rel":"Med"},{"id":"yurei-incense-trap","cat":"Fire / Incense / Crucifix","label":"Non-hunt incense traps it in favorite room","up":["Yurei"],"down":[],"w":32,"rel":"Med"},{"id":"phantom-photo-disappear","cat":"Ghost Events / Manifestation","label":"Ghost disappears when photographed or filmed","up":["Phantom"],"down":[],"w":58,"rel":"High"},{"id":"photo-visible","cat":"Ghost Events / Manifestation","label":"Ghost remains visible in ghost photo","up":[],"down":["Phantom"],"w":32,"rel":"Med"},{"id":"oni-no-mist","cat":"Ghost Events / Manifestation","label":"No mist-form/airball events observed after many events","up":["Oni"],"down":[],"w":34,"rel":"Med"},{"id":"oni-full-visible","cat":"Ghost Events / Manifestation","label":"Very visible during hunts or strong full-form events","up":["Oni"],"down":["Phantom"],"w":35,"rel":"Med"},{"id":"kormos-no-mist-chase","cat":"Ghost Events / Manifestation","label":"Cannot perform mist-form or chasing ghost events","up":["Kormos"],"down":[],"w":32,"rel":"Med"},{"id":"banshee-singing","cat":"Ghost Events / Manifestation","label":"Frequent singing events or unusual singing sanity drain target","up":["Banshee"],"down":[],"w":34,"rel":"Med"},{"id":"phantom-sanity-look","cat":"Ghost Events / Manifestation","label":"Looking at manifestation drains sanity unusually fast","up":["Phantom"],"down":[],"w":30,"rel":"Low"},{"id":"myling-quiet-footsteps","cat":"Sound / Spirit Box","label":"Hunt footsteps/vocalizations only audible when close","up":["Myling"],"down":[],"w":46,"rel":"High"},{"id":"banshee-scream","cat":"Sound / Spirit Box","label":"Banshee scream on parabolic microphone","up":["Banshee"],"down":[],"w":48,"rel":"High"},{"id":"deogen-spiritbox-breath","cat":"Sound / Spirit Box","label":"Deogen breathing response on Spirit Box","up":["Deogen"],"down":[],"w":44,"rel":"High"},{"id":"moroi-curse","cat":"Sound / Spirit Box","label":"Cursed player drains sanity rapidly after paranormal audio/contact","up":["Moroi"],"down":[],"w":42,"rel":"Med"},{"id":"box-alone-mismatch","cat":"Sound / Spirit Box","label":"Spirit Box only works under correct alone/everyone condition","up":[],"down":[],"w":0,"rel":"Context"},{"id":"goryo-camera-dots","cat":"Room / Roaming / D.O.T.S","label":"D.O.T.S visible on camera only, not naked eye","up":["Goryo"],"down":[],"w":50,"rel":"High"},{"id":"goryo-room-stable","cat":"Room / Roaming / D.O.T.S","label":"Favorite room does not naturally change","up":["Goryo"],"down":[],"w":28,"rel":"Low"},{"id":"thaye-high-activity-early","cat":"Room / Roaming / D.O.T.S","label":"Very high activity early, lower activity later","up":["Thaye"],"down":[],"w":36,"rel":"Med"},{"id":"mare-long-roam-lights-on","cat":"Room / Roaming / D.O.T.S","label":"Seems to roam farther when lights are on","up":["Mare"],"down":[],"w":20,"rel":"Low"},{"id":"yurei-door-room","cat":"Room / Roaming / D.O.T.S","label":"Strong door ability or favorite-room trapping behavior","up":["Yurei"],"down":[],"w":38,"rel":"Med"},{"id":"banshee-target","cat":"Targeting / Awareness","label":"Only one player seems targeted during hunts","up":["Banshee"],"down":[],"w":42,"rel":"Med"},{"id":"deogen-knows-location","cat":"Targeting / Awareness","label":"Always knows where players are during hunts","up":["Deogen"],"down":[],"w":44,"rel":"High"},{"id":"kormos-no-los","cat":"Targeting / Awareness","label":"No visual line-of-sight; detects voice/electronics/footsteps instead","up":["Kormos"],"down":[],"w":50,"rel":"High"},{"id":"aswang-hidden-spares","cat":"Targeting / Awareness","label":"Reaches correctly hidden player and hunt ends instead of killing","up":["Aswang"],"down":[],"w":58,"rel":"High"},{"id":"wraith-teleport","cat":"Targeting / Awareness","label":"Teleports to player and leaves EMF at feet level","up":["Wraith"],"down":[],"w":32,"rel":"Med"},{"id":"phantom-travel","cat":"Targeting / Awareness","label":"Travels to random player and leaves EMF at head level","up":["Phantom"],"down":[],"w":28,"rel":"Low"},{"id":"polter-multi-throw","cat":"Object / Interaction","label":"Object pile explosion or many throws at once","up":["Poltergeist"],"down":[],"w":55,"rel":"High"},{"id":"polter-hunt-throw-rate","cat":"Object / Interaction","label":"Throws objects constantly during hunts","up":["Poltergeist"],"down":[],"w":44,"rel":"High"},{"id":"twins-double-interaction","cat":"Object / Interaction","label":"Near-simultaneous interactions in separate places","up":["The Twins"],"down":[],"w":42,"rel":"Med"},{"id":"shade-low-interaction","cat":"Object / Interaction","label":"Low interaction/events while players are near the ghost","up":["Shade"],"down":["Oni","Poltergeist"],"w":34,"rel":"Med"},{"id":"obake-shapeshift","cat":"Object / Interaction","label":"Brief shapeshift/model flicker during hunt","up":["Obake"],"down":[],"w":52,"rel":"High"},{"id":"mimic-fake-orbs","cat":"Mimic / Special Cases","label":"Ghost Orbs plus impossible evidence combo","up":["The Mimic"],"down":[],"w":60,"rel":"High"},{"id":"mimic-changing-tells","cat":"Mimic / Special Cases","label":"Behavior tells change between hunts or over time","up":["The Mimic"],"down":[],"w":44,"rel":"Med"}];
let state={evidence:{},behaviors:{},votes:{},responds:'unknown',evidenceMode:'3'}; let expanded={};
function apiUrl(path){return `${API}${path}?room=${encodeURIComponent(room)}${token?'&token='+encodeURIComponent(token):''}`}
async function getState(){let r=await fetch(`${API}/state?room=${encodeURIComponent(room)}`);state=await r.json();render();}
async function postState(patch){let r=await fetch(apiUrl('/state'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});if(!r.ok){showAuthError('Update blocked. If PHASMO_ADMIN_TOKEN is set, open the control URL with &token=YOUR_TOKEN once.');return;}await getState();}
async function command(cmd,user='control'){let r=await fetch(apiUrl('/command'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd,user:user})});if(!r.ok){showAuthError('Command blocked. Token missing or invalid.');return;}await getState();}
function showAuthError(msg){let box=document.getElementById('authMessage'); if(box){box.textContent=msg;box.classList.remove('hidden');}}
function impact(g){let s=0; for(const b of B){let v=state.behaviors?.[b.id]||'unknown'; if(v==='observed'){if(b.up.includes(g.name))s+=b.w;if(b.down.includes(g.name))s-=b.w} if(v==='contradicted'){if(b.up.includes(g.name))s-=Math.round(b.w*.65);if(b.down.includes(g.name))s+=Math.round(b.w*.45)}} return s}
function candidates(){let yes=E.filter(k=>state.evidence[k]==='yes'), no=E.filter(k=>state.evidence[k]==='no'), mode=+state.evidenceMode; return G.filter(g=>{if(mode===0&&!yes.length)return true; if(!yes.every(e=>g.ev.includes(e)||(g.name==='The Mimic'&&e==='orbs')))return false; if(mode===3&&no.some(e=>g.ev.includes(e)||(g.name==='The Mimic'&&e==='orbs')))return false; return true}).map(g=>({...g,impact:impact(g),score:impact(g)+yes.filter(e=>g.ev.includes(e)).length*22+(g.name==='The Mimic'&&yes.includes('orbs')?12:0)})).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name))}
function status(){let c=candidates(), yes=E.filter(k=>state.evidence[k]==='yes'), mode=+state.evidenceMode, target=mode>0&&yes.length>=mode, mimic=c.some(g=>g.name==='The Mimic'); if(!c.length)return{kind:'conflict',name:'Retest',text:'No ghost matches. Recheck evidence.'}; if(target&&c.length===1)return{kind:'locked',name:`Final ID: ${c[0].name}`,text:'Evidence target reached. Behavior is sanity-check only.'}; if(target&&mimic)return{kind:'mimic',name:'Mimic Check',text:'Evidence target reached, but Mimic remains possible.'}; if(target)return{kind:'locked',name:`Likely: ${c[0].name}`,text:'Evidence target reached. Resolve contradictions only.'}; if(c.length===1)return{kind:'verify',name:`Verify ${c[0].name}`,text:'One candidate remains. Final disconfirming check.'}; return{kind:'open',name:'Investigating',text:'Continue evidence collection.'}}
function nextEv(){let st=status(); if(['locked','conflict','verify'].includes(st.kind))return null; let c=candidates(), unk=E.filter(e=>state.evidence[e]==='unknown'); if(c.length<=1||!unk.length)return null; return unk.map(ev=>{let y=0,n=0; for(const g of c){let has=g.ev.includes(ev)||(g.name==='The Mimic'&&ev==='orbs'); has?y++:n++} let split=Math.min(y,n), swing=Math.abs(y-n); return{ev,y,n,split,score:split*10-swing-(ev==='box'&&state.responds==='unknown'?2:0)}}).sort((a,b)=>b.score-a.score||b.split-a.split||a.swing-b.swing)[0]}
function voteSummary(){let counts={}; for(const [user,ghost] of Object.entries(state.votes||{})){counts[ghost]??=[];counts[ghost].push(user)} return Object.entries(counts).map(([ghost,users])=>({ghost,users,count:users.length})).sort((a,b)=>b.count-a.count||a.ghost.localeCompare(b.ghost))}
function responseLine(){let r=state.responds||'unknown'; if(r==='alone')return 'Spirit Box board: responds to people who are alone.'; if(r==='everyone')return 'Spirit Box board: responds to everyone.'; return 'Spirit Box response condition unknown. Test solo and group before ruling out.';}
function render(){ if(MODE==='overlay')renderOverlay(); else renderControl(); }
function renderControl(){document.getElementById('control').classList.remove('hidden');document.getElementById('roomLabel').textContent=room;document.getElementById('mode').value=state.evidenceMode;let c=candidates();document.getElementById('countBadge').textContent=c.length+' candidates';document.getElementById('summary').textContent=`${E.filter(k=>state.evidence[k]==='yes').length} confirmed`;let r=state.responds||'unknown';document.getElementById('respondsText').textContent=r[0].toUpperCase()+r.slice(1);document.getElementById('respondsChoices').classList.toggle('hidden',r!=='unknown');document.getElementById('respondsHint').textContent=responseLine();
 let nx=nextEv(), st=status(); document.getElementById('nextName').textContent=nx?EL[nx.ev]:st.name; document.getElementById('nextWhy').textContent=nx?`${EL[nx.ev]} splits ${nx.y}/${nx.n}.`+(nx.ev==='box'?` ${responseLine()}`:''):st.text; document.getElementById('confirmNext').disabled=!nx;document.getElementById('denyNext').disabled=!nx;document.getElementById('confirmNext').textContent=nx?'Confirm '+EL[nx.ev]:'Confirmed';document.getElementById('denyNext').textContent=nx?'No '+EL[nx.ev]:'No more evidence'; if(nx){document.getElementById('confirmNext').onclick=()=>postState({evidence:{[nx.ev]:'yes'}});document.getElementById('denyNext').onclick=()=>postState({evidence:{[nx.ev]:'no'}})}
 document.getElementById('evidenceRows').innerHTML=E.map(k=>{let v=state.evidence[k]||'unknown'; let cls=(want)=>`state ${want} ${v===want?'active':'inactive'}`; return `<div class='evrow'><span class='evname'>${EL[k]}</span><button class='${cls('yes')}' data-ev='${k}' data-val='yes'>✓</button><button class='${cls('unk')}' data-ev='${k}' data-val='unknown'>?</button><button class='${cls('no')}' data-ev='${k}' data-val='no'>×</button></div>`}).join(''); document.querySelectorAll('[data-ev]').forEach(btn=>btn.onclick=()=>postState({evidence:{[btn.dataset.ev]:btn.dataset.val}}));
 document.getElementById('ghosts').innerHTML=c.slice(0,8).map((g,i)=>`<div class='ghost ${i===0&&g.score>0?'top':''}'><h4>${g.name}</h4><div class='tags'>${g.ev.map(e=>`<span class='chip'>${EL[e]}</span>`).join('')}${g.ev.includes('box')?`<span class='chip blue'>${state.responds==='alone'?'Box: Alone':state.responds==='everyone'?'Box: Everyone':'Box: Unknown response'}</span>`:''}</div><div class='muted'>${g.impact?`${g.impact>0?'+':''}${g.impact} behavior`:'No behavior'}</div></div>`).join(''); renderVotes(); renderBehaviors();}
function renderVotes(){let box=document.getElementById('votes');let rows=voteSummary(); if(!rows.length){box.innerHTML='<p class="muted">No chat guesses yet.</p>';return;} box.innerHTML=rows.map(v=>`<div class='vote-row'><div><div class='vote-name'>${v.ghost}</div><div class='vote-users'>${v.users.join(', ')}</div></div><span class='badge'>${v.count}</span></div>`).join('')}
function renderBehaviors(){let box=document.getElementById('behaviors'), q=(document.getElementById('behaviorFilter').value||'').toLowerCase(), cset=new Set(candidates().map(g=>g.name)), st=status(); box.innerHTML=''; let groups={}; for(const b of B){let logged=(state.behaviors?.[b.id]||'unknown')!=='unknown'; if(q && !(b.label+' '+b.cat+' '+b.up.join(' ')+b.down.join(' ')).toLowerCase().includes(q))continue; let relevant=b.up.some(g=>cset.has(g))||b.down.some(g=>cset.has(g)); if(!relevant&&!logged)continue; if(st.kind==='mimic'&&!logged&&!b.up.includes('The Mimic')&&!b.down.includes('The Mimic'))continue; if(['locked','verify'].includes(st.kind)&&!logged)continue; (groups[b.cat]??=[]).push(b)} for(const cat of Object.keys(groups)){let rows=groups[cat], selected=rows.find(b=>(state.behaviors?.[b.id]||'unknown')!=='unknown'), open=expanded[cat]===true; let el=document.createElement('div');el.className='branch'; let title=document.createElement('button');title.className='branch-title';title.innerHTML=`<span>${open?'▼':'▶'} ${cat}</span><span class='badge'>${selected?'logged':rows.length+' options'}</span>`;title.onclick=()=>{expanded[cat]=!open;renderBehaviors()};el.appendChild(title); if(selected){let v=state.behaviors[selected.id], div=document.createElement('div');div.className='selected '+(v==='contradicted'?'bad':'');div.innerHTML=`<strong>${v==='observed'?'✓':'×'} ${selected.label}</strong><div class='tags'>${selected.up.map(g=>`<span class='chip'>↑ ${g}</span>`).join('')}${selected.down.map(g=>`<span class='chip'>↓ ${g}</span>`).join('')}<span class='chip'>${selected.rel}</span></div><div class='row'><button data-clear='${selected.id}'>Clear</button><button class='blue' data-change='${cat}'>Change</button></div>`;el.appendChild(div)} if(open){let body=document.createElement('div');body.className='branch-body'; for(const b of rows){let opt=document.createElement('div');opt.className='option';opt.innerHTML=`<div class='option-label'>${b.label}</div><div class='tags'>${b.up.map(g=>`<span class='chip'>↑ ${g}</span>`).join('')}${b.down.map(g=>`<span class='chip'>↓ ${g}</span>`).join('')}<span class='chip'>${b.rel}</span></div><div class='grid2'><button class='green' data-beh='${b.id}' data-cat='${cat}' data-val='observed'>Observed</button><button class='red' data-beh='${b.id}' data-cat='${cat}' data-val='contradicted'>No / False</button></div>`;body.appendChild(opt)} el.appendChild(body)} box.appendChild(el)} document.querySelectorAll('[data-clear]').forEach(btn=>btn.onclick=()=>postState({behaviors:{[btn.dataset.clear]:'unknown'}}));document.querySelectorAll('[data-change]').forEach(btn=>{btn.onclick=()=>{expanded[btn.dataset.change]=true;renderBehaviors()}});document.querySelectorAll('[data-beh]').forEach(btn=>btn.onclick=()=>{let rows=B.filter(x=>x.cat===btn.dataset.cat), patch={behaviors:{}}; for(const sib of rows)patch.behaviors[sib.id]='unknown'; patch.behaviors[btn.dataset.beh]=btn.dataset.val; expanded[btn.dataset.cat]=false; postState(patch)})}
function renderOverlay(){
  document.getElementById('overlay').classList.remove('hidden');
  let c=candidates(), nx=nextEv(), st=status();
  const icon={dots:'◌',emf5:'⚡',freezing:'❄',orbs:'◉',writing:'✎',box:'▣',uv:'☝'};
  const label={dots:'D.O.T.S Projector',emf5:'EMF Level 5',freezing:'Freezing Temperatures',orbs:'Ghost Orb',writing:'Ghost Writing',box:'Spirit Box',uv:'Ultraviolet'};
  const isFinal=c.length===1 && !nx;
  document.getElementById('ovKicker').textContent=isFinal?'Final Identification':'Next Best Test';
  document.getElementById('ovStep').textContent=isFinal?c[0].name:(nx?'Test '+label[nx.ev]:st.name);
  document.getElementById('ovSub').textContent=isFinal?`Only ${c[0].name} remains. Verify with behavior before leaving.`:(nx?`${label[nx.ev]} splits ${nx.y}/${nx.n}.`+(nx.ev==='box'?` ${responseLine()}`:''):st.text);
  document.getElementById('ovGhosts').innerHTML=c.slice(0,4).map(g=>`<span class='badge'>${g.name}</span>`).join('');
  document.getElementById('ovEvidence').innerHTML=E.map(k=>`<span class='ev-dot ${state.evidence[k]==='yes'?'yes':state.evidence[k]==='no'?'no':''}' title='${label[k]}: ${state.evidence[k]}'>${state.evidence[k]==='yes'?'✓':state.evidence[k]==='no'?'×':icon[k]}</span>`).join('');
  let obs=B.filter(b=>(state.behaviors?.[b.id]||'unknown')!=='unknown');
  let votes=voteSummary().slice(0,2);
  let bits=[];
  if(obs.length){bits.push(...obs.slice(0,1).map(b=>`<span class='${state.behaviors[b.id]==='observed'?'ov-note-good':'ov-note-bad'}'>${state.behaviors[b.id]==='observed'?'✓':'×'} ${b.label}</span>`))}
  if(votes.length){bits.push(...votes.map(v=>`<span class='ov-note-vote'>${v.ghost}: ${v.count}</span>`))}
  if(!bits.length)bits.push('No behaviors or chat guesses logged.');
  document.getElementById('ovNotes').innerHTML=bits.join(' • ');
}
document.addEventListener('click',e=>{let r=e.target.dataset.responds;if(r)postState({responds:r})});document.getElementById('mode')?.addEventListener('change',e=>postState({evidenceMode:e.target.value}));document.getElementById('changeResponds')?.addEventListener('click',()=>document.getElementById('respondsChoices').classList.toggle('hidden'));document.getElementById('reset')?.addEventListener('click',()=>postState({reset:true}));document.getElementById('copyOverlay')?.addEventListener('click',()=>navigator.clipboard?.writeText(`${location.origin}/phasmo/overlay?room=${encodeURIComponent(room)}`));document.getElementById('behaviorFilter')?.addEventListener('input',renderBehaviors);
getState(); setInterval(getState, MODE==='overlay'?1000:3000);
</script></body></html>'''


def _room_name(raw: str | None) -> str:
    room = (raw or "default").strip().lower()
    room = re.sub(r"[^a-z0-9_-]", "-", room)[:64]
    return room or "default"


def _state_path(room: str) -> Path:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    return _STATE_DIR / f"{room}.json"


def default_state(room: str = "default") -> Dict[str, Any]:
    return {
        "room": room,
        "evidence": {key: "unknown" for key in EVIDENCE},
        "evidenceMode": "3",
        "responds": "unknown",
        "behaviors": {},
        "votes": {},
        "updatedAt": int(time.time() * 1000),
        "lastCommand": "",
        "lastCommandResult": "",
    }


def read_state(room: str) -> Dict[str, Any]:
    path = _state_path(room)
    if not path.exists():
        return default_state(room)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        merged = default_state(room)
        merged.update(data)
        merged["evidence"] = {**default_state(room)["evidence"], **data.get("evidence", {})}
        merged["behaviors"] = data.get("behaviors", {}) or {}
        merged["votes"] = data.get("votes", {}) or {}
        return merged
    except Exception:
        return default_state(room)


def write_state(room: str, state: Dict[str, Any]) -> Dict[str, Any]:
    state["room"] = room
    state["updatedAt"] = int(time.time() * 1000)
    _state_path(room).write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return state


def _auth_ok(x_phasmo_token: str | None, token_query: str | None) -> bool:
    if not _ADMIN_TOKEN:
        return True
    supplied = (x_phasmo_token or "").strip() or (token_query or "").strip()
    return supplied == _ADMIN_TOKEN


def _normalize_value(raw: str | None, kind: str) -> str:
    value = (raw or "").strip().lower()
    if kind == "evidence":
        if value in {"yes", "y", "true", "found", "confirm", "confirmed", "observed"}:
            return "yes"
        if value in {"no", "n", "false", "ruleout", "ruledout", "absent", "none"}:
            return "no"
        return "unknown"
    if kind == "behavior":
        if value in {"yes", "y", "true", "observed", "obs", "seen"}:
            return "observed"
        if value in {"no", "n", "false", "contradicted", "not"}:
            return "contradicted"
        return "unknown"
    return "unknown"


def _normal_user(raw: str | None) -> str:
    return (raw or "anonymous").strip().lstrip("@").lower() or "anonymous"


def _normal_ghost(raw: str | None) -> str | None:
    key = re.sub(r"[^a-z0-9]", "", (raw or "").lower())
    return GHOST_ALIASES.get(key)


def apply_command(state: Dict[str, Any], command: str, user: str | None = None) -> Tuple[Dict[str, Any], str]:
    text = (command or "").strip()
    parts = text.split()
    lower_parts = text.lower().split()
    if not parts:
        return state, "No command entered."
    cmd = lower_parts[0]

    if cmd in {"!reset", "!phasmoreset"}:
        return default_state(state.get("room", "default")), "Run reset."

    if cmd in {"!mode", "!evidencemode"}:
        mode = lower_parts[1] if len(lower_parts) > 1 else ""
        if mode in {"0", "1", "2", "3"}:
            state["evidenceMode"] = mode
            return state, f"Evidence mode set to {mode}."
        return state, "Use !mode 3, !mode 2, !mode 1, or !mode 0."

    if cmd in {"!responds", "!response", "!interact"}:
        value = lower_parts[1] if len(lower_parts) > 1 else "unknown"
        if value in {"alone", "solo"}:
            state["responds"] = "alone"
        elif value in {"everyone", "all", "group"}:
            state["responds"] = "everyone"
        else:
            state["responds"] = "unknown"
        return state, f"Responds set to {state['responds']}."

    if cmd in {"!ev", "!evidence"}:
        key = EVIDENCE_ALIASES.get(lower_parts[1], "") if len(lower_parts) > 1 else ""
        if not key:
            return state, f"Unknown evidence: {parts[1] if len(parts) > 1 else 'blank'}."
        value = _normalize_value(lower_parts[2] if len(lower_parts) > 2 else "unknown", "evidence")
        state.setdefault("evidence", {})[key] = value
        return state, f"{EVIDENCE_LABELS[key]} set to {value}."

    if cmd in {"!vote", "!guess", "!ghost"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown ghost guess: {ghost_text or 'blank'}."
        voter = _normal_user(user)
        state.setdefault("votes", {})[voter] = ghost
        return state, f"{voter} voted for {ghost}."

    if cmd in {"!unvote", "!unguess", "!clearvote"}:
        voter = _normal_user(user)
        state.setdefault("votes", {}).pop(voter, None)
        return state, f"{voter}'s vote was cleared."

    if cmd in {"!votes", "!guesses"}:
        votes = state.get("votes", {}) or {}
        if not votes:
            return state, "No ghost votes yet."
        counts: dict[str, int] = {}
        for ghost in votes.values():
            counts[ghost] = counts.get(ghost, 0) + 1
        summary = ", ".join(f"{ghost}: {count}" for ghost, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))
        return state, f"Ghost votes: {summary}."

    if cmd in {"!b", "!beh", "!behavior"}:
        if not _ALLOW_BEHAVIOR_COMMANDS:
            return state, "Behavior chat commands are disabled. Set PHASMO_ALLOW_BEHAVIOR_COMMANDS=true to enable !b commands."
        key = BEHAVIOR_ALIASES.get(lower_parts[1], "") if len(lower_parts) > 1 else ""
        if not key:
            return state, f"Unknown behavior: {parts[1] if len(parts) > 1 else 'blank'}."
        value = _normalize_value(lower_parts[2] if len(lower_parts) > 2 else "observed", "behavior")
        state.setdefault("behaviors", {})[key] = value
        return state, f"{key} set to {value}."

    return state, "Command not recognized. Try !ev emf yes, !responds alone, !vote Wraith, !mode 3, or !reset."


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "Kaizen Phasmophobia Helper",
        "control": "/phasmo/control?room=kaizen",
        "overlay": "/phasmo/overlay?room=kaizen",
        "state": "/api/phasmo/state?room=kaizen",
        "command": "/api/phasmo/command?room=kaizen",
    }


@app.get("/phasmo")
def phasmo_index(room: str | None = None):
    safe_room = _room_name(room)
    return RedirectResponse(f"/phasmo/control?room={safe_room}")


@app.get("/phasmo/control")
def phasmo_control():
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "control"))


@app.get("/phasmo/overlay")
def phasmo_overlay():
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "overlay"))


@app.get("/api/phasmo/state")
def api_get_state(room: str | None = Query(default=None)):
    safe_room = _room_name(room)
    with _STATE_LOCK:
        return read_state(safe_room)


@app.post("/api/phasmo/state")
async def api_post_state(
    request: Request,
    room: str | None = Query(default=None),
    token: str | None = Query(default=None),
    x_phasmo_token: str | None = Header(default=None),
):
    if not _auth_ok(x_phasmo_token, token):
        raise HTTPException(status_code=401, detail="unauthorized")
    safe_room = _room_name(room)
    body = await request.json()
    with _STATE_LOCK:
        current = read_state(safe_room)
        if body.get("reset") is True:
            current = default_state(safe_room)
        else:
            if "evidence" in body and isinstance(body["evidence"], dict):
                current["evidence"].update({k: v for k, v in body["evidence"].items() if k in EVIDENCE and v in {"yes", "no", "unknown"}})
            if "behaviors" in body and isinstance(body["behaviors"], dict):
                current["behaviors"].update(body["behaviors"] or {})
            if "votes" in body and isinstance(body["votes"], dict):
                current["votes"].update(body["votes"] or {})
            if "responds" in body:
                current["responds"] = body["responds"] if body["responds"] in {"unknown", "alone", "everyone"} else "unknown"
            if "evidenceMode" in body and str(body["evidenceMode"]) in {"0", "1", "2", "3"}:
                current["evidenceMode"] = str(body["evidenceMode"])
        write_state(safe_room, current)
    return {"ok": True, "state": current}


@app.post("/api/phasmo/command")
async def api_post_command(
    request: Request,
    room: str | None = Query(default=None),
    token: str | None = Query(default=None),
    x_phasmo_token: str | None = Header(default=None),
):
    if not _auth_ok(x_phasmo_token, token):
        raise HTTPException(status_code=401, detail="unauthorized")
    safe_room = _room_name(room)
    try:
        body = await request.json()
    except Exception:
        raw = (await request.body()).decode("utf-8", errors="ignore")
        body = {"command": raw}
    command = body.get("command") or body.get("rawInput") or body.get("message") or ""
    user = body.get("user") or body.get("username") or body.get("displayName") or body.get("userName") or "anonymous"
    with _STATE_LOCK:
        state = read_state(safe_room)
        state, result = apply_command(state, command, user=user)
        state["lastCommand"] = command
        state["lastCommandResult"] = result
        write_state(safe_room, state)
    return {"ok": True, "result": result, "state": state}
