# Privacy, Terms, and Data Retention

Phasmo Helper stores room names, investigation state, viewer command identities, guesses, votes, scoring history, command events, support submissions, and operational analytics required to provide the service. It does not require Twitch passwords and must not log bearer/ops tokens or room passcodes in analytics.

Room and integration data is used for gameplay, moderation, diagnostics, learning, and aggregate product improvement. Operators are responsible for disclosing chat participation and configuring retention appropriate to their community and jurisdiction.

Closed room files follow `PHASMO_CLOSED_ROOM_RETENTION_SECONDS`; active-room expiry follows `PHASMO_ROOM_TTL_SECONDS`. Leaderboard, summary, bug, feedback, and aggregate analytics files persist until an operator exports or removes them. Deleting a group or explicit permission removes future authorization but does not rewrite historical command events.

The software is an unofficial community helper and is provided without affiliation with or endorsement by Kinetic Games. Users remain responsible for platform, Twitch, OBS, Streamer.bot, and game terms.
