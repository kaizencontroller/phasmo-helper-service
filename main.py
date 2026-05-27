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
:root{--bg:#000;--panel:#172235ee;--soft:#213149;--text:#f8fafc;--muted:#94a3b8;--line:#334155;--orange:#f97316;--green:#22c55e;--red:#ef4444;--blue:#38bdf8;--grey:#64748b}*{box-sizing:border-box}body{margin:0;background:#000;color:var(--text);font-family:Inter,system-ui,Segoe UI,sans-serif}.app{width:min(460px,100vw);height:100vh;overflow:auto;padding:10px;background:#000}.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;margin-bottom:10px;box-shadow:0 16px 40px #0007}.head{padding:12px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:8px}.body{padding:10px}.muted{color:var(--muted);font-size:12px}.badge,.chip{border:1px solid var(--line);background:#0f172a;border-radius:999px;padding:5px 8px;font-size:12px}button,select,input{background:#0f172a;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:9px 10px;font:inherit}button{cursor:pointer;touch-action:manipulation;user-select:none}button:disabled{opacity:.45;cursor:not-allowed}.green{background:#14532d;border-color:#22c55e}.red{background:#5b2329;border-color:#ef4444}.blue{background:#123247;border-color:#38bdf8}.orange{background:#432919;border-color:#f97316}.grey{background:#273244;border-color:#64748b;color:#cbd5e1}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.spread{display:flex;justify-content:space-between;align-items:center;gap:8px}.next{border-color:#f97316;background:#2a2330}.big{font-weight:950;font-size:28px;line-height:1}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}.setup-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.setup-grid label{display:grid;gap:4px;font-size:12px;color:var(--muted)}.setup-grid select,.setup-grid input{width:100%}.setup-summary{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.top-links{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.top-summary{font-size:12px;color:#cbd5e1;line-height:1.35;margin-bottom:8px}.top-summary strong{color:#fff}.setup-mode .panel{display:none}.setup-mode #setupPanel{display:block}.setup-mode #setupPanel .body{display:grid}.control-mode #setupPanel{display:none}.control-mode #setupPanel.setup-complete .body{display:none}.control-mode #setupPanel.setup-complete{margin-bottom:10px}.control-mode #setupPanel.setup-complete .head{border-bottom:0}.evidence-panel.collapsed .body{display:none}.behavior-panel.collapsed .body{display:none}.cursed-panel.collapsed .body{display:none}.cursed-grid{display:grid;gap:7px}.cursed-row{display:grid;grid-template-columns:1fr auto auto auto;gap:6px;align-items:center;border:1px solid #334155;border-radius:12px;background:#0f172a;padding:8px}.cursed-row.found{border-color:#22c55e;background:#123d29}.cursed-row.out{opacity:.62;background:#1f2937}.cursed-row.compact{grid-template-columns:1fr auto}.cursed-row.found-card{grid-template-columns:1fr auto;border-color:#22c55e;background:#123d29}.cursed-name{font-weight:900}.cursed-hint{font-size:11px;color:#94a3b8;line-height:1.25}.cursed-row button{padding:7px 8px;font-size:11px}.warnbox{border:1px solid #eab30888;background:#3b2f12;color:#fde68a;border-radius:12px;padding:8px;font-size:12px;line-height:1.35}.quick-timers{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px}.quick-timers button{padding:8px 6px;font-size:12px}.setup-chip{border:1px solid #334155;background:#0f172a;border-radius:999px;padding:4px 7px;font-size:11px;color:#cbd5e1}.evrow{display:grid;grid-template-columns:1fr 48px 48px 48px;gap:8px;align-items:center;padding:10px 0;border-bottom:1px solid #33415588}.evrow:last-child{border-bottom:0}.evname{font-weight:850;font-size:15px}.state{height:46px;padding:0;font-size:24px;font-weight:900}.state.active.yes{background:#14532d;border-color:#22c55e;box-shadow:0 0 0 2px #22c55e66}.state.active.no{background:#5b2329;border-color:#ef4444;box-shadow:0 0 0 2px #ef444466}.state.active.unk{background:#123247;border-color:#38bdf8;box-shadow:0 0 0 2px #38bdf866}.state.inactive{background:#1f2937;border-color:#475569;color:#94a3b8;opacity:.55}.ghosts{display:grid;grid-template-columns:1fr 1fr;gap:7px;max-height:260px;overflow:auto}.ghost{border:1px solid var(--line);border-radius:12px;padding:8px;background:#111a2b}.ghost.top{border-color:#22c55e;background:#132a24}.ghost h4{margin:0 0 5px;font-size:14px}.tags{display:flex;gap:4px;flex-wrap:wrap}.chip{font-size:10px;padding:3px 5px}.vote-grid{display:grid;gap:7px}.vote-row{display:flex;justify-content:space-between;align-items:center;gap:8px;border:1px solid var(--line);border-radius:10px;background:#0f172a;padding:8px}.vote-name{font-weight:900}.vote-users{color:var(--muted);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.timer-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.timer-tile{border:1px solid var(--line);border-radius:12px;background:#0f172a;padding:8px}.timer-name{font-size:10px;text-transform:uppercase;letter-spacing:.11em;color:var(--muted);font-weight:900}.timer-val{font-size:20px;font-weight:950}.timer-val.done{color:#22c55e}.manual-list{display:flex;gap:5px;flex-wrap:wrap}.manual-chip{border:1px solid #ef444477;background:#3a1d24;border-radius:999px;padding:4px 7px;font-size:11px}.branch{border:1px solid var(--line);border-radius:13px;overflow:hidden;margin-bottom:8px;background:#111a2b}.branch-title{width:100%;border:0;border-bottom:1px solid var(--line);border-radius:0;display:flex;justify-content:space-between}.branch-body{padding:8px;display:grid;gap:7px}.option{border:1px solid #334155;border-radius:11px;padding:8px;background:#0f172a}.option-label{font-weight:800;font-size:13px;margin-bottom:5px}.selected{padding:8px;background:#163425}.selected.bad{background:#3a1d24}.error{border-color:#ef4444;color:#fecaca;background:#3a1d24;padding:8px;border-radius:10px}.overlay{width:560px;height:210px;display:flex;align-items:flex-start;justify-content:flex-start;padding:8px;background:#000;overflow:hidden}.ov-card{width:544px;height:194px;background:linear-gradient(180deg,#172235f7,#0f172af2);border:2px solid #f9731688;border-radius:18px;padding:12px 14px;overflow:hidden;box-shadow:0 14px 32px #000b;transition:background .25s ease,border-color .25s ease,box-shadow .25s ease}.ov-card.final{background:linear-gradient(180deg,#14532df7,#0f2f1ef2);border-color:#22c55ecc;box-shadow:0 14px 32px #000b,0 0 22px #22c55e33}.ov-card.final .ov-kicker{color:#bbf7d0}.ov-card.final .ov-ghosts .badge{border-color:#22c55e99;background:#052e1a;color:#dcfce7}.ov-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:3px}.ov-kicker{font-size:12px;text-transform:uppercase;letter-spacing:.16em;color:var(--muted);font-weight:950}.ov-ghosts{display:flex;justify-content:flex-end;gap:5px;flex-wrap:wrap;max-width:245px;max-height:42px;overflow:hidden}.ov-ghosts .badge{font-size:11px;padding:4px 8px;background:#0b1220;border-color:#334155}.ov-step{font-size:40px;font-weight:950;line-height:.98;letter-spacing:-.045em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:2px 0 8px}.ov-step.small{font-size:34px}.ov-step.xsmall{font-size:28px}.ov-sub{font-size:14px;color:#dbeafe;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-height:18px;margin:0 0 9px}.ov-bottom{display:grid;grid-template-columns:344px 1fr;gap:12px;margin-top:0;align-items:end}.ov-evidence{display:flex;gap:5px}.ev-dot{width:44px;height:42px;border-radius:10px;border:1px solid #475569;background:#1d293a;color:#cbd5e1;display:grid;place-items:center;font-size:25px;font-weight:900;line-height:1;overflow:hidden}.ev-dot .ev-mark{font-size:25px;line-height:1}.ev-dot.yes{background:#123d29;border-color:#22c55e;color:#dcfce7}.ev-dot.no{background:#4a1f26;border-color:#ef4444;color:#fee2e2}.ov-notes{border-left:1px solid #334155aa;padding-left:10px;min-width:0;align-self:stretch;display:flex;flex-direction:column;justify-content:center}.ov-notes-title{font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:var(--muted);font-weight:950;margin-bottom:4px}.ov-note-text{font-size:12px;color:#cbd5e1;line-height:1.2;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.ov-note-good{color:#bbf7d0}.ov-note-bad{color:#fecaca}.ov-note-vote{color:#dbeafe}.hidden{display:none!important}@media(max-width:700px){.app{width:100vw}.ghosts{grid-template-columns:1fr}.evrow{grid-template-columns:1fr 52px 52px 52px}.state{height:50px}}
</style>
</head>
<body>
<div id="control" class="app hidden">
  <div class="panel top-panel"><div class="head"><div><strong>Phasmo Control</strong><div class="muted">shared room: <span id="roomLabel"></span></div></div><span class="badge" id="countBadge">0</span></div>
    <div class="body">
      <div id="authMessage" class="error hidden"></div>
      <div class="top-summary" id="controlSetupSummary">Setup not completed.</div>
      <div id="controlWeatherWarning" class="warnbox hidden"></div>
      <div class="spread"><span class="muted">Evidence mode</span><select id="mode"><option value="3">3 evidence</option><option value="2">2 evidence</option><option value="1">1 evidence</option><option value="0">0 evidence</option></select></div>
      <div class="top-links"><a class="badge" id="setupRouteLinkTop" href="#">Setup</a><a class="badge" id="leaderboardRouteLink" href="#">Leaderboard</a></div>
    </div>
  </div>
  <div class="panel" id="setupPanel"><div class="head"><div><strong>Run Setup</strong><div class="muted" id="setupSummaryLine">map, difficulty, weather, response, cursed item</div></div><span class="muted" id="setupStatus">not set</span></div><div class="body stack">
    <div id="setupAuthMessage" class="error hidden"></div>
    <div class="setup-grid">
      <label>Map / Location<select id="setupMap"><option value="unknown">Unknown</option><option>6 Tanglewood Drive</option><option>10 Ridgeview Court</option><option>13 Willow Street</option><option>42 Edgefield Road</option><option>Nell's Diner</option><option>Grafton Farmhouse</option><option>Camp Woodwind</option><option>Point Hope</option><option>Bleasdale Farmhouse</option><option>Sunny Meadows Restricted</option><option>Prison</option><option>Maple Lodge Campsite</option><option>Brownstone High School</option><option>Sunny Meadows Mental Institution</option></select></label>
      <label>Game Level / Difficulty<select id="setupDifficulty"><option value="unknown">Unknown</option><option value="amateur">Amateur</option><option value="intermediate">Intermediate</option><option value="professional">Professional</option><option value="nightmare">Nightmare</option><option value="insanity">Insanity</option><option value="custom">Custom</option></select></label>
      <label>Weather<select id="setupWeather"><option value="unknown">Unknown</option><option value="sunrise">Sunrise</option><option value="clear">Clear</option><option value="fog">Fog</option><option value="blood-moon">Blood Moon</option><option value="light-rain">Light Rain</option><option value="heavy-rain">Heavy Rain</option><option value="windy">Windy</option><option value="snow">Snow</option></select></label>
      <label>Ghost responds to<select id="setupResponds"><option value="unknown">Unknown</option><option value="everyone">Everyone</option><option value="alone">Alone</option></select></label>
    </div>
    <div class="row"><button class="green" id="saveSetup">Start / Save Setup</button></div>
    <div class="muted">Overlay will prompt chat to guess with <strong>!vote GhostName</strong>. Votes are unofficial and shown as chat context only.</div>
  </div></div>
  <div class="panel timer-panel"><div class="head"><strong>Quick Timers</strong><span class="muted" id="timerSummary">incense / hunt / cooldown</span></div><div class="body">
    <div class="quick-timers">
      <button class="blue" data-timer-cmd="!timer incense start">Incense</button>
      <button class="orange" data-timer-cmd="!timer hunt start">Hunt</button>
      <button class="blue" data-timer-cmd="!timer cooldown start">Cooldown</button>
      <button data-timer-cmd="!timer clear">Clear</button>
    </div>
    <div id="timerGrid" class="timer-grid" style="margin-top:8px"></div>
  </div></div>
  <div class="panel responds-panel"><div class="body"><div class="spread"><strong>Responds: <span id="respondsText">Unknown</span></strong><button id="changeResponds">Change</button></div><div id="respondsChoices" class="grid3" style="margin-top:8px"><button data-responds="unknown">Unknown</button><button data-responds="everyone">Everyone</button><button data-responds="alone">Alone</button></div><div class="muted" id="respondsHint" style="margin-top:8px"></div></div></div>
  <div class="panel next"><div class="body"><div class="muted" style="letter-spacing:.12em;font-weight:900">NEXT</div><div class="big" id="nextName">Loading</div><p class="muted" id="nextWhy"></p><div class="grid2"><button class="green" id="confirmNext">Confirm</button><button class="red" id="denyNext">No</button></div></div></div>
  <div class="panel action-panel"><div class="body row"><button class="orange" id="reset">Reset</button><button class="blue" id="copyOverlay">Copy Overlay URL</button></div></div>
  <div class="panel evidence-panel" id="evidencePanel"><div class="head"><strong>Evidence Board</strong><button class="btn-small" id="toggleEvidence">Collapse</button></div><div class="body" id="evidenceRows"></div></div>
  <div class="panel behavior-panel collapsed" id="behaviorPanel"><div class="head"><strong>Behavior Branches</strong><button class="btn-small" id="toggleBehavior">Expand</button></div><div class="body"><input id="behaviorFilter" placeholder="filter: speed, salt, photo" style="width:100%;margin-bottom:8px"><div id="behaviors"></div></div></div>
  <div class="panel cursed-panel" id="cursedPanel"><div class="head"><div><strong>Cursed Possession Helper</strong><div class="muted" id="cursedMapHint">Select a map in setup for location hints.</div></div><button class="btn-small" id="toggleCursed">Collapse</button></div><div class="body"><div id="cursedRows" class="cursed-grid"></div></div></div>
  <div class="panel candidates-panel"><div class="head"><strong>Candidates</strong><span class="muted" id="summary"></span></div><div class="body"><div class="ghosts" id="ghosts"></div></div></div>
  <div class="panel votes-panel"><div class="head"><strong>Chat Input</strong><span class="muted">!guess for luck, !vote for decisions</span></div><div class="body"><div id="votes" class="vote-grid"></div><p class="muted" style="margin-top:8px">Commands: !guess Deogen, !vote Wraith, !unguess, !unvote, !guesses, !votes</p></div></div>
</div>
<div id="overlay" class="overlay hidden"><section class="ov-card" id="ovCard"><div class="ov-top"><div class="ov-kicker" id="ovKicker">Next Best Test</div><div class="ov-ghosts" id="ovGhosts"></div></div><div class="ov-step" id="ovStep">Loading</div><p class="ov-sub" id="ovSub"></p><div class="ov-bottom"><div class="ov-evidence" id="ovEvidence"></div><div class="ov-notes"><div class="ov-notes-title">Notes / Chat</div><div class="ov-note-text" id="ovNotes">No behaviors or guesses.</div></div></div></section></div>
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
const CURSED_ITEMS=['Music Box','Ouija Board','Tarot Cards','Summoning Circle','Haunted Mirror','Monkey Paw','Voodoo Doll'];
const CURSED_USE={
 'Music Box':'Use it to locate the ghost by song/humming. Risk: dropping it, reaching the ghost, or running out of sanity can trigger a cursed hunt.',
 'Ouija Board':'Ask location, age, sanity, etc. Always say goodbye. Low sanity or unsafe questions can break the board and trigger a cursed hunt.',
 'Tarot Cards':'Draw one card at a time for random effects. High variance; Death starts a cursed hunt, Hanged Man can kill.',
 'Summoning Circle':'Light all candles to force a manifestation/photo opportunity. The ghost will usually transition into a cursed hunt shortly after.',
 'Haunted Mirror':'Look through it to identify the favorite room. It drains sanity while used and can break/start a cursed hunt.',
 'Monkey Paw':'Grants wishes with tradeoffs. Strong utility, but several wishes can create major danger or cursed-hunt situations.',
 'Voodoo Doll':'Push pins to force interactions. The heart pin starts a cursed hunt, and low sanity can force all pins.'
};
const CURSED_LOCATIONS={
 "6 Tanglewood Drive": {
  "Music Box": "Nursery / purple baby room shelf by the light switch.",
  "Ouija Board": "Back of basement, on a small table.",
  "Tarot Cards": "Living room / foyer corner by the couch, on a side table.",
  "Summoning Circle": "Basement, immediately at the bottom of the stairs.",
  "Haunted Mirror": "Living-room hall alcove outside the master bedroom door, on the wall.",
  "Monkey Paw": "Garage, sitting on/near the garbage bin in the corner.",
  "Voodoo Doll": "Garage corner, sitting on a garbage bin."
 },
 "42 Edgefield Road": {
  "Music Box": "First room on the left, small table next to a lamp.",
  "Ouija Board": "Kitchen-back laundry room, under shelves.",
  "Tarot Cards": "By front door, on a small table next to the key bowl.",
  "Summoning Circle": "Back of basement, next to the possible fuse box location.",
  "Haunted Mirror": "By front door, at the base of the stairs on the wall.",
  "Monkey Paw": "Upstairs kid/orange bedroom, on the baby changing table.",
  "Voodoo Doll": "Upstairs blue bedroom, on top of the bed."
 },
 "10 Ridgeview Court": {
  "Music Box": "Upstairs purple bedroom, small table by the door.",
  "Ouija Board": "Down the left hall, laundry room shelves.",
  "Tarot Cards": "By front door, on a small table next to the key bowl.",
  "Summoning Circle": "Basement, in the middle at the bottom of the staircase.",
  "Haunted Mirror": "Across from the basement staircase, on the wall.",
  "Monkey Paw": "Upstairs blue/teal bedroom, on the desk.",
  "Voodoo Doll": "Bench next to the piano."
 },
 "13 Willow Street": {
  "Music Box": "Next to the front door, on a small table.",
  "Ouija Board": "Laundry room off garage, on the washing machine.",
  "Tarot Cards": "Living room / foyer side table next to the couch.",
  "Summoning Circle": "Basement, on the 90-degree turn.",
  "Haunted Mirror": "Laundry room off garage, on the ground in the left corner.",
  "Monkey Paw": "Dining room glass display cabinet, on a shelf.",
  "Voodoo Doll": "Blue bedroom glass display cabinet; open the cabinet door."
 },
 "Grafton Farmhouse": {
  "Music Box": "Second floor small bedroom, on an end table by the bed.",
  "Ouija Board": "Third floor attic, on the ground near boxes / standing lamp.",
  "Tarot Cards": "First floor library, on the desk.",
  "Summoning Circle": "Second floor doll room, on the ground.",
  "Haunted Mirror": "Second floor master bedroom, on a table.",
  "Monkey Paw": "First floor dining room, on a side table.",
  "Voodoo Doll": "First floor seamstress/work room, on a table."
 },
 "Bleasdale Farmhouse": {
  "Music Box": "Tea room / left-hand room immediately after entering, on the china cabinet or shelf.",
  "Ouija Board": "Living room, propped on the floor against a couch.",
  "Tarot Cards": "Attic bedroom / crystal-ball room, on the table.",
  "Summoning Circle": "Utility / storage room, near the back corner.",
  "Haunted Mirror": "Trophy room / display room, on the floor near a cabinet.",
  "Monkey Paw": "Second-floor study, on the shelf behind the chair.",
  "Voodoo Doll": "Second-floor bedroom, on the seat/bench at the end of the bed."
 },
 "Camp Woodwind": {
  "Music Box": "Inside yellow tent on the left side, small table by the entrance.",
  "Ouija Board": "Right of fire pit, on the folding tables.",
  "Tarot Cards": "Left of front gate, on the second picnic table.",
  "Summoning Circle": "Straight back from the truck, by folding activity tables.",
  "Haunted Mirror": "Middle of map, base of the string-light tree.",
  "Monkey Paw": "Back curved path, on a wooden table.",
  "Voodoo Doll": "Left of bathrooms, near the red and teal tents."
 },
 "Brownstone High School": {
  "Music Box": "Entry lobby, sitting on the right-side second bench.",
  "Ouija Board": "Entry lobby, on the ground behind the left pillar.",
  "Tarot Cards": "Entry lobby, second bench on the left side.",
  "Summoning Circle": "Entry lobby, straight back by the wet floor sign.",
  "Haunted Mirror": "Entry lobby, leaning against the back of the right pillar.",
  "Monkey Paw": "Entry lobby, on a box against the front of the right pillar.",
  "Voodoo Doll": "Entry lobby, straight back on a bench by the wet floor sign."
 },
 "Prison": {
  "Music Box": "Main entry room, immediately inside on the left table in the black bin/tub.",
  "Ouija Board": "Immediate left corner of first room, behind the table with other spawns.",
  "Tarot Cards": "Immediately inside front door, left table in a white bin/tub.",
  "Summoning Circle": "Straight back from front door, back of first room.",
  "Haunted Mirror": "Main lobby, under center-right row of chairs farther into the room.",
  "Monkey Paw": "Immediately inside front door, left table by the metal detector.",
  "Voodoo Doll": "Main entry room, immediately inside on the left table in the open."
 },
 "Sunny Meadows Mental Institution": {
  "Music Box": "Chapel stage area, in one of the circle slots.",
  "Ouija Board": "Chapel stage area, in one of the circle slots.",
  "Tarot Cards": "Chapel stage area, in one of the circle slots.",
  "Summoning Circle": "Chapel stage itself; the circle is on the stage.",
  "Haunted Mirror": "Chapel stage area, in one of the circle slots.",
  "Monkey Paw": "Chapel stage, at the base of the cross near the circle.",
  "Voodoo Doll": "Chapel stage area, in one of the circle slots."
 },
 "Sunny Meadows Restricted": {
  "Music Box": "Chapel stage area, in one of the circle slots.",
  "Ouija Board": "Chapel stage area, in one of the circle slots.",
  "Tarot Cards": "Chapel stage area, in one of the circle slots.",
  "Summoning Circle": "Chapel stage itself; the circle is on the stage.",
  "Haunted Mirror": "Chapel stage area, in one of the circle slots.",
  "Monkey Paw": "Chapel stage, at the base of the cross near the circle.",
  "Voodoo Doll": "Chapel stage area, in one of the circle slots."
 },
 "Maple Lodge Campsite": {
  "Music Box": "Campfire by the totem pole, sitting on a stump through reception.",
  "Ouija Board": "Back-left restroom building alley/hallway shelf.",
  "Tarot Cards": "First picnic table outside the cabin by the lake.",
  "Summoning Circle": "First floor of lake cabin, base of staircase; cabin key is under welcome mat.",
  "Haunted Mirror": "Immediate left side of reception building, above a couch.",
  "Monkey Paw": "Right-hand area off spawn, past wood chopping, on barrel across from porta-potty.",
  "Voodoo Doll": "Left campsite from spawn, by logs around the campfire."
 },
 "Point Hope": {
  "Music Box": "Master bedroom near the top of the lighthouse.",
  "Ouija Board": "Living room area, tucked away on a shelf.",
  "Tarot Cards": "First room on the right / lower living area table.",
  "Summoning Circle": "Upper bathroom floor near the top of the lighthouse.",
  "Haunted Mirror": "Dining room, against a cupboard / cabinet.",
  "Monkey Paw": "Workshop near the top of the lighthouse.",
  "Voodoo Doll": "Kids bedroom, near the window."
 },
 "Nell's Diner": {
  "Music Box": "Manager's Office, next to the coffee machine.",
  "Ouija Board": "Storage room opposite the staff bathroom / employee-only section.",
  "Tarot Cards": "Counter area, behind the counter next to the till.",
  "Summoning Circle": "Men's Bathroom, on the floor.",
  "Haunted Mirror": "Staff room / break room, on a chair next to the vending machine.",
  "Monkey Paw": "Kitchen, on the chopping board / countertop.",
  "Voodoo Doll": "Dining Area, by a table at the back / far-left booth seat."
 }
};
const CURSED_HINTS={
 "6 Tanglewood Drive": "Small house sweep: nursery, garage, basement, dining display, living-room side table.",
 "42 Edgefield Road": "Three-floor sweep: entry/stairs, basement, orange/blue bedrooms, laundry.",
 "10 Ridgeview Court": "Check upstairs bedrooms, piano bench, basement stairs, laundry, and entry table.",
 "13 Willow Street": "Small house sweep: entry table, blue bedroom cabinet, garage laundry, basement turn.",
 "Grafton Farmhouse": "Reworked farmhouse sweep: dining/library/work room on first floor; bedrooms/doll room on second; attic for Ouija.",
 "Bleasdale Farmhouse": "Reworked farmhouse sweep: tea room, living room, utility/storage, trophy room, second-floor study/bedroom, attic crystal room.",
 "Camp Woodwind": "Outdoor sweep: tents, firepit, string-light tree, activity tables, picnic tables.",
 "Brownstone High School": "Large map shortcut: all cursed items are in the entry lobby near benches/pillars/wet floor sign.",
 "Prison": "Large map shortcut: all cursed items are in the main entry room/lobby near the left table, chairs, and metal detector.",
 "Sunny Meadows Mental Institution": "Large map shortcut: chapel stage. Most items are in circle slots; Monkey Paw is by the cross.",
 "Sunny Meadows Restricted": "Large map shortcut: chapel stage. Same cursed-item area as full Sunny Meadows.",
 "Maple Lodge Campsite": "New Maple Lodge sweep: reception/campfire, restroom alley, lake cabin, picnic table, barrel/porta-potty area.",
 "Point Hope": "Lighthouse sweep: lower living/dining first, then bedrooms/bathroom/workshop toward the top.",
 "Nell's Diner": "Diner sweep: counter, manager office, staff/break room, storage, men's bathroom, dining area, kitchen."
};
const B=[{"id":"hantu-temperature-speed","cat":"Movement Speed","label":"Speed changes with room temperature","up":["Hantu"],"down":[],"w":48,"rel":"High"},{"id":"raiju-electronics-speed","cat":"Movement Speed","label":"Speeds up near active electronics","up":["Raiju"],"down":[],"w":48,"rel":"High"},{"id":"revenant-los-speed","cat":"Movement Speed","label":"Slow searching, extremely fast after detecting a player","up":["Revenant"],"down":[],"w":52,"rel":"High"},{"id":"deogen-distance-speed","cat":"Movement Speed","label":"Very fast far away, very slow when close","up":["Deogen"],"down":[],"w":56,"rel":"High"},{"id":"dayan-moving-speed","cat":"Movement Speed","label":"Fast when a nearby player is moving","up":["Dayan"],"down":[],"w":44,"rel":"High"},{"id":"dayan-still-slow","cat":"Movement Speed","label":"Slow when nearby player stands still","up":["Dayan"],"down":[],"w":40,"rel":"High"},{"id":"twins-speed-profiles","cat":"Movement Speed","label":"Two different hunt speed profiles","up":["The Twins"],"down":[],"w":38,"rel":"Med"},{"id":"thaye-aging-speed","cat":"Movement Speed","label":"Starts fast/hyperactive, calms and slows over time","up":["Thaye"],"down":[],"w":44,"rel":"High"},{"id":"obambo-state-speed","cat":"Movement Speed","label":"Alternates calm/aggressive speed and hunt behavior","up":["Obambo"],"down":[],"w":40,"rel":"Med"},{"id":"aswang-los-ramp","cat":"Movement Speed","label":"Lower base speed but faster line-of-sight acceleration","up":["Aswang"],"down":[],"w":34,"rel":"Med"},{"id":"wraith-no-salt","cat":"Salt / Ultraviolet","label":"Does not disturb salt at all","up":["Wraith"],"down":[],"w":58,"rel":"High"},{"id":"salt-footprints","cat":"Salt / Ultraviolet","label":"Salt disturbed and UV footprints appear","up":[],"down":["Wraith"],"w":45,"rel":"High"},{"id":"gallu-no-salt-enraged","cat":"Salt / Ultraviolet","label":"Cannot disturb salt while enraged","up":["Gallu"],"down":[],"w":36,"rel":"Med"},{"id":"obake-unique-print","cat":"Salt / Ultraviolet","label":"Unique UV print such as six fingers or double switch print","up":["Obake"],"down":[],"w":58,"rel":"High"},{"id":"obake-hides-prints","cat":"Salt / Ultraviolet","label":"Repeated valid UV interactions sometimes leave no print","up":["Obake"],"down":[],"w":32,"rel":"Med"},{"id":"breaker-off-direct","cat":"Electricity / Breaker / Lights","label":"Ghost turns breaker off directly","up":["Hantu","Mare"],"down":["Jinn"],"w":30,"rel":"Med"},{"id":"breaker-on-benefit","cat":"Electricity / Breaker / Lights","label":"Performs better with breaker on","up":["Jinn","Raiju"],"down":["Hantu"],"w":22,"rel":"Low"},{"id":"jinn-breaker-speed","cat":"Electricity / Breaker / Lights","label":"Fast with breaker on, line of sight, and target over 3m away","up":["Jinn"],"down":[],"w":46,"rel":"High"},{"id":"jinn-sanity-drain","cat":"Electricity / Breaker / Lights","label":"Nearby sanity drain with EMF at fuse box","up":["Jinn"],"down":[],"w":38,"rel":"Med"},{"id":"hantu-breath-breaker-off","cat":"Electricity / Breaker / Lights","label":"Freezing breath during hunts when breaker is off or broken","up":["Hantu"],"down":[],"w":48,"rel":"High"},{"id":"mare-lights-off","cat":"Electricity / Breaker / Lights","label":"More dangerous when current room lights are off or broken","up":["Mare"],"down":[],"w":32,"rel":"Med"},{"id":"mare-no-lights-on","cat":"Electricity / Breaker / Lights","label":"Never turns lights on and may immediately turn them off","up":["Mare"],"down":[],"w":34,"rel":"Med"},{"id":"light-shatter-event","cat":"Electricity / Breaker / Lights","label":"Prefers light-shattering events","up":["Mare"],"down":[],"w":24,"rel":"Low"},{"id":"raiju-wide-interference","cat":"Electricity / Breaker / Lights","label":"Electronic interference range feels larger than normal","up":["Raiju"],"down":[],"w":34,"rel":"Med"},{"id":"yokai-short-hearing","cat":"Electricity / Breaker / Lights","label":"During hunts, only hears voice/electronics very close","up":["Yokai"],"down":[],"w":42,"rel":"High"},{"id":"early-hunt","cat":"Hunt Timing / Threshold","label":"Hunts earlier than normal sanity threshold","up":["Demon","Mare","Onryo","Thaye","Raiju","Yokai","Dayan","Kormos","Gallu","Obambo"],"down":["Shade","Deogen"],"w":30,"rel":"Med"},{"id":"demon-ability-hunt","cat":"Hunt Timing / Threshold","label":"Very early hunt that may ignore sanity","up":["Demon"],"down":[],"w":46,"rel":"Med"},{"id":"shade-shy","cat":"Hunt Timing / Threshold","label":"Will not hunt or interact while players are in the same room","up":["Shade"],"down":["Demon","Oni"],"w":42,"rel":"Med"},{"id":"yokai-talking-hunt","cat":"Hunt Timing / Threshold","label":"Talking in same room appears to enable earlier hunt","up":["Yokai"],"down":[],"w":38,"rel":"Med"},{"id":"kormos-sprint-threshold","cat":"Hunt Timing / Threshold","label":"Player sprinting in same room appears to enable earlier hunt","up":["Kormos"],"down":[],"w":36,"rel":"Med"},{"id":"aswang-zero-grace","cat":"Hunt Timing / Threshold","label":"Hunt sometimes appears to start with no grace period","up":["Aswang"],"down":[],"w":36,"rel":"Med"},{"id":"gallu-state-thresholds","cat":"Hunt Timing / Threshold","label":"Hunt threshold changes with normal/enraged/weakened state","up":["Gallu"],"down":[],"w":32,"rel":"Med"},{"id":"obambo-aggressive-hunts","cat":"Hunt Timing / Threshold","label":"Aggressive state hunts earlier but may be shorter","up":["Obambo"],"down":[],"w":34,"rel":"Med"},{"id":"deogen-late-hunt","cat":"Hunt Timing / Threshold","label":"Does not hunt until lower sanity than normal","up":["Deogen"],"down":[],"w":26,"rel":"Low"},{"id":"onryo-flame-prevent","cat":"Fire / Incense / Crucifix","label":"Lit flame nearby prevents hunts like a crucifix","up":["Onryo"],"down":[],"w":48,"rel":"High"},{"id":"onryo-third-blowout","cat":"Fire / Incense / Crucifix","label":"Hunt attempt after third flame blowout with no nearby flame","up":["Onryo"],"down":[],"w":52,"rel":"High"},{"id":"spirit-long-incense","cat":"Fire / Incense / Crucifix","label":"Incense prevents hunts much longer than normal","up":["Spirit"],"down":["Demon"],"w":48,"rel":"High"},{"id":"demon-short-incense","cat":"Fire / Incense / Crucifix","label":"Incense protection seems shorter than normal","up":["Demon"],"down":["Spirit"],"w":46,"rel":"High"},{"id":"demon-crucifix-range","cat":"Fire / Incense / Crucifix","label":"Crucifix blocks hunt from farther away than expected","up":["Demon"],"down":[],"w":32,"rel":"Med"},{"id":"gallu-crucifix-enraged","cat":"Fire / Incense / Crucifix","label":"Crucifix burn causes enraged Gallu behavior","up":["Gallu"],"down":[],"w":38,"rel":"Med"},{"id":"yurei-incense-trap","cat":"Fire / Incense / Crucifix","label":"Non-hunt incense traps it in favorite room","up":["Yurei"],"down":[],"w":32,"rel":"Med"},{"id":"phantom-photo-disappear","cat":"Ghost Events / Manifestation","label":"Ghost disappears when photographed or filmed","up":["Phantom"],"down":[],"w":58,"rel":"High"},{"id":"photo-visible","cat":"Ghost Events / Manifestation","label":"Ghost remains visible in ghost photo","up":[],"down":["Phantom"],"w":32,"rel":"Med"},{"id":"oni-no-mist","cat":"Ghost Events / Manifestation","label":"No mist-form/airball events observed after many events","up":["Oni"],"down":[],"w":34,"rel":"Med"},{"id":"oni-full-visible","cat":"Ghost Events / Manifestation","label":"Very visible during hunts or strong full-form events","up":["Oni"],"down":["Phantom"],"w":35,"rel":"Med"},{"id":"kormos-no-mist-chase","cat":"Ghost Events / Manifestation","label":"Cannot perform mist-form or chasing ghost events","up":["Kormos"],"down":[],"w":32,"rel":"Med"},{"id":"banshee-singing","cat":"Ghost Events / Manifestation","label":"Frequent singing events or unusual singing sanity drain target","up":["Banshee"],"down":[],"w":34,"rel":"Med"},{"id":"phantom-sanity-look","cat":"Ghost Events / Manifestation","label":"Looking at manifestation drains sanity unusually fast","up":["Phantom"],"down":[],"w":30,"rel":"Low"},{"id":"myling-quiet-footsteps","cat":"Sound / Spirit Box","label":"Hunt footsteps/vocalizations only audible when close","up":["Myling"],"down":[],"w":46,"rel":"High"},{"id":"banshee-scream","cat":"Sound / Spirit Box","label":"Banshee scream on parabolic microphone","up":["Banshee"],"down":[],"w":48,"rel":"High"},{"id":"deogen-spiritbox-breath","cat":"Sound / Spirit Box","label":"Deogen breathing response on Spirit Box","up":["Deogen"],"down":[],"w":44,"rel":"High"},{"id":"moroi-curse","cat":"Sound / Spirit Box","label":"Cursed player drains sanity rapidly after paranormal audio/contact","up":["Moroi"],"down":[],"w":42,"rel":"Med"},{"id":"box-alone-mismatch","cat":"Sound / Spirit Box","label":"Spirit Box only works under correct alone/everyone condition","up":[],"down":[],"w":0,"rel":"Context"},{"id":"goryo-camera-dots","cat":"Room / Roaming / D.O.T.S","label":"D.O.T.S visible on camera only, not naked eye","up":["Goryo"],"down":[],"w":50,"rel":"High"},{"id":"goryo-room-stable","cat":"Room / Roaming / D.O.T.S","label":"Favorite room does not naturally change","up":["Goryo"],"down":[],"w":28,"rel":"Low"},{"id":"thaye-high-activity-early","cat":"Room / Roaming / D.O.T.S","label":"Very high activity early, lower activity later","up":["Thaye"],"down":[],"w":36,"rel":"Med"},{"id":"mare-long-roam-lights-on","cat":"Room / Roaming / D.O.T.S","label":"Seems to roam farther when lights are on","up":["Mare"],"down":[],"w":20,"rel":"Low"},{"id":"yurei-door-room","cat":"Room / Roaming / D.O.T.S","label":"Strong door ability or favorite-room trapping behavior","up":["Yurei"],"down":[],"w":38,"rel":"Med"},{"id":"banshee-target","cat":"Targeting / Awareness","label":"Only one player seems targeted during hunts","up":["Banshee"],"down":[],"w":42,"rel":"Med"},{"id":"deogen-knows-location","cat":"Targeting / Awareness","label":"Always knows where players are during hunts","up":["Deogen"],"down":[],"w":44,"rel":"High"},{"id":"kormos-no-los","cat":"Targeting / Awareness","label":"No visual line-of-sight; detects voice/electronics/footsteps instead","up":["Kormos"],"down":[],"w":50,"rel":"High"},{"id":"aswang-hidden-spares","cat":"Targeting / Awareness","label":"Reaches correctly hidden player and hunt ends instead of killing","up":["Aswang"],"down":[],"w":58,"rel":"High"},{"id":"wraith-teleport","cat":"Targeting / Awareness","label":"Teleports to player and leaves EMF at feet level","up":["Wraith"],"down":[],"w":32,"rel":"Med"},{"id":"phantom-travel","cat":"Targeting / Awareness","label":"Travels to random player and leaves EMF at head level","up":["Phantom"],"down":[],"w":28,"rel":"Low"},{"id":"polter-multi-throw","cat":"Object / Interaction","label":"Object pile explosion or many throws at once","up":["Poltergeist"],"down":[],"w":55,"rel":"High"},{"id":"polter-hunt-throw-rate","cat":"Object / Interaction","label":"Throws objects constantly during hunts","up":["Poltergeist"],"down":[],"w":44,"rel":"High"},{"id":"twins-double-interaction","cat":"Object / Interaction","label":"Near-simultaneous interactions in separate places","up":["The Twins"],"down":[],"w":42,"rel":"Med"},{"id":"shade-low-interaction","cat":"Object / Interaction","label":"Low interaction/events while players are near the ghost","up":["Shade"],"down":["Oni","Poltergeist"],"w":34,"rel":"Med"},{"id":"obake-shapeshift","cat":"Object / Interaction","label":"Brief shapeshift/model flicker during hunt","up":["Obake"],"down":[],"w":52,"rel":"High"},{"id":"mimic-fake-orbs","cat":"Mimic / Special Cases","label":"Ghost Orbs plus impossible evidence combo","up":["The Mimic"],"down":[],"w":60,"rel":"High"},{"id":"mimic-changing-tells","cat":"Mimic / Special Cases","label":"Behavior tells change between hunts or over time","up":["The Mimic"],"down":[],"w":44,"rel":"Med"}];
let state={evidence:{},behaviors:{},votes:{},responds:'unknown',evidenceMode:'3'}; let expanded={}; let evidenceCollapsed=localStorage.getItem('phasmoEvidenceCollapsed')==='true'; let behaviorCollapsed=localStorage.getItem('phasmoBehaviorCollapsed')==='true'; let cursedCollapsed=localStorage.getItem('phasmoCursedCollapsed')==='true';
function apiUrl(path){return `${API}${path}?room=${encodeURIComponent(room)}${token?'&token='+encodeURIComponent(token):''}`}
async function getState(){let r=await fetch(`${API}/state?room=${encodeURIComponent(room)}`);state=await r.json();render();}
async function postState(patch){
  let r=await fetch(apiUrl('/state'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});
  if(!r.ok){
    showAuthError('Update blocked. If PHASMO_ADMIN_TOKEN is set, open this page with &token=YOUR_TOKEN once.');
    return false;
  }
  let data=await r.json().catch(()=>null);
  if(data&&data.state){state=data.state;render();}else{await getState();}
  return true;
}
async function command(cmd,user='control'){
  let r=await fetch(apiUrl('/command'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd,user:user})});
  if(!r.ok){
    showAuthError('Command blocked. Token missing or invalid.');
    return false;
  }
  await getState();
  return true;
}
function showAuthError(msg){
  ['authMessage','setupAuthMessage'].forEach(id=>{
    let box=document.getElementById(id);
    if(box){box.textContent=msg;box.classList.remove('hidden');}
  });
}
function impact(g){let s=0; for(const b of B){let v=state.behaviors?.[b.id]||'unknown'; if(v==='observed'){if(b.up.includes(g.name))s+=b.w;if(b.down.includes(g.name))s-=b.w} if(v==='contradicted'){if(b.up.includes(g.name))s-=Math.round(b.w*.65);if(b.down.includes(g.name))s+=Math.round(b.w*.45)}} return s}
function candidates(){let manual=state.manualGhosts||{}, selected=manual.selected||null, excluded=new Set(manual.excluded||[]), yes=E.filter(k=>state.evidence[k]==='yes'), no=E.filter(k=>state.evidence[k]==='no'), mode=+state.evidenceMode; let pool=G.filter(g=>{if(selected)return g.name===selected; if(excluded.has(g.name))return false; if(mode===0&&!yes.length)return true; if(!yes.every(e=>g.ev.includes(e)||(g.name==='The Mimic'&&e==='orbs')))return false; if(mode===3&&no.some(e=>g.ev.includes(e)||(g.name==='The Mimic'&&e==='orbs')))return false; return true}); return pool.map(g=>({...g,impact:impact(g),score:(selected&&g.name===selected?999:0)+impact(g)+yes.filter(e=>g.ev.includes(e)).length*22+(g.name==='The Mimic'&&yes.includes('orbs')?12:0)})).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name))}
function status(){let c=candidates(), yes=E.filter(k=>state.evidence[k]==='yes'), mode=+state.evidenceMode, target=mode>0&&yes.length>=mode, mimic=c.some(g=>g.name==='The Mimic'); if(!c.length)return{kind:'conflict',name:'Retest',text:'No ghost matches. Recheck evidence.'}; if(target&&c.length===1)return{kind:'locked',name:`Final ID: ${c[0].name}`,text:'Evidence target reached. Behavior is sanity-check only.'}; if(target&&mimic)return{kind:'mimic',name:'Mimic Check',text:'Evidence target reached, but Mimic remains possible.'}; if(target)return{kind:'locked',name:`Likely: ${c[0].name}`,text:'Evidence target reached. Resolve contradictions only.'}; if(c.length===1)return{kind:'verify',name:`Verify ${c[0].name}`,text:'One candidate remains. Final disconfirming check.'}; return{kind:'open',name:'Investigating',text:'Continue evidence collection.'}}
function nextEv(){let st=status(); if(['locked','conflict','verify'].includes(st.kind))return null; let c=candidates(), unk=E.filter(e=>state.evidence[e]==='unknown'); if(c.length<=1||!unk.length)return null; return unk.map(ev=>{let y=0,n=0; for(const g of c){let has=g.ev.includes(ev)||(g.name==='The Mimic'&&ev==='orbs'); has?y++:n++} let split=Math.min(y,n), swing=Math.abs(y-n); return{ev,y,n,split,score:split*10-swing-(ev==='box'&&state.responds==='unknown'?2:0)}}).sort((a,b)=>b.score-a.score||b.split-a.split||a.swing-b.swing)[0]}
function nextBehavior(){let c=candidates(); if(c.length<=1)return null; let cset=new Set(c.map(g=>g.name)); let rows=B.filter(b=>{let v=state.behaviors?.[b.id]||'unknown'; if(v!=='unknown')return false; return b.up.some(g=>cset.has(g))||b.down.some(g=>cset.has(g));}); if(!rows.length)return null; return rows.map(b=>{let up=b.up.filter(g=>cset.has(g)).length, down=b.down.filter(g=>cset.has(g)).length, rel=b.rel==='High'?12:b.rel==='Med'?6:0; return {...b,score:b.w+rel+Math.max(up,down)*8}}).sort((a,b)=>b.score-a.score||b.w-a.w)[0]}
function activeTimers(){let now=Date.now(), out=[]; for(const [k,t] of Object.entries(state.timers||{})){if(!t?.running)continue; let remain=Math.ceil(((t.startedAt||now)+(t.durationSeconds||60)*1000-now)/1000); out.push({key:k,remain,duration:t.durationSeconds||60})} return out.sort((a,b)=>a.remain-b.remain)}
function fmtTimer(s){if(s<=0)return 'done'; let m=Math.floor(s/60), r=String(s%60).padStart(2,'0'); return `${m}:${r}`}

