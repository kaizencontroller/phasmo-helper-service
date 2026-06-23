# Kaizen Phasmo Helper — Full Modular Rebuild v5

## Purpose
This revision keeps the original mobile-first Phasmo helper design, but finishes the workflow cleanup after v4.

## Key v5 changes

- Split setup flow conceptually:
  - `/phasmo/room` — reusable room/game settings.
  - `/phasmo/round` — contract-specific round setup.
  - `/phasmo/control` — active investigation screen.
- Kept `/phasmo/setup` as an alias for round setup for compatibility.
- Homepage CTA changed from `Start / Join Room` to `Create Room`.
- Header/logo click goes to `/phasmo` home.
- Moved Helper/Tracker display mode controls to `/phasmo/config`.
- Helper/Tracker choices are slider/segmented toggle controls instead of dropdowns.
- Config now includes room-level display modes and support opt-in, plus global command permission toggles.
- Contract Result confirmation is no longer a standing control-screen panel.
  - It appears only when clicking `Next Round` if there are unscored guesses/votes.
- Chat panel on control is compact by default.
  - Shows counts and leading vote/guess only.
  - Full details are expandable.
- Streamer.bot Setup page rewritten as a practical one-time SOP.
  - Streamer.bot setup happens before room creation.
  - Daily/weekly room changes should only update the `phasmoRoom` variable.
- Added unlisted dev admin panel:
  - `/phasmo/dev-admin`
  - Local default code: `1234`
  - Railway requires `PHASMO_DEV_ADMIN_CODE`; without it, the panel is disabled.
- Dev admin supports:
  - Load sample demo data.
  - Clear sample demo data.
  - Seed active rooms and leaderboard history.

## Important URLs

- Home: `/phasmo`
- Room setup: `/phasmo/room?room=kaizen`
- Round setup: `/phasmo/round?room=kaizen`
- Backward-compatible round setup alias: `/phasmo/setup?room=kaizen`
- Control: `/phasmo/control?room=kaizen`
- Overlay: `/phasmo/overlay?room=kaizen`
- Config: `/phasmo/config?room=kaizen`
- Streamer.bot SOP: `/phasmo/streamerbot?room=kaizen`
- Dev admin: `/phasmo/dev-admin`

## Local dev admin behavior

Local development uses `1234` if `PHASMO_DEV_ADMIN_CODE` is not set.

Railway/production disables the dev admin panel unless `PHASMO_DEV_ADMIN_CODE` is explicitly set.

## Local testing quick start

```powershell
cd "$HOME\Documents\Kaizen_Controller\phasmo-helper-service"
.\.venv\Scripts\Activate.ps1
pip install -r requirements
Remove-Item Env:\PHASMO_ADMIN_TOKEN -ErrorAction SilentlyContinue
$env:PHASMO_STATE_DIR="$PWD\.local_state"
$env:PHASMO_QUICKSTART_VIDEO_URL="https://example.com/quickstart"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open:

- `http://127.0.0.1:8000/phasmo`
- `http://127.0.0.1:8000/phasmo/dev-admin`
- Use code `1234` to load sample data.
- Then test:
  - `http://127.0.0.1:8000/phasmo/room?room=kaizen`
  - `http://127.0.0.1:8000/phasmo/round?room=kaizen`
  - `http://127.0.0.1:8000/phasmo/control?room=kaizen`
  - `http://127.0.0.1:8000/phasmo/config?room=kaizen`
  - `http://127.0.0.1:8000/phasmo/streamerbot?room=kaizen`

## Railway variables

Recommended:

```text
PHASMO_QUICKSTART_VIDEO_URL=https://your-current-video-link
PHASMO_DEV_ADMIN_CODE=<private admin code>
```

Optional:

```text
PHASMO_SUPPORT_WEBHOOK_URL=<discord-compatible-webhook>
PHASMO_ROOM_TTL_SECONDS=14400
```

Remove/blank:

```text
PHASMO_ADMIN_TOKEN
```

Room passcodes are now per-room 4-digit convenience locks, not global app tokens.
