# Phasmo Helper v5.8

Phasmo Helper is a Kaizen Creative Application and a standalone Railway-ready FastAPI service. It provides evidence elimination, behavior tracking, shared rooms, OBS overlays, chat guessing, leaderboards, investigation history, analytics, and a searchable ghost encyclopedia.

Supported Phasmophobia version: **0.18.0.1**. This includes the **Deildegast**, the reworked **13 Willow Street**, and the **EMF Level 5 photo** category.

## Architecture

- Platform: deployment, configuration, health/readiness, manifests, permissions, integrations, themes, maintenance, and release metadata.
- Application: investigation state, ghost logic, overlays, rooms, scoring, analytics, and encyclopedia.
- Content: versioned JSON under `phasmo_helper/content/`.

The service runs inside Kaizen Controller or independently. `KAIZEN_PLATFORM_URL` enables shared platform support without making standalone startup depend on the platform.

## Quick start

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8011
```

Open `http://127.0.0.1:8011/phasmo`. See [Setup](docs/SETUP.md) and the [Streamer.bot guide](docs/STREAMERBOT_GUIDE.md).

## Important routes

- `/phasmo` - application home
- `/phasmo/control?room=kaizen` - investigation control
- `/phasmo/overlay?room=kaizen` - OBS browser source
- `/phasmo/encyclopedia` - ghost encyclopedia
- `/phasmo/timeline?room=kaizen` - investigation replay and exports
- `/phasmo/dev-admin` - protected developer operations
- `/health`, `/ready`, `/version` - platform discovery
- `/api/phasmo/content/validation` - startup/content validation report

## Configuration

Copy `.env.example` into your deployment provider and set secrets there. Do not commit tokens. Production recommendations:

```text
PHASMO_ADMIN_TOKEN=<random integration token>
PHASMO_OPS_TOKEN=<separate operations token>
PHASMO_DEV_ADMIN_CODE=<private admin code>
PHASMO_STATE_DIR=/data/phasmo_state
PHASMO_APP_VERSION=v5.8.0
KAIZEN_PLATFORM_VERSION=contract-1.0
```

Bearer and legacy `X-Phasmo-Token` headers are supported by the local adapter. Room passcodes remain available for browser-room compatibility.

## Content updates

Update JSON files, then call `POST /api/phasmo/ops/content/reload` with the Ops token. Invalid candidate content is rejected and the last valid registry remains active. Validation detects duplicate ghost/room IDs, broken references, invalid evidence, missing encyclopedia fields, invalid commands, and permission errors.

## Documentation

- [Chat commands](docs/CHAT_COMMANDS.md)
- [FAQ](docs/FAQ.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Platform contract](docs/KAIZEN_PLATFORM_MIGRATION.md)
- [Release notes](docs/RELEASE_NOTES.md)
- [Privacy and retention](docs/PRIVACY.md)