function voteSummary(kind='votes'){let source=kind==='guesses'?(state.guesses||{}):(state.votes||{});let counts={}; for(const [user,ghost] of Object.entries(source)){counts[ghost]??=[];counts[ghost].push(user)} return Object.entries(counts).map(([ghost,users])=>({ghost,users,count:users.length})).sort((a,b)=>b.count-a.count||a.ghost.localeCompare(b.ghost))}
function responseLine(){let r=state.responds||'unknown'; if(r==='alone')return 'Spirit Box board: responds to people who are alone.'; if(r==='everyone')return 'Spirit Box board: responds to everyone.'; return 'Spirit Box response condition unknown. Test solo and group before ruling out.';}
function weatherWarnings(){
  const w=(state.weather||'unknown').toLowerCase();
  const notes=[];
  if(w==='sunrise')notes.push('Warmest weather group: rooms start warmer, so early temperature reads may take longer to separate.');
  if(w==='fog')notes.push('Fog can make visual reads and Ghost Orb confirmation harder. Confirm with deliberate camera sweeps.');
  if(w==='blood-moon')notes.push('Blood Moon is special-event weather. Treat visibility and ambient assumptions with caution.');
  if(w==='light-rain'||w==='heavy-rain')notes.push('Rain can mask quiet audio cues and footsteps. Be careful with Myling-style sound reads.');
  if(w==='heavy-rain')notes.push('Heavy Rain is especially noisy; do not overtrust subtle audio.');
  if(w==='snow')notes.push('Snow is the coldest weather group. Trust thermometer thresholds, not visual cold vibes.');
  if(w==='windy')notes.push('Wind can mask subtle throw/door/audio cues.');
  return notes;
}
function titleCase(s){return (s||'unknown').split(/[- ]+/).map(x=>x?x[0].toUpperCase()+x.slice(1):x).join(' ')}
function setupSummary(){
  const bits=[];
  if(state.map)bits.push(state.map);
  if(state.difficulty&&state.difficulty!=='unknown')bits.push(titleCase(state.difficulty));
  if(state.weather&&state.weather!=='unknown')bits.push(titleCase(state.weather));
  if(state.responds&&state.responds!=='unknown')bits.push('Responds: '+titleCase(state.responds));
  return bits.length?bits.join(' • '):'map, difficulty, weather, response';
}
function renderSetup(){
  const setupPanel=document.getElementById('setupPanel'); if(!setupPanel)return;
  document.body.classList.toggle('setup-mode', MODE==='setup');
  document.body.classList.toggle('control-mode', MODE==='control');
  setupPanel.classList.toggle('setup-complete', MODE==='control' && state.setupComplete===true);
  document.getElementById('setupMap').value=state.map||'unknown';
  document.getElementById('setupDifficulty').value=state.difficulty||'unknown';
  document.getElementById('setupWeather').value=state.weather||'unknown';
  document.getElementById('setupResponds').value=state.responds||'unknown';
  const done=state.setupComplete===true;
  document.getElementById('setupStatus').textContent=done?'ready':'setup recommended';
  document.getElementById('setupSummaryLine').textContent=setupSummary();
  const notes=weatherWarnings();
  const controlWarn=document.getElementById('controlWeatherWarning');
  if(controlWarn){
    if(notes.length){controlWarn.innerHTML='<strong>Weather caution:</strong> '+notes.join(' ');controlWarn.classList.remove('hidden')} else {controlWarn.classList.add('hidden')}
  }
  const setupHref=`/phasmo/setup?room=${encodeURIComponent(room)}${token?'&token='+encodeURIComponent(token):''}`;
  const setupLink=document.getElementById('setupRouteLink');
  if(setupLink)setupLink.href=setupHref;
  const setupTop=document.getElementById('setupRouteLinkTop');
  if(setupTop)setupTop.href=setupHref;
  const leaderboardLink=document.getElementById('leaderboardRouteLink');
  if(leaderboardLink)leaderboardLink.href=`/phasmo/leaderboard?room=${encodeURIComponent(room)}${token?'&token='+encodeURIComponent(token):''}`;
  const controlSummary=document.getElementById('controlSetupSummary');
  if(controlSummary){
    const parts=[];
    if(state.map&&state.map!=='unknown')parts.push(`<strong>${state.map}</strong>`);
    if(state.difficulty&&state.difficulty!=='unknown')parts.push(titleCase(state.difficulty));
    if(state.weather&&state.weather!=='unknown')parts.push(titleCase(state.weather));
    if(state.responds&&state.responds!=='unknown')parts.push('Responds: '+titleCase(state.responds));
    controlSummary.innerHTML=parts.length?parts.join(' • '):'Setup not completed.';
  }
}
function render(){ if(MODE==='overlay')renderOverlay(); else renderControl(); }
function renderCursedHelper(){
  const box=document.getElementById('cursedRows'); if(!box)return;
  const map=state.map||'unknown';
  const hint=CURSED_HINTS[map]||'Select a map in setup for location hints. Default contracts usually have one cursed item, so clear known spawns as you check them.';
  document.getElementById('cursedMapHint').textContent=hint;
  const statuses=state.cursedItems||{};
  const found=CURSED_ITEMS.find(item=>(statuses[item.toLowerCase()]||'unknown')==='found');
  if(found){
    const key=found.toLowerCase();
    const loc=(CURSED_LOCATIONS[map]&&CURSED_LOCATIONS[map][found])||'Known spawn for selected map not loaded.';
    const use=CURSED_USE[found]||'Use carefully. Cursed possessions can trigger dangerous/cursed hunt situations.';
    box.innerHTML=`<div class='cursed-row found-card'><div><div class='cursed-name'>${found}</div><div class='cursed-hint'><strong>Location:</strong> ${loc}<br><strong>Use:</strong> ${use}</div></div><button data-cursed='${key}' data-cursed-val='unknown'>Undo</button></div>`;
    document.querySelectorAll('[data-cursed]').forEach(btn=>btn.onclick=()=>postState({cursedItems:{[btn.dataset.cursed]:btn.dataset.cursedVal}}));
    return;
  }
  box.innerHTML=CURSED_ITEMS.map(item=>{
    const key=item.toLowerCase();
    const val=statuses[key]||'unknown';
    const loc=(CURSED_LOCATIONS[map]&&CURSED_LOCATIONS[map][item])||hint;
    if(val==='out'){
      return `<div class='cursed-row out compact'><div><div class='cursed-name'>${item}</div><div class='cursed-hint'>Cleared / not present.</div></div><button data-cursed='${key}' data-cursed-val='unknown'>Undo</button></div>`;
    }
    return `<div class='cursed-row'><div><div class='cursed-name'>${item}</div><div class='cursed-hint'>${loc}</div></div><button class='green' data-cursed='${key}' data-cursed-val='found'>Found</button><button class='grey' data-cursed='${key}' data-cursed-val='out'>Not Present</button><button data-cursed='${key}' data-cursed-val='unknown'>?</button></div>`;
  }).join('');
  document.querySelectorAll('[data-cursed]').forEach(btn=>btn.onclick=()=>postState({cursedItems:{[btn.dataset.cursed]:btn.dataset.cursedVal}}));
}
function renderControl(){document.getElementById('control').classList.remove('hidden');renderSetup();document.getElementById('roomLabel').textContent=room;document.getElementById('mode').value=state.evidenceMode;let c=candidates();document.getElementById('countBadge').textContent=c.length+' candidates';document.getElementById('summary').textContent=`${E.filter(k=>state.evidence[k]==='yes').length} confirmed`;let r=state.responds||'unknown';document.getElementById('respondsText').textContent=r[0].toUpperCase()+r.slice(1);document.getElementById('respondsChoices').classList.toggle('hidden',r!=='unknown');document.getElementById('respondsHint').textContent=responseLine();
 document.querySelector('.responds-panel')?.classList.toggle('hidden', state.setupComplete===true);
 document.getElementById('evidencePanel')?.classList.toggle('collapsed', evidenceCollapsed);
 const evToggle=document.getElementById('toggleEvidence'); if(evToggle)evToggle.textContent=evidenceCollapsed?'Expand':'Collapse';
 document.getElementById('behaviorPanel')?.classList.toggle('collapsed', behaviorCollapsed);
 const behaviorToggle=document.getElementById('toggleBehavior'); if(behaviorToggle)behaviorToggle.textContent=behaviorCollapsed?'Expand':'Collapse';
 document.getElementById('cursedPanel')?.classList.toggle('collapsed', cursedCollapsed);
 const cursedToggle=document.getElementById('toggleCursed'); if(cursedToggle)cursedToggle.textContent=cursedCollapsed?'Expand':'Collapse';
 let nx=nextEv(), nb=nextBehavior(), st=status(); document.getElementById('nextName').textContent=nx?EL[nx.ev]:(nb?'Behavior: '+nb.cat:st.name); document.getElementById('nextWhy').textContent=nx?`${EL[nx.ev]} splits ${nx.y}/${nx.n}.`+(nx.ev==='box'?` ${responseLine()}`:''):(nb?`${nb.label}. Supports: ${nb.up.join(', ')||'context'}${nb.down.length?`; argues against: ${nb.down.join(', ')}`:''}.`:st.text); document.getElementById('confirmNext').disabled=!(nx||nb);document.getElementById('denyNext').disabled=!(nx||nb);document.getElementById('confirmNext').textContent=nx?'Confirm '+EL[nx.ev]:(nb?'Observed':'Confirmed');document.getElementById('denyNext').textContent=nx?'No '+EL[nx.ev]:(nb?'No / False':'No more evidence'); if(nx){document.getElementById('confirmNext').onclick=()=>postState({evidence:{[nx.ev]:'yes'}});document.getElementById('denyNext').onclick=()=>postState({evidence:{[nx.ev]:'no'}})} else if(nb){document.getElementById('confirmNext').onclick=()=>postState({behaviors:{[nb.id]:'observed'}});document.getElementById('denyNext').onclick=()=>postState({behaviors:{[nb.id]:'contradicted'}})}
 renderTimers(); renderManualGhosts(); renderCursedHelper();
 document.getElementById('evidenceRows').innerHTML=E.map(k=>{let v=state.evidence[k]||'unknown'; let cls=(want)=>`state ${want} ${v===want?'active':'inactive'}`; return `<div class='evrow'><span class='evname'>${EL[k]}</span><button class='${cls('yes')}' data-ev='${k}' data-val='yes'>✓</button><button class='${cls('unk')}' data-ev='${k}' data-val='unknown'>?</button><button class='${cls('no')}' data-ev='${k}' data-val='no'>×</button></div>`}).join(''); document.querySelectorAll('[data-ev]').forEach(btn=>btn.onclick=()=>postState({evidence:{[btn.dataset.ev]:btn.dataset.val}}));
 document.getElementById('ghosts').innerHTML=c.slice(0,8).map((g,i)=>`<div class='ghost ${i===0&&g.score>0?'top':''}'><h4>${g.name}</h4><div class='tags'>${g.ev.map(e=>`<span class='chip'>${EL[e]}</span>`).join('')}${g.ev.includes('box')?`<span class='chip blue'>${state.responds==='alone'?'Box: Alone':state.responds==='everyone'?'Box: Everyone':'Box: Unknown response'}</span>`:''}</div><div class='muted'>${g.impact?`${g.impact>0?'+':''}${g.impact} behavior`:'No behavior'}</div></div>`).join(''); renderVotes(); renderBehaviors();}

