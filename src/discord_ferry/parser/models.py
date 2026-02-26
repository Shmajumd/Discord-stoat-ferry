"""Dataclasses for parsed DCE export data."""

from dataclasses import dataclass, field


@dataclass
class DCEAuthor:
    """Parsed message author."""

    id: str
    name: str
    discriminator: str = "0000"
    nickname: str = ""
    color: str | None = None
    is_bot: bool = False
    avatar_url: str = ""


@dataclass
class DCEAttachment:
    """Parsed message attachment."""

    id: str
    url: str
    file_name: str
    file_size_bytes: int = 0


@dataclass
class DCEMessage:
    """Parsed Discord message."""

    id: str
    type: str
    timestamp: str
    content: str
    author: DCEAuthor
    is_pinned: bool = False
    attachments: list[DCEAttachment] = field(default_factory=list)
    embeds: list[dict[str, object]] = field(default_factory=list)
    stickers: list[dict[str, str]] = field(default_factory=list)
    reactions: list[dict[str, object]] = field(default_factory=list)
    mentions: list[dict[str, str]] = field(default_factory=list)
    reference: dict[str, str] | None = None


@dataclass
class DCEChannel:
    """Parsed channel metadata."""

    id: str
    type: int
    name: str
    category_id: str = ""
    category: str = ""
    topic: str = ""


@dataclass
class DCEExport:
    """A single parsed DCE JSON export file."""

    guild_id: str
    guild_name: str
    channel: DCEChannel
    messages: list[DCEMessage] = field(default_factory=list)
    message_count: int = 0
    is_thread: bool = False
    parent_channel_name: str = ""
