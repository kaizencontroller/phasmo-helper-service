# Kaizen Phasmophobia Helper - Railway FastAPI Version

Kaizen Platform packaging and the optional shared support runtime are documented
in `docs/KAIZEN_PLATFORM_MIGRATION.md`.

This is a standalone Railway-ready service for the Phasmophobia evidence/ghost helper.

## Hosted URLs

After deployment:

```text
https://YOUR-RAILWAY-APP/phasmo/control?room=kaizen
https://YOUR-RAILWAY-APP/phasmo/overlay?room=kaizen
```

Use `/phasmo/overlay?room=kaizen` as an OBS Browser Source.

## Railway variables

Recommended:

```text
PHASMO_ADMIN_TOKEN=make-a-random-secret
PHASMO_STATE_DIR=/tmp/phasmo_state
PHASMO_ALLOW_BEHAVIOR_COMMANDS=true
```

`PHASMO_ADMIN_TOKEN` protects POST updates from the local Streamer.bot bridge.
If you leave it blank, anyone with the API URL could post commands, so use a token.

## Local Streamer.bot bridge

Run locally on the streaming PC:

```powershell
cd "PATH_TO_THIS_FOLDER"
python -m pip install flask requests
$env:RAILWAY_BASE_URL="https://YOUR-RAILWAY-APP"
$env:PHASMO_ROOM="kaizen"
$env:PHASMO_ADMIN_TOKEN="same-token-as-railway"
$env:PHASMO_OWNER_USERS="kaizencontroller"
python local_phasmo_streamerbot_bridge.py
```

Health check:

```text
http://127.0.0.1:8765/health
```

## Streamer.bot Web Request action

Create a Web Request action:

```text
URL: http://127.0.0.1:8765/streamerbot/phasmo
Method: POST
Content-Type: application/json
```

Body:

```json
{
  "command": "%rawInput%",
  "user": "%user%",
  "isMod": "%isMod%",
  "isBroadcaster": "%isBroadcaster%"
}
```

Command triggers to point at that action:

```text
!ev
!evidence
!responds
!response
!mode
!reset
!ignore
!unignore
!ignored
!modadd
!modremove
!mods
```

## Command permissions

Normal chatters:
- `!ev emf yes/no/unknown`
- `!ev dots yes/no/unknown`
- `!ev freezing yes/no/unknown`
- `!ev orb yes/no/unknown`
- `!ev writing yes/no/unknown`
- `!ev box yes/no/unknown`
- `!ev uv yes/no/unknown`

Admins/mods:
- `!responds alone/everyone/unknown`
- `!mode 3/2/1/0`
- `!reset`
- `!ignore USERNAME`
- `!unignore USERNAME`
- `!ignored`
- `!mods`

Owner/broadcaster:
- `!modadd USERNAME`
- `!modremove USERNAME`

KaizenController is included as the default owner if `PHASMO_OWNER_USERS` is not set.
