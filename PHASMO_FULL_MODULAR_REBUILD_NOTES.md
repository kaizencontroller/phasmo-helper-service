# Phasmo Helper v5.5.1 — Homepage and Release Notes Cleanup

This hotfix cleans up the v5.5 public-beta help page rollout and makes the live app version visible from the footer.

## Fixed

- Simplified the home page hero section so **Create Room** is the clear primary action.
- Moved secondary links such as Leaderboard and Streamer.bot Setup out of the hero action cluster and back into support/footer navigation.
- Updated the visible `/phasmo/release-notes` page with the v5.5 and v5.5.1 entries.

## Added

- App version display in the footer on public/helper pages.
- Runtime app version fetch for the main helper UI footer through `/api/phasmo/version`.

## Changed

- Default app version is now `v5.5.1`.

## Deployment / Staging Instructions

This hotfix should be staged on the `release` branch and deployed by the scheduled maintenance workflow.

If your local `release` branch is currently in a failed rebase, first clean it up:

```powershell
git rebase --abort
git checkout main
git pull origin main
git checkout release
git reset --hard origin/main
```

Then extract this package over the repo and stage the hotfix:

```powershell
git status
git add main.py phasmo_helper PHASMO_FULL_MODULAR_REBUILD_NOTES.md requirements.example.txt .github docs
git commit -m "Stage Phasmo homepage and release notes cleanup"
git push --force-with-lease origin release
```

Run the scheduled workflow dry-run first:

```text
Actions → Scheduled Phasmo Release → Run workflow
release_branch = release
dry_run = true
```

If the dry-run succeeds, run it again with:

```text
dry_run = false
```

## Railway Variables

Update after deployment:

```text
PHASMO_APP_VERSION=v5.5.1
```

Keep existing:

```text
PHASMO_DEV_ADMIN_CODE=<your private admin code>
PHASMO_OPS_TOKEN=<same token used in GitHub Actions>
```
