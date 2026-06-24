# Phasmo Helper Scheduled Release Automation

This build adds the app-side support and GitHub Actions workflow for scheduled maintenance/deployment windows.

## Branch model

- `main` = production branch connected to Railway.
- `release` = staged build waiting for the next maintenance window.

Do local testing first. When the update is ready, push it to `release`. The scheduled workflow merges `release` into `main` during the maintenance window.


## Create the release branch once

The v5.4 files add the workflow, but GitHub will not show a `release` branch until you create and push it. Do this once after v5.4+ is on `main`:

```powershell
git checkout main
git pull origin main
git checkout -b release
git push -u origin release
git checkout main
```

After that, GitHub should show both `main` and `release` branches. Future staged updates go to `release`; production remains on `main` until the scheduled workflow merges it.

If the scheduled workflow says no release branch exists, run the commands above and then re-run the workflow with `dry_run=true`.

## GitHub repository secrets

Add these in GitHub → Repository → Settings → Secrets and variables → Actions:

- `PHASMO_BASE_URL` = your public Railway URL, for example `https://web-production-12aee.up.railway.app`
- `PHASMO_OPS_TOKEN` = a long random token used by GitHub Actions to call protected ops endpoints
- `DISCORD_WEBHOOK_URL` = Discord webhook for maintenance/deployment notices

## Railway variables

Add this to the Phasmo Helper Railway service:

- `PHASMO_OPS_TOKEN` = the same token used in GitHub Actions

Optional:

- `PHASMO_APP_VERSION=v5.4.1`
- `PHASMO_STATE_DIR=/data/phasmo_state` if using a Railway volume

## New ops endpoints

- `GET /api/phasmo/health`
- `GET /api/phasmo/version`
- `GET /api/phasmo/maintenance`
- `POST /api/phasmo/ops/maintenance/start`
- `POST /api/phasmo/ops/maintenance/end`
- `POST /api/phasmo/ops/banner`

POST ops endpoints require:

`Authorization: Bearer <PHASMO_OPS_TOKEN>`

## Workflow schedule

The workflow file is:

`.github/workflows/scheduled-phasmo-release.yml`

It has two UTC cron entries and a runtime Pacific-time guard so it runs at 9 PM America/Los_Angeles in both daylight and standard time.

## Manual test

Go to GitHub → Actions → Scheduled Phasmo Release → Run workflow.

Use:

- release branch: `release`
- dry_run: `true`

If dry run works, set dry_run to `false` after a staged release branch exists.

## Expected behavior

When a release is staged:

1. Discord posts maintenance starting.
2. GitHub Actions calls Phasmo maintenance start.
3. The app shows the orange maintenance banner and can go read-only.
4. `release` fast-forwards into `main`.
5. Railway deploys from `main`.
6. GitHub Actions checks `/api/phasmo/health`.
7. Discord posts complete or failed.
8. GitHub Actions calls Phasmo maintenance end.

If no release is staged, the workflow posts a routine maintenance/refresh notice and does not deploy code.
