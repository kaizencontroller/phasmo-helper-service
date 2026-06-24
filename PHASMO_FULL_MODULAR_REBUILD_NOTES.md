# Phasmo Helper v5.4 — Scheduled Release / Maintenance Automation

This revision builds on v5.3 and adds the app-side operations layer needed for scheduled maintenance windows and automated release deployment.

## Added

- Protected ops endpoints for GitHub Actions / CI automation:
  - `GET /api/phasmo/health`
  - `GET /api/phasmo/version`
  - `GET /api/phasmo/maintenance`
  - `POST /api/phasmo/ops/maintenance/start`
  - `POST /api/phasmo/ops/maintenance/end`
  - `POST /api/phasmo/ops/banner`
- `PHASMO_OPS_TOKEN` support for automation-only API access.
- Persistent maintenance state file in `PHASMO_STATE_DIR`.
- Dev Admin maintenance panel for local/manual testing of maintenance mode.
- Scheduled GitHub Actions workflow:
  - `.github/workflows/scheduled-phasmo-release.yml`
- Release automation guide:
  - `docs/PHASMO_RELEASE_AUTOMATION.md`

## Changed

- The public orange banner can now be controlled manually from Dev Admin or automatically through ops endpoints.
- Maintenance mode can make room updates temporarily read-only.
- Maintenance mode can pause new room creation.
- Health endpoint checks that the state directory exists and is writable.

## Deployment / Operations

- Use `main` as production.
- Use `release` as the staged update branch.
- GitHub Actions can merge `release` into `main` during the scheduled maintenance window.
- Discord webhook messages can announce:
  - routine refresh window
  - maintenance starting
  - deployment complete
  - deployment failed

## Acknowledgements Update

- Acknowledgements page now lists play testers as clickable links.
- Removed project-owner credit from the acknowledgements list.
- Added `xmysticalnerissa` to play testers.

## Required new variables

In Railway:

```text
PHASMO_OPS_TOKEN=<same long random token used in GitHub Actions>
PHASMO_APP_VERSION=v5.4
```

In GitHub Actions secrets:

```text
PHASMO_BASE_URL=https://your-production-railway-url
PHASMO_OPS_TOKEN=<same long random token as Railway>
DISCORD_WEBHOOK_URL=<Discord webhook URL>
```

## Notes

The workflow uses a fast-forward-only merge from `release` to `main`. If the branches diverge, the deployment fails safely instead of trying to auto-resolve conflicts.
