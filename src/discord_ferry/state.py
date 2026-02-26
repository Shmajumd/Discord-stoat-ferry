"""Migration state management and ID mapping."""

from dataclasses import dataclass, field


@dataclass
class MigrationState:
    """Tracks all ID mappings and progress for resume support."""

    # Discord ID -> Stoat ID mappings
    role_map: dict[str, str] = field(default_factory=dict)
    channel_map: dict[str, str] = field(default_factory=dict)
    category_map: dict[str, str] = field(default_factory=dict)
    message_map: dict[str, str] = field(default_factory=dict)
    emoji_map: dict[str, str] = field(default_factory=dict)

    # Author ID -> uploaded Autumn avatar ID
    avatar_cache: dict[str, str] = field(default_factory=dict)

    # Autumn upload cache: local_path -> autumn_file_id
    upload_cache: dict[str, str] = field(default_factory=dict)

    # Pending pins: list of (stoat_channel_id, stoat_message_id)
    pending_pins: list[tuple[str, str]] = field(default_factory=list)

    # Pending reactions
    pending_reactions: list[dict[str, object]] = field(default_factory=list)

    # Error and warning logs
    errors: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)

    # Stoat server ID
    stoat_server_id: str = ""

    # Resume tracking
    current_phase: str = ""
    last_completed_channel: str = ""
    last_completed_message: str = ""
