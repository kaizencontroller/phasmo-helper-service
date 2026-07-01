# Phasmo Helper Room Usage Analytics

Version: v5.6

## Purpose

The Room Usage Log gives the project owner a lightweight view of how the public beta is actually being used:

- which rooms were created
- whether rooms are open or closed
- how many rounds were observed
- how many rounds were completed/scored
- how long the room/session lasted
- how often commands or browser writes were sent
- when the room was last active

This is intended for beta support and capacity/process improvement, not personal tracking.

## Where to View

Open:

```text
/phasmo/dev-admin
```

Unlock with the Dev Admin code, then use:

```text
Room Usage Log → Refresh Usage
```

## Runtime Files

The app stores usage data in `PHASMO_STATE_DIR`:

```text
__global_room_usage.json
__global_room_usage_events.jsonl
```

## Export / Import

Use the Dev Admin Room Usage Log buttons:

- Export JSON — backup/restore between builds
- Import Usage JSON — merge usage history from a prior export
- Export CSV — quick analysis in Excel/Sheets

Imports merge by room and round id. Export before importing older files.

## Privacy / Safety Notes

The usage log intentionally avoids storing:

- room passcodes
- support contact details
- private admin codes

It may store room names, room status, support opt-in flag, support channel name, maps/difficulties, command counts, round counts, and milestone events.

## Long-Term Direction

This is still file-based beta telemetry. For a production-grade public app, move `PHASMO_STATE_DIR` to a Railway Volume or migrate room/session data to a database.
