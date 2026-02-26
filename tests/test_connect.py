"""Tests for the CONNECT phase (Phase 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from aioresponses import aioresponses

from discord_ferry.config import FerryConfig
from discord_ferry.errors import ConnectionError as FerryConnectionError
from discord_ferry.migrator.connect import run_connect
from discord_ferry.state import MigrationState

if TYPE_CHECKING:
    from pathlib import Path

    from discord_ferry.core.events import MigrationEvent
    from discord_ferry.parser.models import DCEExport

STOAT_URL = "https://api.test"
AUTUMN_URL = "https://autumn.test"
TOKEN = "test-token"

_API_ROOT_RESPONSE = {
    "stoat": "0.8.5",
    "features": {
        "autumn": {
            "enabled": True,
            "url": AUTUMN_URL,
        },
    },
}


def _make_config(tmp_path: Path) -> FerryConfig:
    return FerryConfig(
        export_dir=tmp_path,
        stoat_url=STOAT_URL,
        token=TOKEN,
        output_dir=tmp_path,
    )


async def test_run_connect_discovers_autumn_url(tmp_path: Path) -> None:
    """CONNECT phase discovers Autumn URL and stores it in state."""
    events: list[MigrationEvent] = []
    config = _make_config(tmp_path)
    state = MigrationState()
    exports: list[DCEExport] = []

    with aioresponses() as m:
        m.get(f"{STOAT_URL}/", payload=_API_ROOT_RESPONSE)
        m.get(f"{STOAT_URL}/users/@me", payload={"_id": "user123", "username": "ferry"})

        await run_connect(config, state, exports, events.append)

    assert state.autumn_url == AUTUMN_URL


async def test_run_connect_emits_events(tmp_path: Path) -> None:
    """CONNECT phase emits progress events."""
    events: list[MigrationEvent] = []
    config = _make_config(tmp_path)
    state = MigrationState()

    with aioresponses() as m:
        m.get(f"{STOAT_URL}/", payload=_API_ROOT_RESPONSE)
        m.get(f"{STOAT_URL}/users/@me", payload={"_id": "user123", "username": "ferry"})

        await run_connect(config, state, [], events.append)

    messages = [e.message for e in events]
    assert any("Connecting" in msg for msg in messages)
    assert any("Autumn URL" in msg for msg in messages)
    assert any("Authentication verified" in msg for msg in messages)


async def test_run_connect_invalid_token(tmp_path: Path) -> None:
    """CONNECT phase raises ConnectionError on 401."""
    config = _make_config(tmp_path)
    state = MigrationState()

    with aioresponses() as m:
        m.get(f"{STOAT_URL}/", payload=_API_ROOT_RESPONSE)
        m.get(f"{STOAT_URL}/users/@me", status=401)

        with pytest.raises(FerryConnectionError, match="invalid or expired token"):
            await run_connect(config, state, [], lambda e: None)


async def test_run_connect_unreachable(tmp_path: Path) -> None:
    """CONNECT phase raises ConnectionError when API is unreachable."""
    import aiohttp

    config = _make_config(tmp_path)
    state = MigrationState()

    with aioresponses() as m:
        m.get(f"{STOAT_URL}/", exception=aiohttp.ClientConnectionError("Connection refused"))

        with pytest.raises(FerryConnectionError, match="Cannot reach"):
            await run_connect(config, state, [], lambda e: None)


async def test_run_connect_missing_autumn_feature(tmp_path: Path) -> None:
    """CONNECT phase raises ConnectionError when response lacks Autumn URL."""
    config = _make_config(tmp_path)
    state = MigrationState()

    with aioresponses() as m:
        m.get(f"{STOAT_URL}/", payload={"stoat": "0.8.5", "features": {}})

        with pytest.raises(FerryConnectionError, match="missing Autumn URL"):
            await run_connect(config, state, [], lambda e: None)


async def test_run_connect_api_error_status(tmp_path: Path) -> None:
    """CONNECT phase raises ConnectionError on non-200 API root response."""
    config = _make_config(tmp_path)
    state = MigrationState()

    with aioresponses() as m:
        m.get(f"{STOAT_URL}/", status=500)

        with pytest.raises(FerryConnectionError, match="status 500"):
            await run_connect(config, state, [], lambda e: None)
