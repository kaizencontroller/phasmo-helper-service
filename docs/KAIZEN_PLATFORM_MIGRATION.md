# Phasmo Helper Kaizen Platform Migration

Phasmo Helper is registered as `phasmo-helper` and can run standalone or in
cooperative Platform mode.

## Local contract

- Launcher: `run.bat`
- Base URL: `http://127.0.0.1:8011/phasmo`
- Health: `http://127.0.0.1:8011/health`
- Readiness: `http://127.0.0.1:8011/ready`
- Version: `http://127.0.0.1:8011/version`
- State owner: Phasmo Helper
- Local state default: `.kaizen-data`

Copy `.env.example` into the environment used by the launcher and replace the
placeholder admin token.

## Platform support

Set:

```text
KAIZEN_PLATFORM_URL=http://127.0.0.1:5148
```

Footer links will open the shared Platform report form and include application,
version, and source-page context. Without this variable, the existing
`/phasmo/bug-report` flow remains available.

## Ownership boundary

Still application-owned:

- Rooms and room state
- Evidence and ghost behavior data
- Streamer.bot commands and local bridge
- Leaderboards and usage analytics
- Phasmo-specific configuration and admin behavior

Moved to Platform:

- Generic support intake HTTP contract
- Shared support form and JSONL receiver
- Runtime-neutral browser support client