function renderTimers(){let box=document.getElementById('timerGrid'); if(!box)return; let timers=['incense','hunt','cooldown']; let map=Object.fromEntries(activeTimers().map(t=>[t.key,t])); box.innerHTML=timers.map(k=>{let t=map[k], val=t?fmtTimer(t.remain):'—'; return `<div class='timer-tile'><div class='timer-name'>${k}</div><div class='timer-val ${t&&t.remain<=0?'done':''}'>${val}</div></div>`}).join('')}
function renderManualGhosts(){let box=document.getElementById('manualGhostSummary'); if(!box)return; let manual=state.manualGhosts||{}, bits=[]; if(manual.selected)bits.push(`<span class='chip green'>Selected: ${manual.selected}</span>`); for(const g of (manual.excluded||[]))bits.push(`<span class='manual-chip'>Out: ${g}</span>`); box.innerHTML=bits.length?`<div class='manual-list'>${bits.join('')}</div>`:'No manual overrides.'}

function renderVotes(){let box=document.getElementById('votes');let votes=voteSummary('votes'), guesses=voteSummary('guesses'); let html=''; html+=`<div class='muted' style='margin-bottom:6px'><strong>Votes</strong> are useful decision input when we ask chat to help choose. <strong>Guesses</strong> are lucky predictions.</div>`; if(votes.length){html+=`<div class='vote-section'><div class='muted' style='margin:6px 0'>Decision Votes — !vote GhostName</div>${votes.map(v=>`<div class='vote-row'><div><div class='vote-name'>${v.ghost}</div><div class='vote-users'>${v.users.join(', ')}</div></div><span class='badge'>${v.count}</span></div>`).join('')}</div>`} else html+=`<p class='muted'>No decision votes yet. Use !vote when we need chat's help choosing.</p>`; if(guesses.length){html+=`<div class='vote-section'><div class='muted' style='margin:10px 0 6px'>Lucky Guesses — !guess GhostName</div>${guesses.map(v=>`<div class='vote-row'><div><div class='vote-name'>${v.ghost}</div><div class='vote-users'>${v.users.join(', ')}</div></div><span class='badge'>${v.count}</span></div>`).join('')}</div>`} else html+=`<p class='muted'>No lucky guesses yet. Use !guess before evidence comes in.</p>`; box.innerHTML=html}
function renderBehaviors(){let box=document.getElementById('behaviors'), q=(document.getElementById('behaviorFilter').value||'').toLowerCase(), cset=new Set(candidates().map(g=>g.name)), st=status(); box.innerHTML=''; let groups={}; for(const b of B){let logged=(state.behaviors?.[b.id]||'unknown')!=='unknown'; if(q && !(b.label+' '+b.cat+' '+b.up.join(' ')+b.down.join(' ')).toLowerCase().includes(q))continue; let relevant=b.up.some(g=>cset.has(g))||b.down.some(g=>cset.has(g)); if(!relevant&&!logged)continue; if(st.kind==='mimic'&&!logged&&!b.up.includes('The Mimic')&&!b.down.includes('The Mimic'))continue; if(['locked','verify'].includes(st.kind)&&!logged)continue; (groups[b.cat]??=[]).push(b)} for(const cat of Object.keys(groups)){let rows=groups[cat], selected=rows.find(b=>(state.behaviors?.[b.id]||'unknown')!=='unknown'), open=expanded[cat]===true; let el=document.createElement('div');el.className='branch'; let title=document.createElement('button');title.className='branch-title';title.innerHTML=`<span>${open?'▼':'▶'} ${cat}</span><span class='badge'>${selected?'logged':rows.length+' options'}</span>`;title.onclick=()=>{expanded[cat]=!open;renderBehaviors()};el.appendChild(title); if(selected){let v=state.behaviors[selected.id], div=document.createElement('div');div.className='selected '+(v==='contradicted'?'bad':'');div.innerHTML=`<strong>${v==='observed'?'✓':'×'} ${selected.label}</strong><div class='tags'>${selected.up.map(g=>`<span class='chip'>↑ ${g}</span>`).join('')}${selected.down.map(g=>`<span class='chip'>↓ ${g}</span>`).join('')}<span class='chip'>${selected.rel}</span></div><div class='row'><button data-clear='${selected.id}'>Clear</button><button class='blue' data-change='${cat}'>Change</button></div>`;el.appendChild(div)} if(open){let body=document.createElement('div');body.className='branch-body'; for(const b of rows){let opt=document.createElement('div');opt.className='option';opt.innerHTML=`<div class='option-label'>${b.label}</div><div class='tags'>${b.up.map(g=>`<span class='chip'>↑ ${g}</span>`).join('')}${b.down.map(g=>`<span class='chip'>↓ ${g}</span>`).join('')}<span class='chip'>${b.rel}</span></div><div class='grid2'><button class='green' data-beh='${b.id}' data-cat='${cat}' data-val='observed'>Observed</button><button class='red' data-beh='${b.id}' data-cat='${cat}' data-val='contradicted'>No / False</button></div>`;body.appendChild(opt)} el.appendChild(body)} box.appendChild(el)} document.querySelectorAll('[data-clear]').forEach(btn=>btn.onclick=()=>postState({behaviors:{[btn.dataset.clear]:'unknown'}}));document.querySelectorAll('[data-change]').forEach(btn=>{btn.onclick=()=>{expanded[btn.dataset.change]=true;renderBehaviors()}});document.querySelectorAll('[data-beh]').forEach(btn=>btn.onclick=()=>{let rows=B.filter(x=>x.cat===btn.dataset.cat), patch={behaviors:{}}; for(const sib of rows)patch.behaviors[sib.id]='unknown'; patch.behaviors[btn.dataset.beh]=btn.dataset.val; expanded[btn.dataset.cat]=false; postState(patch)})}
function setupOverlay(){
  const phase=Math.floor(Date.now()/5000)%3;
  const guesses=voteSummary('guesses').slice(0,3);
  const votes=voteSummary('votes').slice(0,3);
  const short={dots:'DOT',emf5:'EMF',freezing:'TMP',orbs:'ORB',writing:'WRT',box:'BOX',uv:'UV'};
  const icon={dots:'◌',emf5:'⚡',freezing:'❄',orbs:'◉',writing:'✎',box:'▣',uv:'☝'};
  document.getElementById('ovCard')?.classList.remove('final');
  document.getElementById('ovKicker').textContent='PRE-GAME';
  const ovStep=document.getElementById('ovStep');
  ovStep.classList.remove('small','xsmall');
  if(phase===0){
    ovStep.textContent='LUCKY GUESSES';
    document.getElementById('ovSub').textContent=guesses.length?guesses.map(v=>`${v.ghost} ${v.count}`).join(' • '):'Type !guess GhostName before evidence comes in.';
  } else if(phase===1){
    ovStep.textContent='CHAT INPUT';
    document.getElementById('ovSub').textContent=votes.length?`Decision votes: ${votes.map(v=>`${v.ghost} ${v.count}`).join(' • ')}`:'Use !vote GhostName when chat is helping make a call.';
  } else {
    ovStep.textContent='COMMANDS';
    document.getElementById('ovSub').textContent='!guess for luck • !vote when asked • !votes / !guesses';
  }
  if(ovStep.textContent.length>16) ovStep.classList.add('small');
  document.getElementById('ovGhosts').innerHTML='';
  document.getElementById('ovEvidence').innerHTML=E.map(k=>`<span class='ev-dot' title='${EL[k]}'><span class='ev-mark'>${icon[k]}</span></span>`).join('');
  document.getElementById('ovNotes').innerHTML=(state.map&&state.map!=='unknown')?`${state.map}${state.difficulty&&state.difficulty!=='unknown'?' • '+titleCase(state.difficulty):''}`:'Setup in progress';
}
function renderOverlay(){
  document.getElementById('overlay').classList.remove('hidden');
  if(state.setupComplete!==true){setupOverlay();return;}
  let c=candidates(), nx=nextEv(), nb=nextBehavior(), st=status();
  const icon={dots:'◌',emf5:'⚡',freezing:'❄',orbs:'◉',writing:'✎',box:'▣',uv:'☝'};
  const short={dots:'DOT',emf5:'EMF',freezing:'TMP',orbs:'ORB',writing:'WRT',box:'BOX',uv:'UV'};
  const shortName={dots:'DOTS',emf5:'EMF 5',freezing:'FREEZING',orbs:'ORB',writing:'WRITING',box:'SPIRIT BOX',uv:'UV'};
  const label={dots:'D.O.T.S Projector',emf5:'EMF Level 5',freezing:'Freezing Temperatures',orbs:'Ghost Orb',writing:'Ghost Writing',box:'Spirit Box',uv:'Ultraviolet'};
  const isFinal=c.length===1 && !nx;
  document.getElementById('ovCard')?.classList.toggle('final', isFinal);
  document.getElementById('ovKicker').textContent=isFinal?'GHOST':'NEXT TEST';

  let stepText=isFinal?c[0].name:(nx?shortName[nx.ev]:(nb?('CHECK '+nb.cat.split('/')[0].trim().toUpperCase()):st.name.toUpperCase()));
  const ovStep=document.getElementById('ovStep');
  ovStep.textContent=stepText;
  ovStep.classList.remove('small','xsmall');
  if(stepText.length>18) ovStep.classList.add('xsmall');
  else if(stepText.length>13) ovStep.classList.add('small');

  let subText='';
  if(isFinal){
    subText='Only ghost remaining. Verify behavior before leaving.';
  } else if(nx){
    subText=`${label[nx.ev]} split: ${nx.y}/${nx.n}`;
    if(nx.ev==='box' && state.responds && state.responds!=='unknown') subText+=` • Responds: ${titleCase(state.responds)}`;
  } else if(nb){
    subText=nb.label;
  } else {
    subText=st.text;
  }
  document.getElementById('ovSub').textContent=subText;

  let ghostBits=c.slice(0,3).map(g=>`<span class='badge'>${g.name}</span>`);
  if(c.length>3) ghostBits.push(`<span class='badge'>+${c.length-3}</span>`);
  document.getElementById('ovGhosts').innerHTML=ghostBits.join('');

  document.getElementById('ovEvidence').innerHTML=E.map(k=>{
    const v=state.evidence[k]||'unknown';
    return `<span class='ev-dot ${v==='yes'?'yes':v==='no'?'no':''}' title='${label[k]}: ${v}'><span class='ev-mark'>${icon[k]}</span></span>`;
  }).join('');

  let obs=B.filter(b=>(state.behaviors?.[b.id]||'unknown')!=='unknown');
  let votes=voteSummary('votes').slice(0,1);
  let guesses=voteSummary('guesses').slice(0,1);
  let timers=activeTimers().slice(0,1);
  let bits=[];
  if(timers.length){bits.push(...timers.map(t=>`<span class='ov-note-vote'>${titleCase(t.key)} ${fmtTimer(Math.max(0,t.remain))}</span>`))}
  if(obs.length){bits.push(...obs.slice(0,1).map(b=>`<span class='${state.behaviors[b.id]==='observed'?'ov-note-good':'ov-note-bad'}'>${state.behaviors[b.id]==='observed'?'✓':'×'} ${b.label}</span>`))}
  if(votes.length){bits.push(...votes.map(v=>`<span class='ov-note-vote'>Vote ${v.ghost}: ${v.count}</span>`))}
  if(guesses.length && bits.length<2){bits.push(...guesses.map(v=>`<span class='ov-note-vote'>Guess ${v.ghost}: ${v.count}</span>`))}
  if(!bits.length)bits.push('!guess for luck • !vote when asked');
  const cautions=weatherWarnings();
  if(cautions.length && bits.length<2) bits.push(`<span class='ov-note-vote'>Weather caution</span>`);
  document.getElementById('ovNotes').innerHTML=bits.join(' • ');
}
document.addEventListener('click',e=>{let r=e.target.dataset.responds;if(r)postState({responds:r}); let tc=e.target.dataset.timerCmd;if(tc)command(tc,'control')});
document.getElementById('saveSetup')?.addEventListener('click',async()=>{
  const ok=await postState({setupComplete:true,map:document.getElementById('setupMap').value,difficulty:document.getElementById('setupDifficulty').value,weather:document.getElementById('setupWeather').value,responds:document.getElementById('setupResponds').value});
  if(ok && MODE==='setup') location.href=`/phasmo/control?room=${encodeURIComponent(room)}${token?'&token='+encodeURIComponent(token):''}`;
});
document.getElementById('mode')?.addEventListener('change',e=>postState({evidenceMode:e.target.value}));document.getElementById('changeResponds')?.addEventListener('click',()=>document.getElementById('respondsChoices').classList.toggle('hidden'));document.getElementById('reset')?.addEventListener('click',async()=>{const ok=await postState({reset:true}); if(ok) location.href=`/phasmo/setup?room=${encodeURIComponent(room)}${token?'&token='+encodeURIComponent(token):''}`;});document.getElementById('copyOverlay')?.addEventListener('click',()=>navigator.clipboard?.writeText(`${location.origin}/phasmo/overlay?room=${encodeURIComponent(room)}`));document.getElementById('behaviorFilter')?.addEventListener('input',renderBehaviors);
document.getElementById('toggleEvidence')?.addEventListener('click',()=>{evidenceCollapsed=!evidenceCollapsed;localStorage.setItem('phasmoEvidenceCollapsed',evidenceCollapsed);renderControl();});
document.getElementById('toggleBehavior')?.addEventListener('click',()=>{behaviorCollapsed=!behaviorCollapsed;localStorage.setItem('phasmoBehaviorCollapsed',behaviorCollapsed);renderControl();});
document.getElementById('toggleCursed')?.addEventListener('click',()=>{cursedCollapsed=!cursedCollapsed;localStorage.setItem('phasmoCursedCollapsed',cursedCollapsed);renderControl();});
getState(); if(MODE!=='setup'){setInterval(getState, MODE==='overlay'?1000:3000);}
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
        "setupComplete": False,
        "map": "unknown",
        "difficulty": "unknown",
        "weather": "unknown",
        "cursedItems": {},
        "behaviors": {},
        "votes": {},
        "guesses": {},
        "timers": {},
        "manualGhosts": {"selected": None, "excluded": []},
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
        merged["guesses"] = data.get("guesses", {}) or {}
        merged["timers"] = data.get("timers", {}) or {}
        merged["cursedItems"] = data.get("cursedItems", {}) or {}
        if not merged.get("map") and data.get("level"):
            merged["map"] = data.get("level")
        manual = data.get("manualGhosts", {}) or {}
        merged["manualGhosts"] = {
            "selected": manual.get("selected"),
            "excluded": manual.get("excluded", []) or [],
        }
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


