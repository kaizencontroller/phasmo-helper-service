# Kaizen Phasmo Helper — Full Modular Rebuild v4

This package keeps the original mobile-first Phasmo Helper design but splits the app into a lighter modular layout.

## Main changes from v3

- Added `PHASMO_QUICKSTART_VIDEO_URL` Railway environment variable.
  - When set, the homepage/footer show a Quick Start Video link.
- Added `/phasmo/streamerbot` setup page.
- Added Streamer.bot default-room routing:
  - `!phasmo-room <room>`
  - `!phasmo room <room>`
  - `!setroom <room>`
- `/api/phasmo/command` now accepts the room in the JSON body:
  - `room`
  - `phasmoRoom`
  - `roomName`
- `/api/phasmo/command` can route by stored Streamer.bot profile when room is omitted and channel/bot info is supplied.
- Added `/api/phasmo/streamerbot/profile` GET/POST endpoints.
- Added independent display modes:
  - `controlMode`: `helper` or `tracker`
  - `overlayMode`: `helper` or `tracker`
- Setup screen now exposes Control Screen Mode and Overlay Mode.
- Tracker mode hides the next-best-test panel on control.
- Tracker overlay shows simplified game state/evidence/candidates without suggested next test.
- Kept bug reports as a footer link instead of a large inline homepage form.
- Kept public pages narrow/mobile-first like the original setup/control pages.

## Railway environment variables

Optional:

```text
PHASMO_QUICKSTART_VIDEO_URL=https://your-video-link-here
PHASMO_STATE_DIR=/tmp/phasmo_state
PHASMO_ROOM_TTL_SECONDS=14400
PHASMO_SUPPORT_WEBHOOK_URL=...
```

## Streamer.bot recommended command body

Use a single endpoint:

```text
POST /api/phasmo/command
```

Example JSON body:

```json
{
  "room": "%phasmoRoom%",
  "command": "%rawInput%",
  "user": "%userName%",
  "source": "streamerbot",
  "channel": "%broadcasterUserName%",
  "botAccount": "%botName%"
}
```

If you do not want a Streamer.bot variable, use the remembered-room workflow:

```text
!phasmo-room kaizen
!guess Deogen
!ev orbs yes
!be 12 yes
!result Deogen
```

The server will remember the default room for the supplied channel/bot profile.

## Local test

```powershell
cd "$HOME\Documents\Kaizen_Controller\phasmo-helper-service"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements
$env:PHASMO_STATE_DIR="$PWD\.local_state"
$env:PHASMO_QUICKSTART_VIDEO_URL="https://example.com/quickstart"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/phasmo
http://127.0.0.1:8000/phasmo/streamerbot?room=test
http://127.0.0.1:8000/phasmo/setup?room=test
http://127.0.0.1:8000/phasmo/control?room=test
http://127.0.0.1:8000/phasmo/overlay?room=test
```

Command test:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/phasmo/command" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"command":"!phasmo-room test","user":"mod","channel":"kaizencontroller","source":"streamerbot"}'

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/phasmo/command" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"command":"!guess Deogen","user":"viewer","channel":"kaizencontroller","source":"streamerbot"}'
```

## v5.1 hotfix
- Prevented the 1-second polling loop from repainting over active Room/Round Setup edits.
- Added a dirty-form guard so room names, passcodes, map/weather/difficulty, player count, and response settings do not snap back while the streamer is typing before saving.
- `main.py` remains a tiny entrypoint importing `phasmo_helper.app`.
