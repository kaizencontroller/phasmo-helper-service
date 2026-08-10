# Setup

## Standalone

1. Install Python 3.11 or newer.
2. Run `python -m pip install -r requirements.txt`.
3. Set `PHASMO_STATE_DIR` to a persistent writable folder.
4. Start `python -m uvicorn main:app --host 0.0.0.0 --port 8011`.
5. Verify `/health`, `/ready`, and `/version`.

Railway should use a Volume for `PHASMO_STATE_DIR`; `/tmp` is suitable only for disposable testing. Configure secrets through Railway variables.

## Kaizen Platform

Kaizen discovers `.kaizen/manifest.json`, launches `run.bat`, and checks `/health`. Set `KAIZEN_PLATFORM_URL` to route support reports through the platform. The app remains available if the shared platform runtime is absent.

## Room workflow

Create a room at `/phasmo/room`, set the contract map/difficulty/evidence mode, then open Control. Add the Overlay URL to OBS as a browser source. Closing a session preserves leaderboard and investigation analytics while making the room read-only.