TIMER_DEFAULT_SECONDS = {
    "incense": 90,
    "hunt": 60,
    "cooldown": 25,
}

TIMER_ALIASES = {
    "smudge": "incense",
    "incense": "incense",
    "hunt": "hunt",
    "cooldown": "cooldown",
    "cd": "cooldown",
}

GHOST_TESTS = {
    "Deogen": ["Hunt test: very fast far away, very slow when close.", "It always knows player location during hunts.", "Spirit Box breathing response can confirm it."],
    "Revenant": ["Hunt test: slow while searching, extremely fast after detection.", "Break line of sight and listen for deceleration."],
    "Raiju": ["Electronics test: speeds up near active electronics.", "Interference range feels wider than normal."],
    "Hantu": ["Temperature test: faster in cold rooms, slower in warm rooms.", "Freezing breath during hunts when breaker is off/broken."],
    "Wraith": ["Salt test: it never disturbs salt.", "Teleport can leave EMF near a player."],
    "Obake": ["UV test: unique fingerprints such as six fingers/double switch.", "May hide valid fingerprints or briefly shapeshift during hunts."],
    "Phantom": ["Photo test: disappears when photographed/filmed.", "More invisible during hunts; looking at it drains sanity."],
    "Poltergeist": ["Object pile test: many throws at once.", "During hunts, very high throw rate near objects."],
    "Goryo": ["D.O.T.S test: camera-only and not visible to naked eye.", "Favorite room tends to stay stable."],
    "Onryo": ["Flame test: flame prevents hunt like crucifix.", "Third flame blowout can trigger a hunt if no nearby flame remains."],
    "Spirit": ["Incense test: hunt prevention lasts much longer than normal."],
    "Demon": ["Hunt timing: can hunt very early.", "Incense protection is shorter; crucifix range is larger."],
    "The Mimic": ["Mimic check: orbs plus an impossible evidence/behavior combo.", "Behavior can change over time. Do not trust one hunt tell alone."],
    "The Twins": ["Look for two interaction locations or two hunt speeds.", "Hunt may start from extended interaction range."],
    "Yokai": ["Talking in same room can enable earlier hunts.", "During hunts, hearing range is very short."],
    "Yurei": ["Door test: strong full door close / sanity drain event.", "Incense can trap it in favorite room."],
    "Shade": ["Same-room test: low activity, no hunt/interactions while player is in same room.", "Later hunt threshold than normal."],
    "Oni": ["Event test: no mist/airball events; stronger full-form events.", "More visible during hunts."],
    "Mare": ["Light test: more dangerous in dark, avoids turning lights on.", "Can immediately turn lights off and prefers light-shatter events."],
    "Moroi": ["Curse test: sanity drains rapidly after audio/Spirit Box contact.", "Hunt speed scales with lower sanity; incense blind lasts longer."],
    "Myling": ["Sound test: footsteps/vocalizations only audible when close.", "Parabolic sounds occur more often."],
    "Banshee": ["Targeting test: focuses one player.", "Banshee scream or frequent singing events support it."],
    "Thaye": ["Aging test: starts fast/active, calms and slows over time."],
    "Jinn": ["Breaker test: fast with breaker on, line of sight, and distance.", "Can sanity-drain near fuse box; never turns breaker off directly."],
    "Kormos": ["Awareness test: no normal visual line-of-sight; reacts to sound/electronics/footsteps.", "No mist/chasing events."],
    "Aswang": ["Hunt start/speed test: possible no grace, faster line-of-sight acceleration.", "Official hiding spot behavior can spare instead of kill."],
    "Gallu": ["State test: crucifix, incense, and salt can shift normal/enraged/weakened behavior.", "Cannot disturb salt while enraged."],
    "Obambo": ["State timing test: calm/aggressive state alternates after door opens.", "Aggressive hunts earlier and can be shorter."],
    "Dayan": ["Movement test: faster if nearby player moves, slower if nearby player stands still."],
}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _start_timer(state: Dict[str, Any], key: str, seconds: int | None = None):
    duration = int(seconds or TIMER_DEFAULT_SECONDS.get(key, 60))
    state.setdefault("timers", {})[key] = {
        "startedAt": _now_ms(),
        "durationSeconds": max(1, duration),
        "running": True,
    }


