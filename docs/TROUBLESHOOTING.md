# Troubleshooting

- Not ready: open `/api/phasmo/content/validation`; fix every error, then use the protected content reload endpoint.
- Streamer.bot 401: confirm the local and hosted `PHASMO_ADMIN_TOKEN` values match and HTTPS is used.
- Permission denied: inspect the action in `/api/phasmo/permissions` and verify that Streamer.bot forwards Twitch role flags.
- Room locked: provide the four-digit room passcode; integration tokens do not replace room passcodes.
- Lost state after deploy: point `PHASMO_STATE_DIR` at a Railway Volume or other persistent disk.
- Overlay is stale: verify the browser source uses the correct `room` query value and can reach `/api/phasmo/state`.
- Deildegast missing: check that content version `2026.08.09` is active and reload content.

Include `/health`, `/ready`, `/version`, content validation, room name, and build commit in a bug report. Never include tokens or room passcodes.
