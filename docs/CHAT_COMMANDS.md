# Chat Commands

Commands are defined in `phasmo_helper/content/commands.json`; aliases, help, permissions, cooldown metadata, visibility, and enabled state are data.

- `!evidence emf yes` (`!ev`) - update evidence.
- `!guess Deildegast` - lock a viewer guess.
- `!ghost Deildegast` - submit a decision vote or use a control override.
- `!behavior deildegast-moved-items-slow observed` (`!b`) - log behavior.
- `!actual Deildegast` - confirm and score the contract (moderator by default).
- `!reset` - reset the current round (moderator by default).
- `!reloadcontent` - validate and reload content (owner only, hidden).

Default roles are Owner, Broadcaster, Moderator, VIP, Subscriber, Follower, Viewer, and Guest. Dev Admin can define custom groups and explicit permanent or expiring user grants. Denials and disabled actions take precedence.
