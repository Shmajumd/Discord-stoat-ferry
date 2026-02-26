"""Content transformation: markdown, mentions, emoji, spoilers, embeds."""


def convert_spoilers(content: str) -> str:
    """Convert Discord spoiler syntax (||) to Stoat syntax (!!)."""
    # TODO: implement with code block awareness
    raise NotImplementedError


def remap_mentions(content: str) -> str:
    """Remap Discord mention IDs to Stoat IDs or plain text fallback."""
    # TODO: implement
    raise NotImplementedError


def remap_emoji(content: str) -> str:
    """Remap Discord custom emoji to Stoat emoji IDs."""
    # TODO: implement
    raise NotImplementedError


def flatten_embed(embed: dict[str, object]) -> dict[str, object]:
    """Convert Discord embed to Stoat-compatible SendableEmbed."""
    # TODO: implement
    raise NotImplementedError


def format_original_timestamp(iso_timestamp: str) -> str:
    """Format Discord timestamp for prepending to message content."""
    # TODO: implement
    raise NotImplementedError
