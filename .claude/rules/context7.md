---
globs:
  - "src/**/*.py"
  - "pyproject.toml"
---

# Context7 — Live Library Documentation

Before writing any API code that uses these libraries, fetch live documentation via Context7 MCP to verify current API signatures:

- **stoat-py** — `stoat` module: Client, HTTPClient, Permissions, MessageMasquerade, Reply, SendableEmbed, ChannelType
- **NiceGUI** — `nicegui` module: ui components, native mode, progress bars, file dialogs
- **Click** — CLI decorators, options, arguments, groups
- **Rich** — Progress bars, live display, console, tables

## How

Use the `mcp__plugin_context7_context7__resolve-library-id` tool to find the library, then `mcp__plugin_context7_context7__query-docs` to fetch relevant documentation.

## When

- Before implementing any new stoat.py API call (especially less common ones like `edit_category`, `create_emoji`, `pin_message`)
- Before implementing NiceGUI screens (verify component APIs match current version)
- When encountering unexpected behavior from a library call
- When the brief says "verify at implementation time" (see brief §15)
