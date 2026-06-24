# Phasmo Helper v5.5.2 — Static Page Layout and Footer Cleanup

## Added
- Visible release notes entry for v5.5.2.

## Fixed
- Static help and policy pages no longer use room/session headers such as `ROOM: KAIZEN • SETUP NEEDED`.
- Getting Started and Terms page spacing so action buttons do not collide with following headings.
- Footer clutter on mobile by grouping links and removing duplicates/low-priority links from the always-visible footer.

## Changed
- Static pages now use a simpler evergreen help-page header.
- Footer is grouped into help, support, and policy/version rows.
- Default app version is now `v5.5.2`.

## Deployment
Apply over the repo, then commit directly to `main` for the live hotfix:

```powershell
git checkout main
git pull origin main
git add main.py phasmo_helper PHASMO_FULL_MODULAR_REBUILD_NOTES.md requirements.example.txt .github docs
git commit -m "Hotfix static page layout and footer cleanup"
git push origin main
```

After Railway deploys, set or confirm:

```text
PHASMO_APP_VERSION=v5.5.2
```

## Verify
- `/phasmo`
- `/phasmo/getting-started`
- `/phasmo/terms`
- `/phasmo/release-notes`
- Footer shows Version v5.5.2.
