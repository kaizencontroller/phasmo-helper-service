
from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, Tuple

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

app = FastAPI(title="Kaizen Phasmophobia Helper")

_STATE_LOCK = threading.Lock()
_STATE_DIR = Path(os.getenv("PHASMO_STATE_DIR", "/tmp/phasmo_state"))
_ADMIN_TOKEN = os.getenv("PHASMO_ADMIN_TOKEN", "").strip()
_ALLOW_BEHAVIOR_COMMANDS = os.getenv("PHASMO_ALLOW_BEHAVIOR_COMMANDS", "false").strip().lower() in {"1", "true", "yes", "on"}

EVIDENCE = ["dots", "emf5", "freezing", "orbs", "writing", "box", "uv"]

EVIDENCE_ALIASES = {
    "dots": "dots", "dot": "dots", "projector": "dots",
    "emf": "emf5", "emf5": "emf5", "emf-5": "emf5", "emf_5": "emf5",
    "freezing": "freezing", "freeze": "freezing", "temps": "freezing", "temp": "freezing",
    "orb": "orbs", "orbs": "orbs", "ghostorb": "orbs", "ghostorbs": "orbs",
    "writing": "writing", "book": "writing",
    "box": "box", "spirit": "box", "spiritbox": "box", "spirit-box": "box",
    "uv": "uv", "ultraviolet": "uv", "fingerprints": "uv", "prints": "uv",
}

BEHAVIOR_ALIASES = {
    "no-salt": "no-salt", "nosalt": "no-salt", "wraith": "no-salt", "no-prints": "no-salt", "no-footprints": "no-salt",
    "salt-prints": "salt-prints", "prints": "salt-prints", "footprints": "salt-prints",
    "photo-disappear": "photo-disappear", "phantom-photo": "photo-disappear", "photo": "photo-disappear", "disappear": "photo-disappear",
    "photo-visible": "photo-visible", "visible-photo": "photo-visible", "notphantom": "photo-visible",
    "six-finger": "six-finger", "sixfinger": "six-finger", "six-fingers": "six-finger", "obake": "six-finger",
    "normal-uv": "normal-uv", "normalprints": "normal-uv", "normal-prints": "normal-uv",
    "breaker-off": "breaker-off", "breaker": "breaker-off", "poweroff": "breaker-off", "breakeroff": "breaker-off",
    "breaker-on": "breaker-on", "poweron": "breaker-on", "breakeron": "breaker-on", "jinn": "breaker-on",
    "cold-fast": "cold-fast", "hantu": "cold-fast", "cold": "cold-fast",
    "electronics-fast": "electronics-fast", "raiju": "electronics-fast", "electronics": "electronics-fast", "electric": "electronics-fast",
    "revenant-speed": "revenant-speed", "revenant": "revenant-speed", "rev": "revenant-speed", "fast-los": "revenant-speed",
    "deogen-speed": "deogen-speed", "deogen": "deogen-speed", "deo": "deogen-speed", "slow-close": "deogen-speed",
    "twins": "twins", "twin": "twins", "double": "twins",
    "polter-throw": "polter-throw", "polter": "polter-throw", "polty": "polter-throw", "throw": "polter-throw", "throws": "polter-throw",
    "goryo-dots": "goryo-dots", "goryo": "goryo-dots", "camera-dots": "goryo-dots", "camdots": "goryo-dots",
    "oni-visible": "oni-visible", "oni": "oni-visible", "visible": "oni-visible", "blink": "oni-visible",
    "myling-quiet": "myling-quiet", "myling": "myling-quiet", "quiet": "myling-quiet", "footsteps": "myling-quiet",
    "banshee-target": "banshee-target", "banshee": "banshee-target", "target": "banshee-target",
    "parabolic": "parabolic", "para": "parabolic", "sound": "parabolic",
    "early-hunt": "early-hunt", "early": "early-hunt", "hunt": "early-hunt",
    "shade-shy": "shade-shy", "shade": "shade-shy", "shy": "shade-shy", "nohunt": "shade-shy",
    "candle": "candle", "onryo": "candle", "flame": "candle",
    "lights-off": "lights-off", "mare": "lights-off", "lights": "lights-off",
    "door-slam": "door-slam", "yurei": "door-slam", "door": "door-slam", "slam": "door-slam",
    "long-smudge": "long-smudge", "smudge": "long-smudge", "incense": "long-smudge", "moroi": "long-smudge", "spirit": "long-smudge",
    "thaye-age": "thaye-age", "thaye": "thaye-age", "age": "thaye-age", "aging": "thaye-age",
    "mimic-check": "mimic-check", "mimic": "mimic-check", "fake-orbs": "mimic-check", "fakeorb": "mimic-check",
}