def _stop_timer(state: Dict[str, Any], key: str):
    state.setdefault("timers", {}).pop(key, None)


def _clear_timers(state: Dict[str, Any]):
    state["timers"] = {}


def _ghost_test_summary(ghost: str) -> str:
    checks = GHOST_TESTS.get(ghost)
    if not checks:
        return f"No quick test notes are configured for {ghost} yet."
    return f"{ghost} quick checks: " + " | ".join(checks[:3])


def apply_command(state: Dict[str, Any], command: str, user: str | None = None) -> Tuple[Dict[str, Any], str]:
    text = (command or "").strip()
    parts = text.split()
    lower_parts = text.lower().split()
    if not parts:
        return state, "No command entered."
    cmd = lower_parts[0]

    if cmd in {"!reset", "!phasmoreset"}:
        return default_state(state.get("room", "default")), "Run reset. Setup required."

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

    if cmd in {"!timer", "!timers"}:
        if len(lower_parts) == 1:
            return state, "Use !timer incense start, !timer hunt start, !timer cooldown start, or !timer clear."
        if lower_parts[1] in {"clear", "reset", "stopall"}:
            _clear_timers(state)
            return state, "All timers cleared."
        key = TIMER_ALIASES.get(lower_parts[1])
        if not key:
            return state, f"Unknown timer: {parts[1]}. Use incense, hunt, or cooldown."
        action = lower_parts[2] if len(lower_parts) > 2 else "start"
        custom_seconds = None
        if len(lower_parts) > 3 and lower_parts[3].isdigit():
            custom_seconds = int(lower_parts[3])
        if action in {"start", "go", "begin", "restart"}:
            _start_timer(state, key, custom_seconds)
            return state, f"{key.title()} timer started."
        if action in {"stop", "clear", "reset", "done"}:
            _stop_timer(state, key)
            return state, f"{key.title()} timer cleared."
        if action.isdigit():
            _start_timer(state, key, int(action))
            return state, f"{key.title()} timer started for {action} seconds."
        return state, "Use start, stop, clear, or a duration in seconds."

    if cmd in {"!incense", "!smudge"}:
        _start_timer(state, "incense")
        return state, "Incense timer started."

    if cmd in {"!hunt"}:
        _start_timer(state, "hunt")
        return state, "Hunt timer started."

    if cmd in {"!cooldown", "!cd"}:
        _start_timer(state, "cooldown")
        return state, "Cooldown timer started."

    if cmd in {"!tests", "!test"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown ghost for quick tests: {ghost_text or 'blank'}."
        return state, _ghost_test_summary(ghost)

    if cmd in {"!ghost", "!select", "!notghost", "!restoreghost"}:
        action = lower_parts[1] if len(lower_parts) > 1 else ""
        manual = state.setdefault("manualGhosts", {"selected": None, "excluded": []})
        manual.setdefault("excluded", [])

        if cmd == "!notghost":
            action = "not"
            ghost_text = " ".join(parts[1:])
        elif cmd == "!restoreghost":
            action = "restore"
            ghost_text = " ".join(parts[1:])
        elif cmd == "!select":
            action = "select"
            ghost_text = " ".join(parts[1:])
        else:
            ghost_text = " ".join(parts[2:]) if action in {"not", "exclude", "out", "restore", "select", "force", "clear"} else " ".join(parts[1:])

        if action in {"clear", "reset"}:
            state["manualGhosts"] = {"selected": None, "excluded": []}
            return state, "Manual ghost overrides cleared."

        if action in {"not", "exclude", "out"}:
            ghost = _normal_ghost(ghost_text)
            if not ghost:
                return state, f"Unknown ghost to exclude: {ghost_text or 'blank'}."
            if ghost not in manual["excluded"]:
                manual["excluded"].append(ghost)
            if manual.get("selected") == ghost:
                manual["selected"] = None
            return state, f"{ghost} manually excluded."

        if action == "restore":
            ghost = _normal_ghost(ghost_text)
            if not ghost:
                return state, f"Unknown ghost to restore: {ghost_text or 'blank'}."
            manual["excluded"] = [g for g in manual.get("excluded", []) if g != ghost]
            return state, f"{ghost} restored to the candidate pool."

        if action in {"select", "force"}:
            ghost = _normal_ghost(ghost_text)
            if not ghost:
                return state, f"Unknown ghost to select: {ghost_text or 'blank'}."
            manual["selected"] = ghost
            manual["excluded"] = [g for g in manual.get("excluded", []) if g != ghost]
            return state, f"{ghost} manually selected."

        # If !ghost is not being used as an override, treat it as a viewer guess.
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown ghost guess: {ghost_text or 'blank'}."
        voter = _normal_user(user)
        state.setdefault("votes", {})[voter] = ghost
        return state, f"{voter} voted for {ghost}."

    if cmd in {"!guess"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown lucky guess: {ghost_text or 'blank'}."
        voter = _normal_user(user)
        state.setdefault("guesses", {})[voter] = ghost
        return state, f"{voter} locked in a lucky guess for {ghost}."

    if cmd in {"!vote"}:
        ghost_text = " ".join(parts[1:]) if len(parts) > 1 else ""
        ghost = _normal_ghost(ghost_text)
        if not ghost:
            return state, f"Unknown decision vote: {ghost_text or 'blank'}."
        voter = _normal_user(user)
        state.setdefault("votes", {})[voter] = ghost
        return state, f"{voter} voted for {ghost} as decision input."

    if cmd in {"!unvote", "!clearvote"}:
        voter = _normal_user(user)
        state.setdefault("votes", {}).pop(voter, None)
        return state, f"{voter}'s decision vote was cleared."

    if cmd in {"!unguess", "!clearguess"}:
        voter = _normal_user(user)
        state.setdefault("guesses", {}).pop(voter, None)
        return state, f"{voter}'s lucky guess was cleared."

    if cmd in {"!votes"}:
        votes = state.get("votes", {}) or {}
        if not votes:
            return state, "No decision votes yet."
        counts: dict[str, int] = {}
        for ghost in votes.values():
            counts[ghost] = counts.get(ghost, 0) + 1
        summary = ", ".join(f"{ghost}: {count}" for ghost, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))
        return state, f"Decision votes: {summary}."

    if cmd in {"!guesses"}:
        guesses = state.get("guesses", {}) or {}
        if not guesses:
            return state, "No lucky guesses yet."
        counts: dict[str, int] = {}
        for ghost in guesses.values():
            counts[ghost] = counts.get(ghost, 0) + 1
        summary = ", ".join(f"{ghost}: {count}" for ghost, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])))
        return state, f"Lucky guesses: {summary}."

    if cmd in {"!b", "!beh", "!behavior"}:
        if not _ALLOW_BEHAVIOR_COMMANDS:
            return state, "Behavior chat commands are disabled. Set PHASMO_ALLOW_BEHAVIOR_COMMANDS=true to enable !b commands."
        key = BEHAVIOR_ALIASES.get(lower_parts[1], "") if len(lower_parts) > 1 else ""
        if not key:
            return state, f"Unknown behavior: {parts[1] if len(parts) > 1 else 'blank'}."
        value = _normalize_value(lower_parts[2] if len(lower_parts) > 2 else "observed", "behavior")
        state.setdefault("behaviors", {})[key] = value
        return state, f"{key} set to {value}."

    return state, "Command not recognized. Try !ev emf yes, !b deogen observed, !timer incense start, !ghost not Wraith, !tests Deogen, !guess Deogen, !vote Wraith, or !reset."


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


