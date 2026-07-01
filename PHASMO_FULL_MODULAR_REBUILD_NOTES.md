# Phasmo Helper v5.6 — Room Usage Log and Session Analytics

## Added
- Dev Admin **Room Usage Log** showing room usage, observed rounds, completed rounds, active duration, last seen time, command/write counts, and support/channel notes.
- Aggregate room usage tracking whenever room state is saved, including room creation, Next Round, Reset Current Round, confirmed contract results, End Session, jumpscare events, and Streamer.bot commands.
- Room usage JSON export/import so usage history can be preserved between builds while the app is still using file-based storage.
- Room usage CSV export for quick review in Excel/Sheets.
- Lightweight room usage event stream for milestone events.
- Visible release notes entry for v5.6.

## Changed
- Default app version is now `v5.6`.
- Room state writes now update operational analytics, but usage logging intentionally avoids storing room passcodes or support contact details.
- Dev Admin now has a clearer path for reviewing both bug reports and real-world room/session usage.

## Files Added
- `phasmo_helper/services/usage.py`

## Data Files Created at Runtime
These are stored under `PHASMO_STATE_DIR`:

- `__global_room_usage.json`
- `__global_room_usage_events.jsonl`

## Deployment
For the next staged release, apply over the repo and commit to the `release` branch:

```powershell
git checkout release
git pull origin release
# extract v5.6 over the repo folder
git status
git add main.py phasmo_helper PHASMO_FULL_MODULAR_REBUILD_NOTES.md requirements.example.txt .github docs
git commit -m "Stage Phasmo room usage analytics"
git push
```

If you decide this should be a direct live update instead:

```powershell
git checkout main
git pull origin main
# extract v5.6 over the repo folder
git status
git add main.py phasmo_helper PHASMO_FULL_MODULAR_REBUILD_NOTES.md requirements.example.txt .github docs
git commit -m "Add Phasmo room usage analytics"
git push origin main
```

After Railway deploys, set or confirm:

```text
PHASMO_APP_VERSION=v5.6
```

## Verify
- `/phasmo/dev-admin`
  - Unlock admin tools.
  - Use **Room Usage Log** → Refresh Usage.
  - Create/use a test room, click Next Round, confirm a result, then End Session.
  - Refresh Room Usage Log and confirm rounds/duration update.
  - Export JSON and CSV.
- `/phasmo/release-notes`
  - Confirm v5.6 is listed at the top.
- `/api/phasmo/health`
  - Confirm the app still reports healthy.

## Notes
- Usage analytics are operational support data for public beta learning. They are not a replacement for persistent storage.
- For long-term production reliability, continue moving toward a Railway Volume or database-backed state store.