HTML_TEMPLATE = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8" />\n<meta name="viewport" content="width=device-width, initial-scale=1" />\n<title>Phasmo Decision Tool</title>\n<style>\n:root{--bg:#101827;--panel:#172235ee;--soft:#213149;--text:#f8fafc;--muted:#94a3b8;--line:#334155;--orange:#f97316;--green:#22c55e;--red:#ef4444;--blue:#38bdf8}*{box-sizing:border-box}body{margin:0;background:#000;color:var(--text);font-family:Inter,system-ui,Segoe UI,sans-serif}.app{width:min(460px,100vw);height:100vh;overflow:auto;padding:10px;background:#000}.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;margin-bottom:10px;box-shadow:0 16px 40px #0007}.head{padding:12px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:8px}.body{padding:10px}.muted{color:var(--muted);font-size:12px}.badge,.chip{border:1px solid var(--line);background:#0f172a;border-radius:999px;padding:5px 8px;font-size:12px}button,select,input{background:#0f172a;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:9px 10px;font:inherit}button{cursor:pointer}.green{background:#14532d;border-color:#22c55e}.red{background:#5b2329;border-color:#ef4444}.blue{background:#123247;border-color:#38bdf8}.orange{background:#432919;border-color:#f97316}.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.spread{display:flex;justify-content:space-between;align-items:center;gap:8px}.next{border-color:#f97316;background:#2a2330}.big{font-weight:950;font-size:28px;line-height:1}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px}.evrow{display:grid;grid-template-columns:1fr 30px 30px 30px;gap:6px;align-items:center;padding:6px 0;border-bottom:1px solid #33415588}.evrow:last-child{border-bottom:0}.evname{font-weight:800;font-size:13px}.state{height:30px;padding:0}.yes{background:#14532d;border-color:#22c55e}.no{background:#5b2329;border-color:#ef4444}.unk{background:#0f172a}.ghosts{display:grid;grid-template-columns:1fr 1fr;gap:7px;max-height:230px;overflow:auto}.ghost{border:1px solid var(--line);border-radius:12px;padding:8px;background:#111a2b}.ghost.top{border-color:#22c55e;background:#132a24}.ghost h4{margin:0 0 5px;font-size:14px}.tags{display:flex;gap:4px;flex-wrap:wrap}.chip{font-size:10px;padding:3px 5px}.branch{border:1px solid var(--line);border-radius:13px;overflow:hidden;margin-bottom:8px;background:#111a2b}.branch-title{width:100%;border:0;border-bottom:1px solid var(--line);border-radius:0;display:flex;justify-content:space-between}.branch-body{padding:8px;display:grid;gap:7px}.option{border:1px solid #334155;border-radius:11px;padding:8px;background:#0f172a}.option-label{font-weight:800;font-size:13px;margin-bottom:5px}.selected{padding:8px;background:#163425}.selected.bad{background:#3a1d24}.overlay{width:1280px;height:220px;display:block;padding:8px;background:#000;overflow:hidden}.ov-main{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:10px 12px;height:204px;overflow:hidden;display:grid;grid-template-rows:14px 44px 22px 28px 38px 24px;gap:4px}.ov-side{display:none}.ov-footnote{border-top:1px solid var(--line);padding-top:4px;display:flex;gap:6px;align-items:center;white-space:nowrap;overflow:hidden}.ov-footnote-title{font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);font-weight:900}.ov-footnote-items{display:flex;gap:5px;overflow:hidden}.foot-behavior{border:1px solid var(--line);background:#0f172a;border-radius:999px;padding:3px 6px;font-size:10px;max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.foot-behavior.observed{border-color:#22c55e;color:#bbf7d0}.foot-behavior.contradicted{border-color:#ef4444;color:#fecaca}.ov-step{font-size:42px;font-weight:950;line-height:.95;letter-spacing:-.03em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ov-sub{font-size:14px;color:#dbeafe;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ov-evidence{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;margin-top:0}.ov-evidence .chip{font-size:11px;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding:4px 5px}.hidden{display:none!important}@media(max-width:700px){.app{width:100vw}.ghosts{grid-template-columns:1fr}}\n</style>\n</head>\n<body>\n<div id="control" class="app hidden">\n  <div class="panel"><div class="head"><div><strong>Phasmo Control</strong><div class="muted">shared room: <span id="roomLabel"></span></div></div><span class="badge" id="countBadge">0</span></div>\n    <div class="body">\n      <div class="spread"><span class="muted">Evidence mode</span><select id="mode"><option value="3">3 evidence</option><option value="2">2 evidence</option><option value="1">1 evidence</option><option value="0">0 evidence</option></select></div>\n    </div>\n  </div>\n  <div class="panel" id="respondsPanel"><div class="body"><div class="spread"><strong>Responds: <span id="respondsText">Unknown</span></strong><button id="changeResponds">Change</button></div><div id="respondsChoices" class="grid3" style="margin-top:8px"><button data-responds="unknown">Unknown</button><button data-responds="everyone">Everyone</button><button data-responds="alone">Alone</button></div></div></div>\n  <div class="panel next"><div class="body"><div class="muted" style="letter-spacing:.12em;font-weight:900">NEXT</div><div class="big" id="nextName">Loading</div><p class="muted" id="nextWhy"></p><div class="grid2"><button class="green" id="confirmNext">Confirm</button><button class="red" id="denyNext">No</button></div></div></div>\n  <div class="panel"><div class="body row"><button class="orange" id="reset">Reset</button><button class="blue" id="copyOverlay">Copy Overlay URL</button></div></div>\n  <div class="panel"><div class="body" id="evidenceRows"></div></div>\n  <div class="panel"><div class="head"><strong>Candidates</strong><span class="muted" id="summary"></span></div><div class="body"><div class="ghosts" id="ghosts"></div></div></div>\n  <div class="panel"><div class="head"><strong>Behavior Branches</strong></div><div class="body"><input id="behaviorFilter" placeholder="filter: speed, salt, photo" style="width:100%;margin-bottom:8px"><div id="behaviors"></div></div></div>\n</div>\n<div id="overlay" class="overlay hidden"><div class="ov-main"><div class="muted">NEXT STEP</div><div class="ov-step" id="ovStep">Loading</div><p class="ov-sub" id="ovSub"></p><div class="row" id="ovCandidates"></div><div class="ov-evidence" id="ovEvidence"></div><div class="ov-footnote"><span class="ov-footnote-title">Witnessed <span id="ovBehaviorCount">0</span></span><div class="ov-footnote-items" id="ovBehaviors"></div></div></div></div>\n<script>\nconst MODE=\'__MODE__\'; const room=new URLSearchParams(location.search).get(\'room\')||\'default\'; const API=\'/api/phasmo\';\nconst E=[\'dots\',\'emf5\',\'freezing\',\'orbs\',\'writing\',\'box\',\'uv\']; const EL={dots:\'D.O.T.S Projector\',emf5:\'EMF Level 5\',freezing:\'Freezing Temperatures\',orbs:\'Ghost Orb\',writing:\'Ghost Writing\',box:\'Spirit Box\',uv:\'Ultraviolet\'};\nconst G=[\n[\'Aswang\',[\'freezing\',\'writing\',\'dots\']],\n[\'Banshee\',[\'dots\',\'orbs\',\'uv\']],\n[\'Dayan\',[\'emf5\',\'orbs\',\'box\']],\n[\'Demon\',[\'writing\',\'uv\',\'freezing\']],\n[\'Deogen\',[\'dots\',\'writing\',\'box\']],\n[\'Gallu\',[\'emf5\',\'box\',\'uv\']],\n[\'Goryo\',[\'dots\',\'emf5\',\'uv\']],\n[\'Hantu\',[\'orbs\',\'uv\',\'freezing\']],\n[\'Jinn\',[\'emf5\',\'uv\',\'freezing\']],\n[\'Kormos\',[\'orbs\',\'box\',\'uv\']],\n[\'Mare\',[\'writing\',\'orbs\',\'box\']],\n[\'Moroi\',[\'writing\',\'freezing\',\'box\']],\n[\'Myling\',[\'writing\',\'emf5\',\'uv\']],\n[\'Obake\',[\'emf5\',\'orbs\',\'uv\']],\n[\'Obambo\',[\'uv\',\'writing\',\'dots\']],\n[\'Oni\',[\'dots\',\'emf5\',\'freezing\']],\n[\'Onryo\',[\'orbs\',\'freezing\',\'box\']],\n[\'Phantom\',[\'dots\',\'uv\',\'box\']],\n[\'Poltergeist\',[\'writing\',\'uv\',\'box\']],\n[\'Raiju\',[\'dots\',\'emf5\',\'orbs\']],\n[\'Revenant\',[\'writing\',\'orbs\',\'freezing\']],\n[\'Shade\',[\'writing\',\'emf5\',\'freezing\']],\n[\'Spirit\',[\'writing\',\'emf5\',\'box\']],\n[\'Thaye\',[\'dots\',\'writing\',\'orbs\']],\n[\'The Mimic\',[\'uv\',\'freezing\',\'box\']],\n[\'The Twins\',[\'emf5\',\'freezing\',\'box\']],\n[\'Wraith\',[\'dots\',\'emf5\',\'box\']],\n[\'Yokai\',[\'dots\',\'orbs\',\'box\']],\n[\'Yurei\',[\'dots\',\'orbs\',\'freezing\']]\n].map(([name,ev])=>({name,ev}));\nconst B=[\n{id:\'no-salt\',cat:\'Salt / UV\',label:\'Salt stepped in, no UV footprints\',up:[\'Wraith\'],down:[],w:55,rel:\'High\'},\n{id:\'salt-prints\',cat:\'Salt / UV\',label:\'Salt stepped in and UV footprints appear\',up:[],down:[\'Wraith\'],w:45,rel:\'High\'},\n{id:\'photo-disappear\',cat:\'Photo\',label:\'Ghost disappears when photo is taken\',up:[\'Phantom\'],down:[],w:55,rel:\'High\'},\n{id:\'photo-visible\',cat:\'Photo\',label:\'Ghost remains visible in ghost photo\',up:[],down:[\'Phantom\'],w:32,rel:\'Med\'},\n{id:\'six-finger\',cat:\'UV\',label:\'Six-finger / unusual UV print\',up:[\'Obake\'],down:[],w:55,rel:\'High\'},\n{id:\'breaker-off\',cat:\'Breaker\',label:\'Ghost turns breaker off directly\',up:[\'Hantu\',\'Mare\'],down:[\'Jinn\'],w:28,rel:\'Med\'},\n{id:\'breaker-on\',cat:\'Breaker\',label:\'Breaker stays on / performs better with power on\',up:[\'Jinn\',\'Raiju\'],down:[\'Hantu\'],w:18,rel:\'Low\'},\n{id:\'cold-fast\',cat:\'Hunt Speed\',label:\'Fast in cold rooms, slower in warm rooms\',up:[\'Hantu\'],down:[],w:45,rel:\'High\'},\n{id:\'electronics-fast\',cat:\'Hunt Speed\',label:\'Speeds up around active electronics\',up:[\'Raiju\'],down:[],w:45,rel:\'High\'},\n{id:\'revenant-speed\',cat:\'Hunt Speed\',label:\'Slow searching, very fast with line of sight\',up:[\'Revenant\'],down:[],w:50,rel:\'High\'},\n{id:\'deogen-speed\',cat:\'Hunt Speed\',label:\'Very fast far away, very slow when close\',up:[\'Deogen\'],down:[],w:55,rel:\'High\'},\n{id:\'twins\',cat:\'Activity\',label:\'Two interaction/speed profiles appear\',up:[\'The Twins\'],down:[],w:38,rel:\'Med\'},\n{id:\'polter-throw\',cat:\'Interaction\',label:\'Object pile explosion / many throws at once\',up:[\'Poltergeist\'],down:[],w:50,rel:\'High\'},\n{id:\'goryo-dots\',cat:\'D.O.T.S\',label:\'D.O.T.S only visible on camera\',up:[\'Goryo\'],down:[],w:45,rel:\'High\'},\n{id:\'oni-visible\',cat:\'Manifestation\',label:\'Very visible during hunts / no airball\',up:[\'Oni\'],down:[\'Phantom\'],w:35,rel:\'Med\'},\n{id:\'myling-quiet\',cat:\'Sound\',label:\'Hunt footsteps audible only when close\',up:[\'Myling\'],down:[],w:42,rel:\'High\'},\n{id:\'banshee-target\',cat:\'Targeting\',label:\'Only one player seems targeted\',up:[\'Banshee\'],down:[],w:38,rel:\'Med\'},\n{id:\'early-hunt\',cat:\'Hunt Timing\',label:\'Early hunt above normal threshold\',up:[\'Demon\',\'Mare\',\'Onryo\',\'Thaye\',\'Raiju\',\'Yokai\'],down:[\'Shade\'],w:30,rel:\'Med\'},\n{id:\'shade-shy\',cat:\'Hunt Timing\',label:\'Will not hunt while players are nearby\',up:[\'Shade\'],down:[\'Demon\',\'Oni\'],w:34,rel:\'Med\'},\n{id:\'candle\',cat:\'Object Test\',label:\'Flame/candle pattern triggers hunt\',up:[\'Onryo\'],down:[],w:45,rel:\'High\'},\n{id:\'lights-off\',cat:\'Light\',label:\'Turns lights off / avoids lights on\',up:[\'Mare\'],down:[],w:24,rel:\'Low\'},\n{id:\'door-slam\',cat:\'Door\',label:\'Full door shut / sanity-drain event\',up:[\'Yurei\'],down:[],w:36,rel:\'Med\'},\n{id:\'long-smudge\',cat:\'Smudge\',label:\'Incense seems effective longer\',up:[\'Moroi\',\'Spirit\'],down:[],w:30,rel:\'Med\'},\n{id:\'thaye-age\',cat:\'Activity\',label:\'Starts hyperactive/fast, calms over time\',up:[\'Thaye\'],down:[],w:42,rel:\'High\'},\n{id:\'mimic-check\',cat:\'Mimic Check\',label:\'Orbs plus impossible evidence combo\',up:[\'The Mimic\'],down:[],w:55,rel:\'High\'}];\nlet state=null, expanded={};\nasync function getState(){state=await fetch(`${API}/state?room=${encodeURIComponent(room)}`).then(r=>r.json());render();}\nasync function postState(patch){await fetch(`${API}/state?room=${encodeURIComponent(room)}`,{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify(patch)});await getState();}\nasync function command(cmd){await fetch(`${API}/command?room=${encodeURIComponent(room)}`,{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({command:cmd})});await getState();}\nfunction impact(g){let s=0; for(const b of B){let v=state.behaviors?.[b.id]||\'unknown\'; if(v===\'observed\'){if(b.up.includes(g.name))s+=b.w;if(b.down.includes(g.name))s-=b.w} if(v===\'contradicted\'){if(b.up.includes(g.name))s-=Math.round(b.w*.65);if(b.down.includes(g.name))s+=Math.round(b.w*.45)}} return s}\nfunction candidates(){let yes=E.filter(k=>state.evidence[k]===\'yes\'), no=E.filter(k=>state.evidence[k]===\'no\'), mode=+state.evidenceMode; return G.filter(g=>{if(mode===0&&!yes.length)return true; if(!yes.every(e=>g.ev.includes(e)||(g.name===\'The Mimic\'&&e===\'orbs\')))return false; if(mode===3&&no.some(e=>g.ev.includes(e)||(g.name===\'The Mimic\'&&e===\'orbs\')))return false; return true}).map(g=>({...g,impact:impact(g),score:impact(g)+yes.filter(e=>g.ev.includes(e)).length*22+(g.name===\'The Mimic\'&&yes.includes(\'orbs\')?12:0)})).sort((a,b)=>b.score-a.score||a.name.localeCompare(b.name))}\nfunction status(){let c=candidates(), yes=E.filter(k=>state.evidence[k]===\'yes\'), mode=+state.evidenceMode, target=mode>0&&yes.length>=mode, mimic=c.some(g=>g.name===\'The Mimic\'); if(!c.length)return{kind:\'conflict\',name:\'Retest\',text:\'No ghost matches. Recheck evidence.\'}; if(target&&c.length===1)return{kind:\'locked\',name:`Final ID: ${c[0].name}`,text:\'Evidence target reached. Behavior is sanity-check only.\'}; if(target&&mimic)return{kind:\'mimic\',name:\'Mimic Check\',text:\'Evidence target reached, but Mimic remains possible.\'}; if(target)return{kind:\'locked\',name:`Likely: ${c[0].name}`,text:\'Evidence target reached. Resolve contradictions only.\'}; if(c.length===1)return{kind:\'verify\',name:`Verify ${c[0].name}`,text:\'One candidate remains. Final disconfirming check.\'}; return{kind:\'open\',name:\'Investigating\',text:\'Continue evidence collection.\'}}\nfunction nextEv(){let st=status(); if([\'locked\',\'conflict\',\'verify\'].includes(st.kind))return null; let c=candidates(), unk=E.filter(e=>state.evidence[e]===\'unknown\'); if(c.length<=1||!unk.length)return null; return unk.map(ev=>{let y=0,n=0; for(const g of c){let has=g.ev.includes(ev)||(g.name===\'The Mimic\'&&ev===\'orbs\'); has?y++:n++} let split=Math.min(y,n), swing=Math.abs(y-n); return{ev,y,n,split,score:split*10-swing-(ev===\'box\'&&state.responds===\'unknown\'?2:0)}}).sort((a,b)=>b.score-a.score||b.split-a.split||a.swing-b.swing)[0]}\nfunction render(){ if(MODE===\'overlay\')renderOverlay(); else renderControl(); }\nfunction renderControl(){document.getElementById(\'control\').classList.remove(\'hidden\');document.getElementById(\'roomLabel\').textContent=room;document.getElementById(\'mode\').value=state.evidenceMode;let c=candidates();document.getElementById(\'countBadge\').textContent=c.length+\' candidates\';document.getElementById(\'summary\').textContent=`${E.filter(k=>state.evidence[k]===\'yes\').length} confirmed`;let r=state.responds||\'unknown\';document.getElementById(\'respondsText\').textContent=r[0].toUpperCase()+r.slice(1);document.getElementById(\'respondsChoices\').classList.toggle(\'hidden\',r!==\'unknown\');\n let nx=nextEv(), st=status(); document.getElementById(\'nextName\').textContent=nx?EL[nx.ev]:st.name; document.getElementById(\'nextWhy\').textContent=nx?`${EL[nx.ev]} splits ${nx.y}/${nx.n}.`+(nx.ev===\'box\'?` Response: ${r}.`:\'\'):st.text; document.getElementById(\'confirmNext\').disabled=!nx;document.getElementById(\'denyNext\').disabled=!nx;document.getElementById(\'confirmNext\').textContent=nx?\'Confirm \'+EL[nx.ev]:\'Confirmed\';document.getElementById(\'denyNext\').textContent=nx?\'No \'+EL[nx.ev]:\'No more evidence\'; if(nx){document.getElementById(\'confirmNext\').onclick=()=>postState({evidence:{[nx.ev]:\'yes\'}});document.getElementById(\'denyNext\').onclick=()=>postState({evidence:{[nx.ev]:\'no\'}})}\n document.getElementById(\'evidenceRows\').innerHTML=E.map(k=>`<div class=\'evrow\'><span class=\'evname\'>${EL[k]}</span><button class=\'state yes ${state.evidence[k]===\'yes\'?\'green\':\'\'}\' onclick="postState({evidence:{${JSON.stringify(k)}:\'yes\'}})">✓</button><button class=\'state unk\' onclick="postState({evidence:{${JSON.stringify(k)}:\'unknown\'}})">?</button><button class=\'state no ${state.evidence[k]===\'no\'?\'red\':\'\'}\' onclick="postState({evidence:{${JSON.stringify(k)}:\'no\'}})">×</button></div>`).join(\'\');\n document.getElementById(\'ghosts\').innerHTML=c.slice(0,6).map((g,i)=>`<div class=\'ghost ${i===0&&g.score>0?\'top\':\'\'}\'><h4>${g.name}</h4><div class=\'tags\'>${g.ev.map(e=>`<span class=\'chip\'>${EL[e]}</span>`).join(\'\')}</div><div class=\'muted\'>${g.impact?`${g.impact>0?\'+\':\'\'}${g.impact} behavior`:\'No behavior\'}</div></div>`).join(\'\'); renderBehaviors();}\nfunction renderBehaviors(){let box=document.getElementById(\'behaviors\'), q=(document.getElementById(\'behaviorFilter\').value||\'\').toLowerCase(), cset=new Set(candidates().map(g=>g.name)), st=status(); box.innerHTML=\'\'; let groups={}; for(const b of B){let logged=(state.behaviors?.[b.id]||\'unknown\')!==\'unknown\'; if(q && !(b.label+\' \'+b.cat+\' \'+b.up.join(\' \')+\' \'+b.down.join(\' \')).toLowerCase().includes(q))continue; let relevant=b.up.some(g=>cset.has(g))||b.down.some(g=>cset.has(g)); if(!relevant&&!logged)continue; if(st.kind===\'mimic\'&&!logged&&!b.up.includes(\'The Mimic\')&&!b.down.includes(\'The Mimic\'))continue; if([\'locked\',\'verify\'].includes(st.kind)&&!logged)continue; (groups[b.cat]??=[]).push(b)} for(const cat of Object.keys(groups)){let rows=groups[cat], selected=rows.find(b=>(state.behaviors?.[b.id]||\'unknown\')!==\'unknown\'), open=expanded[cat]||!selected; let el=document.createElement(\'div\');el.className=\'branch\'; let title=document.createElement(\'button\');title.className=\'branch-title\';title.innerHTML=`<span>${open?\'▼\':\'▶\'} ${cat}</span><span class=\'badge\'>${selected?\'logged\':rows.length+\' options\'}</span>`;title.onclick=()=>{expanded[cat]=!open;renderBehaviors()};el.appendChild(title); if(selected){let v=state.behaviors[selected.id], div=document.createElement(\'div\');div.className=\'selected \'+(v===\'contradicted\'?\'bad\':\'\');div.innerHTML=`<strong>${v===\'observed\'?\'✓\':\'×\'} ${selected.label}</strong><div class=\'tags\'>${selected.up.map(g=>`<span class=\'chip\'>↑ ${g}</span>`).join(\'\')}${selected.down.map(g=>`<span class=\'chip\'>↓ ${g}</span>`).join(\'\')}<span class=\'chip\'>${selected.rel}</span></div><div class=\'row\'><button onclick="postState({behaviors:{\'${selected.id}\':\'unknown\'}})">Clear</button><button class=\'blue\' onclick="expanded[\'${cat}\']=true;renderBehaviors()">Change</button></div>`;el.appendChild(div)} if(open){let body=document.createElement(\'div\');body.className=\'branch-body\'; for(const b of rows){let opt=document.createElement(\'div\');opt.className=\'option\';opt.innerHTML=`<div class=\'option-label\'>${b.label}</div><div class=\'tags\'>${b.up.map(g=>`<span class=\'chip\'>↑ ${g}</span>`).join(\'\')}${b.down.map(g=>`<span class=\'chip\'>↓ ${g}</span>`).join(\'\')}<span class=\'chip\'>${b.rel}</span></div><div class=\'grid2\'><button class=\'green\'>Observed</button><button class=\'red\'>No / False</button></div>`;let [obs,no]=opt.querySelectorAll(\'button\');obs.onclick=()=>{let patch={behaviors:{}}; for(const sib of rows)patch.behaviors[sib.id]=\'unknown\'; patch.behaviors[b.id]=\'observed\'; expanded[cat]=false; postState(patch)};no.onclick=()=>{let patch={behaviors:{}}; for(const sib of rows)patch.behaviors[sib.id]=\'unknown\'; patch.behaviors[b.id]=\'contradicted\'; expanded[cat]=false; postState(patch)};body.appendChild(opt)} el.appendChild(body)} box.appendChild(el)}}\nfunction renderOverlay(){document.getElementById(\'overlay\').classList.remove(\'hidden\');let c=candidates(), nx=nextEv(), st=status();document.getElementById(\'ovStep\').textContent=nx?\'Test \'+EL[nx.ev]:st.name;document.getElementById(\'ovSub\').textContent=nx?`${EL[nx.ev]} splits the current pool ${nx.y}/${nx.n}.`:st.text;document.getElementById(\'ovCandidates\').innerHTML=c.slice(0,6).map(g=>`<span class=\'badge\'>${g.name}${g.impact?` (${g.impact>0?\'+\':\'\'}${g.impact})`:\'\'}</span>`).join(\'\');document.getElementById(\'ovEvidence\').innerHTML=E.map(k=>`<span class=\'chip ${state.evidence[k]===\'yes\'?\'green\':state.evidence[k]===\'no\'?\'red\':\'\'}\' title=\'${EL[k]}\'>${EL[k]} ${state.evidence[k]===\'yes\'?\'✓\':state.evidence[k]===\'no\'?\'×\':\'?\'}</span>`).join(\'\');let obs=B.filter(b=>(state.behaviors?.[b.id]||\'unknown\')!==\'unknown\');document.getElementById(\'ovBehaviorCount\').textContent=obs.length;document.getElementById(\'ovBehaviors\').innerHTML=obs.length?obs.slice(0,4).map(b=>`<span class=\'foot-behavior ${state.behaviors[b.id]}\' title=\'${b.label}\'>${state.behaviors[b.id]===\'observed\'?\'✓\':\'×\'} ${b.label}</span>`).join(\'\'):`<span class=\'muted\'>No behaviors logged.</span>`}\ndocument.addEventListener(\'click\',e=>{let r=e.target.dataset.responds;if(r)postState({responds:r})});document.getElementById(\'mode\')?.addEventListener(\'change\',e=>postState({evidenceMode:e.target.value}));document.getElementById(\'changeResponds\')?.addEventListener(\'click\',()=>document.getElementById(\'respondsChoices\').classList.toggle(\'hidden\'));document.getElementById(\'reset\')?.addEventListener(\'click\',()=>postState({reset:true}));document.getElementById(\'copyOverlay\')?.addEventListener(\'click\',()=>navigator.clipboard?.writeText(`${location.origin}/phasmo/overlay?room=${encodeURIComponent(room)}`));document.getElementById(\'behaviorFilter\')?.addEventListener(\'input\',renderBehaviors);\ngetState(); setInterval(getState, MODE===\'overlay\'?1000:3000);\n</script></body></html>'


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
        if value in {"clear", "unknown", "reset"}:
            return "unknown"
        return "unknown"

    return "unknown"


def apply_command(state: Dict[str, Any], command: str) -> Tuple[Dict[str, Any], str]:
    text = (command or "").strip()
    parts = text.lower().split()

    if not parts:
        return state, "No command entered."

    cmd = parts[0]

    if cmd in {"!reset", "!phasmoreset"}:
        return default_state(state.get("room", "default")), "Run reset."

    if cmd in {"!mode", "!evidencemode"}:
        mode = parts[1] if len(parts) > 1 else ""
        if mode in {"0", "1", "2", "3"}:
            state["evidenceMode"] = mode
            return state, f"Evidence mode set to {mode}."
        return state, "Use !mode 3, !mode 2, !mode 1, or !mode 0."

    if cmd in {"!responds", "!response", "!interact"}:
        value = parts[1] if len(parts) > 1 else "unknown"
        if value in {"alone", "solo"}:
            state["responds"] = "alone"
        elif value in {"everyone", "all", "group"}:
            state["responds"] = "everyone"
        else:
            state["responds"] = "unknown"
        return state, f"Responds set to {state['responds']}."

    if cmd in {"!ev", "!evidence"}:
        key = EVIDENCE_ALIASES.get(parts[1], "") if len(parts) > 1 else ""
        if not key:
            return state, f"Unknown evidence: {parts[1] if len(parts) > 1 else 'blank'}."

        value = _normalize_value(parts[2] if len(parts) > 2 else "unknown", "evidence")
        state.setdefault("evidence", {})[key] = value
        return state, f"{key} set to {value}."

    if cmd in {"!b", "!beh", "!behavior"}:
        if not _ALLOW_BEHAVIOR_COMMANDS:
            return state, "Behavior chat commands are disabled. Use evidence commands only for now."

        key = BEHAVIOR_ALIASES.get(parts[1], "") if len(parts) > 1 else ""
        if not key:
            return state, f"Unknown behavior: {parts[1] if len(parts) > 1 else 'blank'}."

        value = _normalize_value(parts[2] if len(parts) > 2 else "observed", "behavior")
        state.setdefault("behaviors", {})[key] = value
        return state, f"{key} set to {value}."

    return state, "Command not recognized. Try !ev emf yes, !responds alone, !mode 3, or !reset."


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
                current["evidence"].update({k: v for k, v in body["evidence"].items() if k in EVIDENCE})
            if "behaviors" in body and isinstance(body["behaviors"], dict):
                current["behaviors"].update(body["behaviors"] or {})
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

    with _STATE_LOCK:
        state = read_state(safe_room)
        state, result = apply_command(state, command)
        state["lastCommand"] = command
        state["lastCommandResult"] = result
        write_state(safe_room, state)

    return {"ok": True, "result": result, "state": state}
