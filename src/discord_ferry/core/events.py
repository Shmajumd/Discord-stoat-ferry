"""Event emitter for migration progress reporting."""

from dataclasses import dataclass


@dataclass
class MigrationEvent:
    """Progress event emitted by the migration engine."""

    phase: str
    status: str  # "started", "progress", "completed", "error", "warning"
    message: str
    current: int = 0
    total: int = 0
    channel_name: str = ""
    detail: dict[str, object] | None = None
