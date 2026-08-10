# Streamer.bot Integration 2.0

Streamer.bot is an adapter. The hosted service owns command lookup, permission checks, validation, execution, responses, logging, and analytics.

1. Install `flask` and `requests` on the streaming PC.
2. Set `RAILWAY_BASE_URL`, `PHASMO_ROOM`, and `PHASMO_ADMIN_TOKEN`.
3. Run `python local_phasmo_streamerbot_bridge.py`.
4. Configure one Streamer.bot Web Request action at `http://127.0.0.1:8765/streamerbot/phasmo`.
5. POST JSON containing `command`, `user`, and available Twitch role flags such as `isBroadcaster`, `isMod`, `isVip`, `isSubscriber`, and `isFollower`.

The bridge sends outbound HTTPS only and supplies both `Authorization: Bearer` and `X-Phasmo-Token` for compatibility. `/health` on port 8765 reports adapter readiness without exposing tokens.

Profiles can route channels/bots to default rooms. The provider-neutral `IChatProvider` boundary permits future EventSub, Discord, Kick, or YouTube adapters without moving command logic out of the service.