@app.get("/phasmo/setup")
def phasmo_setup():
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "setup"))


@app.get("/phasmo/control")
def phasmo_control(room: str | None = Query(default=None), token: str | None = Query(default=None)):
    safe_room = _room_name(room)
    state = read_state(safe_room)
    if not state.get("setupComplete"):
        suffix = f"?room={safe_room}"
        if token:
            suffix += f"&token={token}"
        return RedirectResponse(f"/phasmo/setup{suffix}")
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "control"))


@app.get("/phasmo/overlay")
def phasmo_overlay():
    return HTMLResponse(HTML_TEMPLATE.replace("__MODE__", "overlay"))




@app.get("/phasmo/leaderboard")
def phasmo_leaderboard(room: str | None = Query(default=None), token: str | None = Query(default=None)):
    safe_room = _room_name(room)
    state = read_state(safe_room)

    def make_rows(source: dict[str, str], empty_text: str) -> str:
        counts: dict[str, list[str]] = {}
        for user, ghost in (source or {}).items():
            counts.setdefault(str(ghost), []).append(str(user))
        rows = ""
        for ghost, users in sorted(counts.items(), key=lambda item: (-len(item[1]), item[0])):
            user_list = ", ".join(sorted(users))
            rows += f"<tr><td>{ghost}</td><td>{len(users)}</td><td>{user_list}</td></tr>"
        if not rows:
            rows = f"<tr><td colspan='3'>{empty_text}</td></tr>"
        return rows

    guess_rows = make_rows(state.get("guesses", {}) or {}, "No lucky guesses yet. Viewers can use <strong>!guess GhostName</strong>.")
    vote_rows = make_rows(state.get("votes", {}) or {}, "No decision votes yet. Use <strong>!vote GhostName</strong> when chat is helping make a call.")

    token_suffix = f"&token={token}" if token else ""
    control_url = f"/phasmo/control?room={safe_room}{token_suffix}"
    overlay_url = f"/phasmo/overlay?room={safe_room}"
    html = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Phasmo Chat Board</title>
        <style>
          body {{ margin:0; background:#000; color:#f8fafc; font-family:Inter,system-ui,Segoe UI,sans-serif; }}
          .app {{ width:min(820px,100vw); padding:14px; display:grid; gap:14px; }}
          .panel {{ background:#172235ee; border:1px solid #334155; border-radius:16px; overflow:hidden; box-shadow:0 16px 40px #0007; }}
          .head {{ padding:14px; border-bottom:1px solid #334155; display:flex; justify-content:space-between; gap:8px; align-items:center; }}
          .body {{ padding:14px; }}
          a {{ color:#38bdf8; }}
          .muted {{ color:#94a3b8; font-size:12px; }}
          table {{ width:100%; border-collapse:collapse; }}
          th,td {{ border-bottom:1px solid #334155; padding:10px; text-align:left; vertical-align:top; }}
          th {{ color:#94a3b8; font-size:12px; text-transform:uppercase; letter-spacing:.12em; }}
          .badge {{ border:1px solid #334155; background:#0f172a; border-radius:999px; padding:6px 9px; font-size:12px; display:inline-block; margin-left:6px; }}
        </style>
      </head>
      <body>
        <main class="app">
          <section class="panel">
            <div class="head">
              <div>
                <strong>Phasmo Chat Board</strong>
                <div class="muted">room: {safe_room}</div>
              </div>
              <div>
                <a class="badge" href="{control_url}">Control</a>
                <a class="badge" href="{overlay_url}">Overlay</a>
              </div>
            </div>
            <div class="body">
              <p class="muted"><strong>!guess</strong> is the lucky prediction board. <strong>!vote</strong> is decision input when evidence is thin and chat is helping choose.</p>
            </div>
          </section>
          <section class="panel">
            <div class="head"><strong>Lucky Guesses</strong><span class="muted">!guess GhostName</span></div>
            <div class="body"><table><thead><tr><th>Ghost</th><th>Guesses</th><th>Users</th></tr></thead><tbody>{guess_rows}</tbody></table></div>
          </section>
          <section class="panel">
            <div class="head"><strong>Decision Votes</strong><span class="muted">!vote GhostName</span></div>
            <div class="body"><table><thead><tr><th>Ghost</th><th>Votes</th><th>Users</th></tr></thead><tbody>{vote_rows}</tbody></table></div>
          </section>
        </main>
      </body>
    </html>
    """
    return HTMLResponse(html)


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
            if "guesses" in body and isinstance(body["guesses"], dict):
                current.setdefault("guesses", {}).update(body["guesses"] or {})
            if "timers" in body and isinstance(body["timers"], dict):
                current["timers"].update(body["timers"] or {})
            if "manualGhosts" in body and isinstance(body["manualGhosts"], dict):
                manual = body["manualGhosts"] or {}
                current.setdefault("manualGhosts", {"selected": None, "excluded": []})
                if "selected" in manual:
                    current["manualGhosts"]["selected"] = manual["selected"] if manual["selected"] in GHOST_NAMES else None
                if "excluded" in manual and isinstance(manual["excluded"], list):
                    current["manualGhosts"]["excluded"] = [g for g in manual["excluded"] if g in GHOST_NAMES]
            if "responds" in body:
                current["responds"] = body["responds"] if body["responds"] in {"unknown", "alone", "everyone"} else "unknown"
            if "evidenceMode" in body and str(body["evidenceMode"]) in {"0", "1", "2", "3"}:
                current["evidenceMode"] = str(body["evidenceMode"])
            if "setupComplete" in body:
                current["setupComplete"] = bool(body["setupComplete"])
            if "map" in body:
                current["map"] = str(body.get("map") or "unknown")[:120]
            if "difficulty" in body:
                current["difficulty"] = str(body.get("difficulty") or "unknown")[:40]
            if "weather" in body:
                current["weather"] = str(body.get("weather") or "unknown")[:40]
            if "cursedItems" in body and isinstance(body["cursedItems"], dict):
                current.setdefault("cursedItems", {})
                for k, v in body["cursedItems"].items():
                    key = str(k).lower()[:80]
                    if str(v) in {"found", "out", "unknown"}:
                        current["cursedItems"][key] = str(v)
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
