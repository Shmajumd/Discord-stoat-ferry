"""Migration orchestrator — shared by CLI and GUI."""

from collections.abc import Callable
from typing import Any

from discord_ferry.config import FerryConfig
from discord_ferry.core.events import MigrationEvent


async def run_migration(
    config: FerryConfig,
    on_event: Callable[[MigrationEvent], Any],
) -> None:
    """Run the full 11-phase migration.

    Args:
        config: Migration configuration.
        on_event: Callback for progress events. GUI subscribes to update UI,
                  CLI subscribes to print Rich output.
    """
    # TODO: implement 11-phase migration
    raise NotImplementedError
