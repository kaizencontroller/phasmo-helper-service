# Phasmo Helper v5.5 — Public Beta Help and Policy Pages

This staged update is a low-risk public beta polish release. It adds clearer help pages for new users and lightweight policy/retention pages now that the tool is being shared beyond the project owner.

## Added

- `/phasmo/getting-started` — quick flow for new streamers/testers.
- `/phasmo/commands` — viewer command guide for guesses, votes, evidence, behaviors, results, and room routing.
- `/phasmo/privacy` — lightweight privacy note for the public beta.
- `/phasmo/terms` — basic stream-safe usage expectations and moderation language.
- `/phasmo/data-retention` — explains temporary rooms, bug tracker exports, and beta persistence limits.
- Footer links to the new help and policy pages.
- Home page quick links for Getting Started and Viewer Commands.

## Changed

- Default app version is now `v5.5`.
- Release notes page includes this v5.5 entry.
- Build package excludes Python cache files so staged release commits stay cleaner.

## Why this update matters

The app is moving from personal/test use toward a public beta. These pages set expectations before more people create rooms, submit reports, and use Streamer.bot integration.

## Deployment / Staging Instructions

This release is intended to be staged on the `release` branch and deployed by the scheduled maintenance workflow.

```powershell
git checkout release
git pull origin release
# extract this package over the repo
git status
git add main.py phasmo_helper PHASMO_FULL_MODULAR_REBUILD_NOTES.md requirements.example.txt .github docs
git commit -m "Stage Phasmo public beta help pages"
git push
```

Then run a dry-run from GitHub Actions:

```text
Actions → Scheduled Phasmo Release → Run workflow
release_branch = release
dry_run = true
```

If the dry-run is clean, the scheduled 9 PM Pacific maintenance workflow can merge `release` into `main` automatically.

## Railway Variables

Update after deployment:

```text
PHASMO_APP_VERSION=v5.5
```

Keep existing:

```text
PHASMO_DEV_ADMIN_CODE=<your private admin code>
PHASMO_OPS_TOKEN=<same token used in GitHub Actions>
```

## Notes

This update does not change core gameplay logic, passcode enforcement, or room state behavior. It is primarily public-beta documentation and navigation polish.
