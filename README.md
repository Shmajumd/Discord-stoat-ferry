# Discord Ferry

**Migrate your Discord server to Stoat (formerly Revolt) — messages, channels, roles, emoji, attachments, and all.**

> One-click app for Windows and Mac. CLI for Linux.
> No coding required. Your data stays on your machine.

[screenshot placeholder — validate screen + migrate screen]

---

## Download

| Platform | Download | Size |
|----------|----------|------|
| **Windows** | Ferry.exe (v0.1.0) | ~XX MB |
| **macOS** | Ferry.dmg (v0.1.0) | ~XX MB |
| **Linux / pip** | `pipx install discord-ferry` | — |

---

## How It Works (3 Steps)

### Step 1: Export your Discord server

Use DiscordChatExporter to save your server locally.
[Detailed guide](docs/getting-started/export-discord.md)

### Step 2: Open Ferry and connect to your Stoat instance

Point Ferry at your export folder, enter your Stoat URL and token.
[screenshot placeholder]

### Step 3: Click Migrate

Your messages, channels, roles, emoji and attachments migrate to Stoat.
Original authors show up via masquerade. Pins are preserved.
[screenshot placeholder]

---

## How long does it take?

About **1 message per second** due to Stoat API rate limits. That means:
- 1,000 messages ~ 17 minutes
- 10,000 messages ~ 3 hours
- 100,000 messages ~ 28 hours (run overnight!)

Ferry can **pause and resume** — close it anytime, pick up where you left off.

---

## What gets migrated?

| Feature | Status |
|---------|--------|
| Text channels | Supported |
| Categories | Supported |
| Roles (with colours) | Supported |
| Messages + author names | Supported (via masquerade) |
| File attachments | Supported |
| Custom emoji | Supported (up to 100) |
| Pinned messages | Supported |
| Replies | Supported |
| Reactions | Supported (without per-user attribution) |
| Threads | Supported (as text channels) |
| Forum posts | Supported (as text channels) |
| Voice channels | Partial (created but may not work — Stoat bug) |
| Stickers | Info only (shown as text placeholder) |
| Original timestamps | Info only (shown in message text, not metadata) |

---

## Detailed Guides

- [Exporting from Discord (step-by-step)](docs/getting-started/export-discord.md)
- [Setting up your Stoat instance](docs/getting-started/setup-stoat.md)
- [Your first migration (full walkthrough)](docs/getting-started/first-migration.md)
- [GUI guide (every screen explained)](docs/guides/gui-walkthrough.md)
- [CLI reference](docs/guides/cli-reference.md)
- [Migrating large servers (100k+ messages)](docs/guides/large-servers.md)
- [Troubleshooting](docs/guides/troubleshooting.md)

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT
