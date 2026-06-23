# Phasmo Helper Full Modular Rebuild v5.3

This build rolls v5.1/v5.2 fixes forward and adds the next production-readiness pass for shared/public use.

## Added

- Locked-room entry gate before loading room-specific pages.
  - Direct links to `/phasmo/control`, `/phasmo/round`, `/phasmo/config`, `/phasmo/overlay`, and `/phasmo/leaderboard` now show a passcode screen first when the room is locked.
  - Correct 4-digit room code is remembered in localStorage per browser/room.
  - Incognito or a new browser must enter the code again.
- Server-side locked-room enforcement for reads, writes, and Streamer.bot commands.
  - Locked room state reads without a code return `403`.
  - Locked room writes without a code return `403`.
  - Closed room access returns `410`.
- End Session / Close Room flow.
  - Ends the current room session.
  - Removes the room from Active Rooms.
  - Preserves scored history/leaderboard data.
- Clearer control-screen guardrails.
  - `Next Round` is for continuing play in the same room.
  - `End Session / Close Room` is for when the group is done playing.
  - `Reset Current Round` moved into a danger/details area with confirmation text.
- Server-side room name validation and content filtering.
  - Room names must be 3–32 characters.
  - Allowed characters: letters, numbers, spaces, hyphens, underscores.
  - Blocks URLs, reserved names, excessive repeated characters, and a conservative public-safety blocklist.
  - Optional extra blocklist patterns can be supplied with `PHASMO_ROOM_NAME_BLOCKLIST_EXTRA`.
- App-level abuse/cost-protection controls.
  - Basic in-memory rate limits for pages, state polling, state writes, commands, bug reports, feedback, and dev-admin endpoints.
  - Request body size cap via `PHASMO_MAX_REQUEST_BYTES`.
  - Temporary abuse/degraded modes via `PHASMO_ABUSE_MODE` and `PHASMO_DEGRADED_MODE`.
  - Failed passcode attempt throttling.
- Dev Admin site banner editor.
  - Protected by the existing dev admin code.
  - Lets you publish an editable Kaizen safety-orange banner across Phasmo pages.
  - Supports optional expiry timestamp.
- Dev Admin bug tracker table.
  - Submitted bug reports can now be triaged from `/phasmo/dev-admin`.
  - Supports status, priority, target version, fixed version, and internal notes.
  - Supports JSON export/import for carrying the tracker between builds.
- Overlay remaining-ghost news reel.
  - Overlay now shows all remaining ghost candidates as a scrolling ticker instead of only the first few alphabetical ghosts.
  - If only a few candidates remain, the display stays static.
- Global branded header behavior.
  - Public page branded headers now route back to `/phasmo`.
- Public banner endpoint: `/api/phasmo/banner`.

## Changed

- Round Setup no longer auto-redirects back to Control just because a round is active.
- Setup/config polling is less aggressive to avoid overwriting typing and to reduce request volume.
- Overlay/control polling is smarter:
  - Overlay remains fast.
  - Control is less aggressive.
  - Setup/room pages poll slower.
- Active Rooms hides closed sessions.
- Closed room files can be retained temporarily for history/export before cleanup.

## Fixed

- Passcode-protected rooms could previously be viewed or edited in some flows without entering the passcode.
- Incognito/new browser sessions could bypass parts of the old UI-level protection.
- Control → Round Setup navigation could bounce back to Control.
- Bug Reports page header was not consistently clickable as a Home link.
- Overlay candidate display could imply the first alphabetical ghosts were the most likely options.

## New / Updated Environment Variables

- `PHASMO_STATE_DIR` — state storage folder. Use a Railway Volume path for production persistence.
- `PHASMO_DEV_ADMIN_CODE` — required on Railway for `/phasmo/dev-admin`; local default remains `1234`.
- `PHASMO_MAX_REQUEST_BYTES` — max accepted request body size. Default `10000`.
- `PHASMO_ABUSE_MODE` — when true, tightens rate limits and pauses nonessential submissions.
- `PHASMO_DEGRADED_MODE` — when true, tightens polling limits without fully disabling features.
- `PHASMO_CLOSED_ROOM_RETENTION_SECONDS` — how long closed room files are retained before cleanup. Default 7 days.
- `PHASMO_ROOM_NAME_BLOCKLIST_EXTRA` — optional comma-separated regex patterns for additional blocked room names.

## Local Test Notes

Local dev-admin code defaults to:

```text
1234
```

Test locked-room behavior in incognito/private mode to verify that the browser is not using a previously saved room code.

## Suggested Git Commit

```powershell
git add main.py phasmo_helper PHASMO_FULL_MODULAR_REBUILD_NOTES.md requirements.example.txt
git commit -m "Add Phasmo locked-room gates session closure and dev tracker"
git push
```
