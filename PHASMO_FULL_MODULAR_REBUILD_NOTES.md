# Phasmo Helper v5.4.1 — Dev Admin Privacy + Release Branch Setup Cleanup

This revision is a small operational hotfix on top of v5.4. It tightens the Dev Admin page and makes the release automation setup clearer.

## Added

- Dev Admin unlock/bootstrap flow:
  - Admin tools stay hidden until the admin code is accepted.
  - Banner, maintenance, and tracker data are loaded only after unlock.
- Dev Admin Maintenance / Release Automation panel:
  - View current maintenance state.
  - Manually start maintenance for local/testing.
  - Manually end maintenance as success or failure.
- Dev Admin bootstrap endpoint:
  - `POST /api/phasmo/dev-admin/bootstrap`
- Updated release notes page with v5.4.1, v5.4, and v5.3 summaries.

## Changed

- Dev Admin no longer shows banner, bug tracker, sample data, or maintenance controls before entering a valid admin code.
- Default app version changed to `v5.4.1`.
- Release automation docs now clearly explain that the `release` branch must be created and pushed once before GitHub can display it or the workflow can deploy from it.

## Deployment / Operations

Create the release branch once after this update is on `main`:

```powershell
git checkout main
git pull origin main
git checkout -b release
git push -u origin release
git checkout main
```

Going forward:

- `main` = production branch connected to Railway.
- `release` = staged update branch waiting for the maintenance window.

## Required / Recommended Variables

In Railway:

```text
PHASMO_OPS_TOKEN=<same long random token used in GitHub Actions>
PHASMO_APP_VERSION=v5.4.1
PHASMO_DEV_ADMIN_CODE=<your private admin code>
```

In GitHub Actions secrets:

```text
PHASMO_BASE_URL=https://your-production-railway-url
PHASMO_OPS_TOKEN=<same long random token as Railway>
DISCORD_WEBHOOK_URL=<Discord webhook URL>
```

## Notes

This update does not change gameplay logic. It is primarily a release operations, Dev Admin privacy, and documentation cleanup update.
