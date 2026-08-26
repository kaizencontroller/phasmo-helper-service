# Release Notes

## v5.8.6 - Candidate-based sanity warning

- Hunt Risk now always posts the highest hunt percentage among the remaining candidates, without requiring team sanity entry.
- Team sanity, when entered, adds current-hunt context but no longer gates the warning.

## v5.8.5 - Display mode toggle

- Added a persistent Low profile / Full screen toggle for desktop Control sessions.
- Full screen uses the available browser width and expands candidate and tracker layouts; narrow screens remain optimized for mobile.

## v5.8.4 - Loading-state hotfix

- Versioned the Control page assets so browsers cannot combine the updated page with an older cached script.
- Added a temporary compatibility bridge for already-cached v5.8.2 JavaScript.

## v5.8.3 - Control flow and live hunt risk

- Moved weather and ghost response settings to Control, where they are learned during the investigation.
- Added an in-place New Round shortcut requiring only the new map while retaining editable player and difficulty defaults.
- Added live hunt-risk guidance from current team sanity and the ghosts still in consideration, including special-condition warnings.

## v5.8.2 - Quality of Life Part 2 compatibility

- Updated supported game metadata to Phasmophobia v0.19.0.0.
- Added selectable Restricted variants for Prison, Brownstone High School, and Point Hope, including chat aliases and map guidance.
- Revalidated the 13 Willow Street rework room registry and Deildegast evidence, behavior, aliases, commands, and encyclopedia content.
- Documented shared journal selections and duplicate media indicators from the official update.

## v5.8.1 - UX, Integration & Polish

- Added a responsive workspace navigation and live version/integration status.
- Redesigned the home dashboard around rooms, the ghost field guide, stream setup, and advanced exports.
- Added Basic/Advanced progressive disclosure with a remembered preference.
- Added Streamer.bot health and command telemetry, inherited role permissions, and permission explanations.
- Added an Integration Center and privacy-sanitized JSON/ZIP Export Center.
- Added an application event bus for room, evidence, elimination, round, session, and viewer-guess events.
- Preserved the v5.8 content registry, including the Deildegast ghost and the commonly searched Dildegeist alias.

## v5.8.0 - Kaizen Platform Evolution

- Added official Deildegast support across evidence, elimination, overlays, guesses, scoring, analytics, commands, and encyclopedia. Common `Dildegeist` spelling is accepted as an alias.
- Added game v0.18.0.1 metadata, Willow Street reworked room IDs with legacy aliases, and EMF Level 5 photo/objective definitions.
- Added validated data-driven content registry and protected hot reload.
- Added searchable Ghost Encyclopedia, investigation timeline/replay, and JSON/CSV/Markdown session summaries.
- Added provider-neutral chat interface, command registry/dispatcher, role permission matrix, custom groups, and expiring user grants.
- Expanded investigation analytics and platform health/readiness/version metadata.
- Updated Kaizen manifest, dark Creative theme metadata, standalone/platform deployment profile, setup, commands, FAQ, privacy, retention, and troubleshooting documentation.

See the in-app `/phasmo/release-notes` and `/phasmo/whats-new` pages.
