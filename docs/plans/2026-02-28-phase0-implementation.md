# Phase 0 — DCE Orchestration & Streaming Parser Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Ferry from a "DCE-to-Stoat Importer" into a "1-click Discord-to-Stoat Migrator" by embedding DCE binary management, subprocess orchestration, and streaming JSON parsing.

**Architecture:** Thin subprocess wrapper around DCE. Export runs as an inline pre-phase in `run_migration()` (same pattern as validate/report). Streaming parser uses `ijson` for messages, `json.loads` for metadata. Engine, GUI, and CLI all updated to support orchestrated and offline modes.

**Tech Stack:** Python 3.10+, asyncio subprocess, ijson, aiohttp (token validation + GitHub API), shutil (disk space)

**Design doc:** `docs/plans/2026-02-28-phase0-orchestration-design.md`

---

## Task 1: Add Export Exception Classes

**Files:**
- Modify: `src/discord_ferry/errors.py`
- Test: `tests/test_errors.py` (create if not exists)

**Step 1: Write the failing test**

Create `tests/test_errors.py`:

```python
"""Tests for custom exception hierarchy."""

from discord_ferry.errors import (
    DCENotFoundError,
    DiscordAuthError,
    DotNetMissingError,
    ExportError,
    FerryError,
    MigrationError,
)


def test_export_error_hierarchy():
    """ExportError inherits from MigrationError -> FerryError."""
    err = ExportError("test")
    assert isinstance(err, MigrationError)
    assert isinstance(err, FerryError)


def test_dce_not_found_is_export_error():
    assert isinstance(DCENotFoundError("msg"), ExportError)


def test_dotnet_missing_is_export_error():
    assert isinstance(DotNetMissingError("msg"), ExportError)


def test_discord_auth_is_export_error():
    assert isinstance(DiscordAuthError("msg"), ExportError)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_errors.py -v`
Expected: FAIL with `ImportError` (classes don't exist yet)

**Step 3: Write minimal implementation**

Add to the bottom of `src/discord_ferry/errors.py`:

```python
class ExportError(MigrationError):
    """Error during DCE export phase."""


class DCENotFoundError(ExportError):
    """DCE binary not found and download failed."""


class DotNetMissingError(ExportError):
    """Required .NET runtime not detected."""


class DiscordAuthError(ExportError):
    """Discord token validation failed."""
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_errors.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```
git add src/discord_ferry/errors.py tests/test_errors.py
git commit -m "feat: add export exception classes (ExportError, DCENotFoundError, DotNetMissingError, DiscordAuthError)"
```

---

## Task 2: Expand FerryConfig with Discord Credentials

**Files:**
- Modify: `src/discord_ferry/config.py`
- Test: `tests/test_config.py` (create or modify)

**Step 1: Write the failing test**

Create `tests/test_config.py`:

```python
"""Tests for FerryConfig dataclass."""

from pathlib import Path

from discord_ferry.config import FerryConfig


def test_default_discord_fields_are_none():
    """New Discord fields default to None."""
    cfg = FerryConfig(export_dir=Path("/tmp/test"), stoat_url="https://stoat.example", token="tok")
    assert cfg.discord_token is None
    assert cfg.discord_server_id is None
    assert cfg.skip_export is False


def test_discord_token_not_in_repr():
    """discord_token must be excluded from repr (security)."""
    cfg = FerryConfig(
        export_dir=Path("/tmp/test"),
        stoat_url="https://stoat.example",
        token="tok",
        discord_token="secret-discord-token",
    )
    assert "secret-discord-token" not in repr(cfg)


def test_orchestrated_mode_detection():
    """When discord_token and discord_server_id are set, skip_export remains False."""
    cfg = FerryConfig(
        export_dir=Path("/tmp/test"),
        stoat_url="https://stoat.example",
        token="tok",
        discord_token="dt",
        discord_server_id="123",
    )
    assert cfg.discord_token == "dt"
    assert cfg.discord_server_id == "123"
    assert cfg.skip_export is False


def test_offline_mode_detection():
    """When skip_export is True, we're in offline mode."""
    cfg = FerryConfig(
        export_dir=Path("/tmp/exports"),
        stoat_url="https://stoat.example",
        token="tok",
        skip_export=True,
    )
    assert cfg.skip_export is True
    assert cfg.discord_token is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `TypeError` (unexpected keyword arguments)

**Step 3: Write minimal implementation**

Add three new fields to `FerryConfig` in `src/discord_ferry/config.py`, after `max_emoji` and before the runtime-only fields:

```python
    # Discord credentials (orchestrated mode only — never persisted to disk)
    discord_token: str | None = field(default=None, repr=False)
    discord_server_id: str | None = None

    # Skip the export phase (auto-set when export_dir is user-provided in offline mode)
    skip_export: bool = False
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```
git add src/discord_ferry/config.py tests/test_config.py
git commit -m "feat: add discord_token, discord_server_id, skip_export to FerryConfig"
```

---

## Task 3: Add `export_completed` to MigrationState

**Files:**
- Modify: `src/discord_ferry/state.py`
- Test: `tests/test_state.py` (existing — add tests)

**Context:** `state.py` has manual `_state_to_dict` and `_dict_to_state` functions (lines 98-156). The new field must be added to the dataclass AND both serialization functions.

**Step 1: Write the failing tests**

Add to `tests/test_state.py`:

```python
def test_export_completed_default_false():
    """New states default export_completed to False."""
    state = MigrationState()
    assert state.export_completed is False


def test_export_completed_round_trip(tmp_path):
    """export_completed survives save/load cycle."""
    state = MigrationState()
    state.export_completed = True
    save_state(state, tmp_path)
    loaded = load_state(tmp_path)
    assert loaded.export_completed is True


def test_load_old_state_without_export_completed(tmp_path):
    """Loading a state.json from before this field was added defaults to False."""
    import json

    old_data = {"role_map": {}, "channel_map": {}}  # minimal old state
    (tmp_path / "state.json").write_text(json.dumps(old_data))
    loaded = load_state(tmp_path)
    assert loaded.export_completed is False
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_state.py -v -k "export_completed"`
Expected: FAIL with `TypeError` (unexpected keyword) or `AttributeError`

**Step 3: Write minimal implementation**

In `src/discord_ferry/state.py`:

1. Add field to `MigrationState` dataclass (after `is_dry_run`):
```python
    # Export phase tracking (for smart resume)
    export_completed: bool = False
```

2. Add to `_state_to_dict()` (after `"is_dry_run"` line):
```python
        "export_completed": state.export_completed,
```

3. Add to `_dict_to_state()` (after `is_dry_run` line):
```python
            export_completed=data.get("export_completed", False),
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_state.py -v -k "export_completed"`
Expected: PASS (3 tests)

**Step 5: Commit**

```
git add src/discord_ferry/state.py tests/test_state.py
git commit -m "feat: add export_completed field to MigrationState for smart resume"
```

---

## Task 4: Add `json_path` to DCEExport Model

**Files:**
- Modify: `src/discord_ferry/parser/models.py`
- Modify: `src/discord_ferry/parser/dce_parser.py`
- Test: `tests/test_parser.py` (existing — add test)

**Context:** `DCEExport` is at line 110 of `models.py`. The `json_path` field will be used by the streaming parser in Task 8 to know which file to stream messages from.

**Step 1: Write the failing test**

Add to `tests/test_parser.py`:

```python
def test_dce_export_has_json_path():
    """DCEExport includes json_path field for streaming parser."""
    from pathlib import Path
    from discord_ferry.parser.models import DCEExport, DCEChannel, DCEGuild

    export = DCEExport(
        guild=DCEGuild(id="1", name="Test"),
        channel=DCEChannel(id="2", type=0, name="general"),
        json_path=Path("/tmp/test.json"),
    )
    assert export.json_path == Path("/tmp/test.json")


def test_dce_export_json_path_defaults_to_none():
    """json_path defaults to None for backward compatibility."""
    from discord_ferry.parser.models import DCEExport, DCEChannel, DCEGuild

    export = DCEExport(
        guild=DCEGuild(id="1", name="Test"),
        channel=DCEChannel(id="2", type=0, name="general"),
    )
    assert export.json_path is None
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_parser.py -v -k "json_path"`
Expected: FAIL with `TypeError` (unexpected keyword)

**Step 3: Write minimal implementation**

In `src/discord_ferry/parser/models.py`:

1. Add `from pathlib import Path` to imports at top.

2. Add field to `DCEExport` (after `parent_channel_name`):
```python
    json_path: Path | None = None
```

**Step 4: Set json_path in parse_single_export**

In `src/discord_ferry/parser/dce_parser.py`, add `json_path=json_path` to the `DCEExport(...)` constructor at line 78:

```python
    return DCEExport(
        guild=guild,
        channel=channel,
        messages=messages,
        message_count=int(raw["messageCount"]),
        exported_at=str(raw.get("exportedAt", "")),
        is_thread=is_thread,
        parent_channel_name=parent_channel_name,
        json_path=json_path,
    )
```

**Step 5: Run tests**

Run: `uv run pytest tests/test_parser.py -v`
Expected: All existing tests PASS plus new json_path tests

**Step 6: Commit**

```
git add src/discord_ferry/parser/models.py src/discord_ferry/parser/dce_parser.py tests/test_parser.py
git commit -m "feat: add json_path field to DCEExport for streaming parser support"
```

---

## Task 5: Create Exporter Manager (DCE Binary Management)

**Files:**
- Create: `src/discord_ferry/exporter/__init__.py`
- Create: `src/discord_ferry/exporter/manager.py`
- Create: `tests/test_exporter_manager.py`

**Context:** This module downloads and manages the DCE binary. It queries the GitHub Releases API for a pinned version, detects the OS/arch, downloads the correct zip, extracts it to `~/.discord-ferry/bin/dce/{version}/`. On macOS/Linux, it checks for .NET 8 runtime.

**Step 1: Create the exporter package**

Create `src/discord_ferry/exporter/__init__.py`:

```python
"""DCE export orchestration — binary management and subprocess execution."""

from discord_ferry.exporter.manager import DCE_VERSION, detect_dotnet, download_dce, get_dce_path

__all__ = ["DCE_VERSION", "detect_dotnet", "download_dce", "get_dce_path"]
```

**Step 2: Write failing tests**

Create `tests/test_exporter_manager.py`:

```python
"""Tests for exporter binary manager."""

from __future__ import annotations

import platform
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from discord_ferry.exporter.manager import (
    DCE_VERSION,
    _get_asset_name,
    _get_dce_dir,
    detect_dotnet,
    get_dce_path,
)


def test_dce_version_is_pinned():
    assert DCE_VERSION == "2.46.1"


def test_get_dce_dir():
    """DCE binary directory is under ~/.discord-ferry/bin/dce/{version}/."""
    dce_dir = _get_dce_dir()
    assert dce_dir == Path.home() / ".discord-ferry" / "bin" / "dce" / DCE_VERSION


class TestGetAssetName:
    def test_windows_x64(self):
        with patch("platform.system", return_value="Windows"), patch(
            "platform.machine", return_value="AMD64"
        ):
            assert "win-x64" in _get_asset_name()

    def test_linux_x64(self):
        with patch("platform.system", return_value="Linux"), patch(
            "platform.machine", return_value="x86_64"
        ):
            assert "linux-x64" in _get_asset_name()

    def test_macos_arm64(self):
        with patch("platform.system", return_value="Darwin"), patch(
            "platform.machine", return_value="arm64"
        ):
            assert "osx-arm64" in _get_asset_name()

    def test_unsupported_os_raises(self):
        with patch("platform.system", return_value="FreeBSD"), pytest.raises(
            ValueError, match="Unsupported"
        ):
            _get_asset_name()


class TestDetectDotnet:
    def test_windows_always_true(self):
        """Windows uses self-contained DCE — .NET not required."""
        with patch("platform.system", return_value="Windows"):
            assert detect_dotnet() is True

    def test_linux_with_dotnet_8(self):
        """Returns True when dotnet --version reports 8.x."""
        import subprocess

        with patch("platform.system", return_value="Linux"), patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="8.0.100\n"),
        ):
            assert detect_dotnet() is True

    def test_linux_without_dotnet(self):
        """Returns False when dotnet command not found."""
        with patch("platform.system", return_value="Linux"), patch(
            "subprocess.run", side_effect=FileNotFoundError
        ):
            assert detect_dotnet() is False

    def test_linux_with_old_dotnet(self):
        """Returns False when dotnet version is < 8."""
        import subprocess

        with patch("platform.system", return_value="Linux"), patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout="6.0.400\n"),
        ):
            assert detect_dotnet() is False


class TestGetDcePath:
    def test_returns_path_when_binary_exists(self, tmp_path):
        """Returns path to DCE executable when it exists."""
        dce_dir = tmp_path / "dce"
        dce_dir.mkdir()
        exe = dce_dir / "DiscordChatExporter.Cli"
        exe.touch()
        exe.chmod(0o755)

        with patch("discord_ferry.exporter.manager._get_dce_dir", return_value=dce_dir):
            result = get_dce_path()
            assert result is not None
            assert result.exists()

    def test_returns_none_when_not_found(self, tmp_path):
        """Returns None when DCE directory doesn't exist."""
        with patch(
            "discord_ferry.exporter.manager._get_dce_dir", return_value=tmp_path / "nonexistent"
        ):
            result = get_dce_path()
            assert result is None
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_exporter_manager.py -v`
Expected: FAIL with `ImportError` (module doesn't exist yet)

**Step 4: Write implementation**

Create `src/discord_ferry/exporter/manager.py`:

```python
"""DCE binary download, verification, and platform detection."""

from __future__ import annotations

import io
import logging
import platform
import subprocess
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp

from discord_ferry.errors import DCENotFoundError

if TYPE_CHECKING:
    from discord_ferry.core.events import EventCallback

logger = logging.getLogger(__name__)

DCE_VERSION = "2.46.1"

# Map (system, machine) to DCE release asset suffix.
_PLATFORM_MAP: dict[tuple[str, str], str] = {
    ("Windows", "AMD64"): "win-x64",
    ("Windows", "x86"): "win-x64",
    ("Linux", "x86_64"): "linux-x64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Darwin", "x86_64"): "osx-x64",
    ("Darwin", "arm64"): "osx-arm64",
}

_GITHUB_RELEASE_URL = (
    "https://api.github.com/repos/Tyrrrz/DiscordChatExporter/releases/tags/v{version}"
)


def _get_dce_dir() -> Path:
    """Return the directory where DCE binary should be stored."""
    return Path.home() / ".discord-ferry" / "bin" / "dce" / DCE_VERSION


def _get_asset_name() -> str:
    """Return the DCE release asset name for the current platform."""
    system = platform.system()
    machine = platform.machine()
    suffix = _PLATFORM_MAP.get((system, machine))
    if suffix is None:
        raise ValueError(f"Unsupported platform: {system} {machine}")
    return f"DiscordChatExporter.Cli.{suffix}.zip"


def detect_dotnet() -> bool:
    """Check if .NET 8+ runtime is available. Always True on Windows (self-contained)."""
    if platform.system() == "Windows":
        return True
    try:
        result = subprocess.run(
            ["dotnet", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False
        version_str = result.stdout.strip()
        major = int(version_str.split(".")[0])
        return major >= 8
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return False


def get_dce_path() -> Path | None:
    """Return path to DCE executable if it exists, else None."""
    dce_dir = _get_dce_dir()
    if not dce_dir.exists():
        return None

    if platform.system() == "Windows":
        exe = dce_dir / "DiscordChatExporter.Cli.exe"
    else:
        exe = dce_dir / "DiscordChatExporter.Cli"

    return exe if exe.exists() else None


async def download_dce(on_event: EventCallback) -> Path:
    """Download the pinned DCE release from GitHub and extract it.

    Args:
        on_event: Callback for progress events.

    Returns:
        Path to the DCE executable.

    Raises:
        DCENotFoundError: If download or extraction fails.
    """
    from discord_ferry.core.events import MigrationEvent

    asset_name = _get_asset_name()
    release_url = _GITHUB_RELEASE_URL.format(version=DCE_VERSION)
    dce_dir = _get_dce_dir()

    on_event(
        MigrationEvent(
            phase="export",
            status="progress",
            message=f"Downloading DiscordChatExporter v{DCE_VERSION}...",
        )
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                release_url, headers={"Accept": "application/vnd.github.v3+json"}
            ) as resp:
                if resp.status != 200:
                    raise DCENotFoundError(
                        f"GitHub API returned {resp.status} for DCE v{DCE_VERSION}"
                    )
                release_data = await resp.json()

            download_url: str | None = None
            for asset in release_data.get("assets", []):
                if asset["name"] == asset_name:
                    download_url = asset["browser_download_url"]
                    break

            if download_url is None:
                raise DCENotFoundError(
                    f"Asset {asset_name} not found in DCE v{DCE_VERSION} release"
                )

            async with session.get(download_url) as resp:
                if resp.status != 200:
                    raise DCENotFoundError(f"Failed to download {asset_name}: HTTP {resp.status}")
                data = await resp.read()

    except aiohttp.ClientError as e:
        raise DCENotFoundError(f"Network error downloading DCE: {e}") from e

    dce_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(dce_dir)
    except zipfile.BadZipFile as e:
        raise DCENotFoundError(f"Downloaded file is not a valid zip: {e}") from e

    exe_path = get_dce_path()
    if exe_path is None:
        raise DCENotFoundError(f"Extraction succeeded but executable not found in {dce_dir}")

    if platform.system() != "Windows":
        exe_path.chmod(0o755)

    on_event(
        MigrationEvent(
            phase="export",
            status="progress",
            message=f"DiscordChatExporter v{DCE_VERSION} ready.",
        )
    )

    return exe_path
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_exporter_manager.py -v`
Expected: PASS (all tests)

**Step 6: Run full verification**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest`
Expected: All pass

**Step 7: Commit**

```
git add src/discord_ferry/exporter/__init__.py src/discord_ferry/exporter/manager.py tests/test_exporter_manager.py
git commit -m "feat: add exporter/manager.py — DCE binary download, platform detection, .NET check"
```

---

## Task 6: Create Exporter Runner (DCE Subprocess Execution)

**Files:**
- Create: `src/discord_ferry/exporter/runner.py`
- Create: `tests/test_exporter_runner.py`
- Create: `tests/fixtures/dce_stdout_sample.txt`
- Modify: `src/discord_ferry/exporter/__init__.py` (add exports)

**Context:** The runner launches DCE as an async subprocess, parses its stdout for progress, emits MigrationEvents, and supports cancellation via config.cancel_event.

**Step 1: Create DCE stdout fixture**

Create `tests/fixtures/dce_stdout_sample.txt`:

```text
Starting export of guild 123456789...
[1/15] Exporting #general...
[1/15] Exporting #general... 25.0%
[1/15] Exporting #general... 50.0%
[1/15] Exporting #general... 100.0%
[2/15] Exporting #announcements...
[2/15] Exporting #announcements... 100.0%
[3/15] Exporting #memes...
[3/15] Exporting #memes... 33.3%
[3/15] Exporting #memes... 66.7%
[3/15] Exporting #memes... 100.0%
Export complete.
```

**Step 2: Write failing tests**

Create `tests/test_exporter_runner.py`:

```python
"""Tests for exporter subprocess runner."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from discord_ferry.config import FerryConfig
from discord_ferry.core.events import MigrationEvent
from discord_ferry.exporter.runner import (
    _DCE_PROGRESS_RE,
    _build_dce_command,
    _check_disk_space,
    validate_discord_token,
)


class TestProgressRegex:
    def test_channel_with_percentage(self):
        line = "[1/15] Exporting #general... 50.0%"
        match = _DCE_PROGRESS_RE.search(line)
        assert match is not None
        assert match.group("channel") == "general"
        assert match.group("pct") == "50.0"

    def test_channel_start_no_percentage(self):
        line = "[2/15] Exporting #announcements..."
        match = _DCE_PROGRESS_RE.search(line)
        assert match is not None
        assert match.group("channel") == "announcements"
        assert match.group("pct") is None

    def test_no_match_for_other_lines(self):
        line = "Starting export of guild 123..."
        assert _DCE_PROGRESS_RE.search(line) is None


class TestBuildCommand:
    def test_command_construction(self, tmp_path):
        dce_path = tmp_path / "dce"
        cfg = FerryConfig(
            export_dir=tmp_path / "exports",
            stoat_url="https://stoat.example",
            token="st",
            discord_token="dt",
            discord_server_id="12345",
        )
        cmd = _build_dce_command(cfg, dce_path)
        assert cmd[0] == str(dce_path)
        assert "exportguild" in cmd
        assert "--token" in cmd
        assert "dt" in cmd
        assert "-g" in cmd
        assert "12345" in cmd
        assert "--media" in cmd
        assert "--markdown" in cmd
        assert "false" in cmd
        assert "--format" in cmd
        assert "Json" in cmd
        assert "--include-threads" in cmd
        assert "All" in cmd
        assert "--reuse-media" in cmd


class TestDiskSpaceCheck:
    def test_warns_when_low(self, tmp_path):
        events: list[MigrationEvent] = []
        on_event = events.append

        with patch("shutil.disk_usage") as mock_du:
            mock_du.return_value = MagicMock(free=1_000_000_000)  # 1 GB
            _check_disk_space(tmp_path, on_event)

        assert len(events) == 1
        assert "Low disk space" in events[0].message

    def test_no_warning_when_plenty(self, tmp_path):
        events: list[MigrationEvent] = []
        on_event = events.append

        with patch("shutil.disk_usage") as mock_du:
            mock_du.return_value = MagicMock(free=20_000_000_000)  # 20 GB
            _check_disk_space(tmp_path, on_event)

        assert len(events) == 0


class TestValidateDiscordToken:
    @pytest.mark.asyncio
    async def test_valid_token(self, aioresponses):
        aioresponses.get(
            "https://discord.com/api/v10/users/@me", status=200, payload={"id": "1"}
        )
        await validate_discord_token("valid-token")  # should not raise

    @pytest.mark.asyncio
    async def test_invalid_token(self, aioresponses):
        from discord_ferry.errors import DiscordAuthError

        aioresponses.get("https://discord.com/api/v10/users/@me", status=401)
        with pytest.raises(DiscordAuthError, match="Invalid Discord token"):
            await validate_discord_token("bad-token")
```

Note: Check `conftest.py` for the `aioresponses` fixture. If not present, add it.

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_exporter_runner.py -v`
Expected: FAIL with `ImportError` (module doesn't exist yet)

**Step 4: Write implementation**

Create `src/discord_ferry/exporter/runner.py`:

```python
"""Async subprocess execution for DiscordChatExporter."""

from __future__ import annotations

import asyncio
import logging
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp

from discord_ferry.core.events import MigrationEvent
from discord_ferry.errors import DiscordAuthError, ExportError

if TYPE_CHECKING:
    from discord_ferry.config import FerryConfig
    from discord_ferry.core.events import EventCallback

logger = logging.getLogger(__name__)

# Regex to parse DCE stdout progress lines.
# Matches: "[1/15] Exporting #general... 50.0%" or "[1/15] Exporting #general..."
_DCE_PROGRESS_RE = re.compile(
    r"\[\d+/\d+\] Exporting #(?P<channel>[^\s.]+)\.{3}\s*(?:(?P<pct>[\d.]+)%)?"
)

_DISK_WARN_BYTES = 5_000_000_000  # 5 GB


def _build_dce_command(config: FerryConfig, dce_path: Path) -> list[str]:
    """Build the DCE CLI command list."""
    return [
        str(dce_path),
        "exportguild",
        "--token",
        config.discord_token or "",
        "-g",
        config.discord_server_id or "",
        "--media",
        "--reuse-media",
        "--markdown",
        "false",
        "--format",
        "Json",
        "--include-threads",
        "All",
        "--output",
        str(config.export_dir),
    ]


def _check_disk_space(export_dir: Path, on_event: EventCallback) -> None:
    """Emit a warning event if disk space is low."""
    try:
        export_dir.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(export_dir)
        if usage.free < _DISK_WARN_BYTES:
            free_gb = usage.free / 1_000_000_000
            on_event(
                MigrationEvent(
                    phase="export",
                    status="warning",
                    message=(
                        f"Low disk space ({free_gb:.1f} GB free). "
                        f"Large servers may need 5-10 GB for exports."
                    ),
                )
            )
    except OSError:
        pass  # Can't check disk space — not critical


async def validate_discord_token(token: str) -> None:
    """Validate a Discord user token via the /users/@me endpoint.

    Raises:
        DiscordAuthError: If the token is invalid (401).
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": token},
        ) as resp:
            if resp.status == 401:
                raise DiscordAuthError(
                    "Invalid Discord token. Check that you copied it correctly."
                )
            if resp.status != 200:
                raise DiscordAuthError(
                    f"Discord API returned unexpected status {resp.status}"
                )


async def run_dce_export(
    config: FerryConfig,
    dce_path: Path,
    on_event: EventCallback,
) -> Path:
    """Run DCE as an async subprocess and stream progress.

    Args:
        config: Ferry configuration with discord_token and discord_server_id.
        dce_path: Path to the DCE executable.
        on_event: Callback for progress events.

    Returns:
        Path to the export directory containing JSON files.

    Raises:
        ExportError: If DCE exits with a non-zero code.
        asyncio.CancelledError: If cancelled via config.cancel_event.
    """
    _check_disk_space(config.export_dir, on_event)

    cmd = _build_dce_command(config, dce_path)
    config.export_dir.mkdir(parents=True, exist_ok=True)

    on_event(
        MigrationEvent(
            phase="export",
            status="started",
            message="Starting Discord export...",
        )
    )

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stderr_lines: list[str] = []

    try:
        assert process.stdout is not None
        assert process.stderr is not None

        async def _read_stderr() -> None:
            assert process.stderr is not None
            async for raw_line in process.stderr:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line:
                    stderr_lines.append(line)

        stderr_task = asyncio.create_task(_read_stderr())

        async for raw_line in process.stdout:
            if config.cancel_event and config.cancel_event.is_set():
                process.terminate()
                await process.wait()
                raise asyncio.CancelledError("Export cancelled by user")

            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue

            logger.debug("DCE: %s", line)

            match = _DCE_PROGRESS_RE.search(line)
            if match:
                channel = match.group("channel")
                pct_str = match.group("pct")
                pct = int(float(pct_str)) if pct_str else 0
                on_event(
                    MigrationEvent(
                        phase="export",
                        status="progress",
                        message=f"Exporting #{channel}...",
                        channel_name=channel,
                        current=pct,
                        total=100,
                    )
                )

        await stderr_task
        await process.wait()

    except asyncio.CancelledError:
        process.terminate()
        await process.wait()
        raise

    if process.returncode != 0:
        last_err = stderr_lines[-1] if stderr_lines else "Unknown error"
        raise ExportError(
            f"DCE export failed (exit code {process.returncode}): {last_err}"
        )

    on_event(
        MigrationEvent(
            phase="export",
            status="completed",
            message="Discord export complete.",
        )
    )

    return config.export_dir
```

**Step 5: Update `__init__.py`**

Update `src/discord_ferry/exporter/__init__.py` to export runner functions:

```python
"""DCE export orchestration — binary management and subprocess execution."""

from discord_ferry.exporter.manager import DCE_VERSION, detect_dotnet, download_dce, get_dce_path
from discord_ferry.exporter.runner import run_dce_export, validate_discord_token

__all__ = [
    "DCE_VERSION",
    "detect_dotnet",
    "download_dce",
    "get_dce_path",
    "run_dce_export",
    "validate_discord_token",
]
```

**Step 6: Run tests**

Run: `uv run pytest tests/test_exporter_runner.py -v`
Expected: PASS

**Step 7: Run full verification**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest`
Expected: All pass

**Step 8: Commit**

```
git add src/discord_ferry/exporter/ tests/test_exporter_runner.py tests/fixtures/dce_stdout_sample.txt
git commit -m "feat: add exporter/runner.py — async DCE subprocess, progress parsing, token validation"
```

---

## Task 7: Wire Export Phase into Engine

**Files:**
- Modify: `src/discord_ferry/core/engine.py`
- Test: `tests/test_engine.py` (existing — add tests)

**Context:** The engine at `core/engine.py` runs `run_migration()`. We add the export pre-phase inline, following the same pattern as validate (line 99-122) and report (line 136-142).

Key integration points:
- Line 31-43: `PHASE_ORDER` — add `"export"` at index 0
- Line 99-122: Validate runs inline — export goes before this
- Line 125: `runnable_phases = PHASE_ORDER[1:-1]` — must adjust for new phase
- Lines 175-187: Resume skip logic uses `PHASE_ORDER.index()` — adding "export" shifts indices

**Step 1: Write failing tests**

Add to `tests/test_engine.py`:

```python
@pytest.mark.asyncio
async def test_export_phase_in_phase_order():
    """PHASE_ORDER starts with 'export'."""
    from discord_ferry.core.engine import PHASE_ORDER
    assert PHASE_ORDER[0] == "export"


@pytest.mark.asyncio
async def test_export_skipped_in_offline_mode(tmp_path):
    """When skip_export is True, the export phase is skipped."""
    fixture = tmp_path / "test.json"
    fixture.write_text(
        '{"guild":{"id":"1","name":"G"},"channel":{"id":"2","type":0,"name":"c"},'
        '"messages":[],"messageCount":0}'
    )

    events: list = []
    config = FerryConfig(
        export_dir=tmp_path,
        stoat_url="https://stoat.example",
        token="tok",
        skip_export=True,
        dry_run=True,
        output_dir=tmp_path / "out",
    )

    from discord_ferry.core.engine import run_migration
    state = await run_migration(config, events.append)

    export_events = [e for e in events if e.phase == "export"]
    assert any(e.status == "skipped" for e in export_events)
```

**Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_engine.py -v -k "export"`
Expected: FAIL

**Step 3: Implement engine changes**

In `src/discord_ferry/core/engine.py`:

1. Add imports after existing imports:
```python
from discord_ferry.errors import DotNetMissingError
from discord_ferry.exporter import (
    detect_dotnet,
    download_dce,
    get_dce_path,
    run_dce_export,
    validate_discord_token,
)
```

2. Add `"export"` at index 0 of `PHASE_ORDER`:
```python
PHASE_ORDER: list[str] = [
    "export",    # Phase 0 — handled inline (DCE subprocess)
    "validate",  # Phase 1 — handled inline (parser)
    "connect",   # Phase 2
    ...
]
```

3. Add `"export"` to `_SKIPPABLE`:
```python
_SKIPPABLE: dict[str, str] = {
    "export": "skip_export",
    "emoji": "skip_emoji",
    ...
}
```

4. In `run_migration()`, insert export phase before validate:
```python
    # Phase 0: EXPORT — run DCE subprocess inline (orchestrated mode)
    if not config.skip_export:
        on_event(MigrationEvent(phase="export", status="started", message="Starting export..."))
        await validate_discord_token(config.discord_token or "")
        dce_path = get_dce_path()
        if dce_path is None:
            dce_path = await download_dce(on_event)
        if not detect_dotnet():
            raise DotNetMissingError(
                "DCE requires .NET 8 runtime. "
                "Install from https://dotnet.microsoft.com/download/dotnet/8.0"
            )
        await run_dce_export(config, dce_path, on_event)
        state.export_completed = True
        save_state(state, config.output_dir)
        on_event(MigrationEvent(phase="export", status="completed", message="Export complete."))
    else:
        on_event(
            MigrationEvent(phase="export", status="skipped", message="Using existing exports")
        )
```

5. Update `runnable_phases` to exclude export, validate, and report:
```python
    runnable_phases = [p for p in PHASE_ORDER if p not in ("export", "validate", "report")]
```

**Step 4: Run tests**

Run: `uv run pytest tests/test_engine.py -v`
Expected: PASS (including new export tests)

**Step 5: Run full verification**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest`
Expected: All pass

**Step 6: Commit**

```
git add src/discord_ferry/core/engine.py tests/test_engine.py
git commit -m "feat: wire export phase into engine — Phase 0 runs before validate"
```

---

## Task 8: Add Streaming Parser with ijson

**Files:**
- Modify: `pyproject.toml` (add ijson dependency)
- Modify: `src/discord_ferry/parser/dce_parser.py`
- Modify: `src/discord_ferry/migrator/messages.py`
- Test: `tests/test_parser.py` (add streaming tests)

**Context:** Currently `parse_single_export()` at `dce_parser.py:63` does `json.loads(json_path.read_text())` loading all messages into memory. We add a `stream_messages()` generator that uses `ijson`.

Key lines in `messages.py`:
- Line 84: `for msg_obj in export.messages` (dry run)
- Line 188: `sorted_messages = sorted(export.messages, key=...)` (live run)

**Step 1: Add ijson dependency**

In `pyproject.toml`, add `"ijson>=3.0"` to dependencies (keep sorted):

```toml
dependencies = [
    "aiohttp>=3.9",
    "click>=8.0",
    "ijson>=3.0",
    "nicegui>=2.0",
    "python-dotenv",
    "rich>=13.0",
]
```

Run: `uv sync` to install ijson.

**Step 2: Write failing tests for stream_messages**

Add to `tests/test_parser.py`:

```python
def test_stream_messages_yields_all(tmp_path):
    """stream_messages yields each message from a DCE JSON file."""
    from discord_ferry.parser.dce_parser import stream_messages
    import json

    data = {
        "guild": {"id": "1", "name": "G"},
        "channel": {"id": "2", "type": 0, "name": "c"},
        "messages": [
            {"id": "100", "type": "Default", "timestamp": "2024-01-01T00:00:00+00:00",
             "content": "hello", "author": {"id": "10", "name": "User"}},
            {"id": "101", "type": "Default", "timestamp": "2024-01-01T00:01:00+00:00",
             "content": "world", "author": {"id": "10", "name": "User"}},
        ],
        "messageCount": 2,
    }
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps(data))

    msgs = list(stream_messages(json_path))
    assert len(msgs) == 2
    assert msgs[0].id == "100"
    assert msgs[0].content == "hello"
    assert msgs[1].id == "101"


def test_stream_messages_handles_empty(tmp_path):
    """stream_messages yields nothing for exports with no messages."""
    from discord_ferry.parser.dce_parser import stream_messages
    import json

    data = {
        "guild": {"id": "1", "name": "G"},
        "channel": {"id": "2", "type": 0, "name": "c"},
        "messages": [],
        "messageCount": 0,
    }
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps(data))

    msgs = list(stream_messages(json_path))
    assert len(msgs) == 0
```

**Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_parser.py -v -k "stream_messages"`
Expected: FAIL with `ImportError` (stream_messages doesn't exist)

**Step 4: Implement stream_messages**

In `src/discord_ferry/parser/dce_parser.py`:

1. Add imports:
```python
from collections.abc import Iterator
import ijson
```

2. Add the function after `parse_single_export`:
```python
def stream_messages(json_path: Path) -> Iterator[DCEMessage]:
    """Yield messages one at a time from a DCE JSON file using streaming JSON.

    This avoids loading all messages into memory at once.

    Args:
        json_path: Path to the DCE JSON export file.

    Yields:
        Parsed DCEMessage objects in file order.
    """
    with open(json_path, "rb") as f:
        for raw_msg in ijson.items(f, "messages.item"):
            yield _parse_message(raw_msg)
```

**Step 5: Run streaming tests**

Run: `uv run pytest tests/test_parser.py -v -k "stream_messages"`
Expected: PASS

**Step 6: Update messages.py to use streaming**

In `src/discord_ferry/migrator/messages.py`:

1. Add import:
```python
from discord_ferry.parser.dce_parser import stream_messages
```

2. In the live message loop (around line 187-191), replace:
```python
            sorted_messages = sorted(export.messages, key=lambda m: m.timestamp)
            total = len(sorted_messages)

            for idx, msg in enumerate(sorted_messages):
```
With:
```python
            if export.json_path is not None:
                message_source = stream_messages(export.json_path)
            else:
                message_source = iter(sorted(export.messages, key=lambda m: m.timestamp))
            total = export.message_count

            for idx, msg in enumerate(message_source):
```

3. Similarly update the dry-run loop (line 82-84):
```python
            if export.json_path is not None:
                dry_source = stream_messages(export.json_path)
            else:
                dry_source = iter(export.messages)
            for msg_obj in dry_source:
```

**Step 7: Run full test suite**

Run: `uv run pytest -v`
Expected: All pass

**Step 8: Run full verification**

Run: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest`
Expected: All pass

**Step 9: Commit**

```
git add pyproject.toml src/discord_ferry/parser/dce_parser.py src/discord_ferry/migrator/messages.py tests/test_parser.py
git commit -m "feat: add streaming JSON parser with ijson — flat memory for large exports"
```

---

## Task 9: Update Validate Phase for Metadata-Only Parsing

**Files:**
- Modify: `src/discord_ferry/parser/dce_parser.py`
- Modify: `src/discord_ferry/core/engine.py`
- Test: `tests/test_parser.py` (add tests)

**Context:** Currently `parse_single_export()` loads all messages into memory during validate. We add a `metadata_only` parameter to skip message loading. The validate phase and author_names building in engine.py must be updated.

**Step 1: Write failing test**

Add to `tests/test_parser.py`:

```python
def test_parse_single_export_metadata_only(tmp_path):
    """metadata_only=True returns DCEExport with empty messages list."""
    from discord_ferry.parser.dce_parser import parse_single_export
    import json

    data = {
        "guild": {"id": "1", "name": "G"},
        "channel": {"id": "2", "type": 0, "name": "c"},
        "messages": [
            {"id": "100", "type": "Default", "timestamp": "2024-01-01T00:00:00+00:00",
             "content": "hello", "author": {"id": "10", "name": "User"}},
        ],
        "messageCount": 1,
    }
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps(data))

    export = parse_single_export(json_path, metadata_only=True)
    assert export.message_count == 1
    assert len(export.messages) == 0
    assert export.json_path == json_path
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_parser.py -v -k "metadata_only"`
Expected: FAIL (parameter doesn't exist)

**Step 3: Implement metadata_only mode**

In `src/discord_ferry/parser/dce_parser.py`:

1. Update `parse_single_export` signature:
```python
def parse_single_export(json_path: Path, *, metadata_only: bool = False) -> DCEExport:
```

2. Replace the message loading lines:
```python
    if metadata_only:
        messages = []
    else:
        messages = [_parse_message(m) for m in raw["messages"]]
        messages.sort(key=lambda m: m.timestamp)
```

3. Update `parse_export_directory` to accept and pass through:
```python
def parse_export_directory(export_dir: Path, *, metadata_only: bool = False) -> list[DCEExport]:
```
And:
```python
            export = parse_single_export(json_path, metadata_only=metadata_only)
```

**Step 4: Update engine.py to use metadata_only**

In `engine.py`, change validate call to `metadata_only=True`:
```python
    exports = parse_export_directory(config.export_dir, metadata_only=True)
```

Update the `author_names` building to stream instead of using `export.messages`:
```python
    for export in exports:
        if export.json_path is not None:
            for msg in stream_messages(export.json_path):
                author = msg.author
                if author.id not in state.author_names:
                    state.author_names[author.id] = author.nickname or author.name
        else:
            for msg in export.messages:
                author = msg.author
                if author.id not in state.author_names:
                    state.author_names[author.id] = author.nickname or author.name
```

Add the import: `from discord_ferry.parser.dce_parser import stream_messages`

Update `validate_export()` to handle empty message lists by streaming when json_path is available.

**Step 5: Run tests**

Run: `uv run pytest -v`
Expected: All pass

**Step 6: Commit**

```
git add src/discord_ferry/parser/dce_parser.py src/discord_ferry/core/engine.py tests/test_parser.py
git commit -m "feat: add metadata_only parsing mode — validate without loading all messages"
```

---

## Task 10: Update CLI for Orchestrated Mode

**Files:**
- Modify: `src/discord_ferry/cli.py`
- Test: `tests/test_cli.py` (existing — add tests)

**Context:** Currently `cli.py` has `export_dir` as a positional argument. Change to optional `--export-dir` flag and add `--discord-token` and `--discord-server` options. Read the full `cli.py` during implementation to understand the exact argument structure.

**Step 1: Write failing tests**

Add to `tests/test_cli.py` — tests for the new argument structure, mutual exclusion, and mode detection.

**Step 2: Implement CLI changes**

Key changes:
1. Replace positional `EXPORT_DIR` with optional `--export-dir` flag
2. Add `--discord-token` and `--discord-server` options
3. Add mutual exclusion validation
4. Compute `export_dir` from `discord_server_id` when in orchestrated mode
5. Set `skip_export` on FerryConfig

**Step 3: Run tests and verify**

Run: `uv run pytest tests/test_cli.py -v`

**Step 4: Commit**

```
git add src/discord_ferry/cli.py tests/test_cli.py
git commit -m "feat: update CLI for orchestrated mode — --discord-token, --discord-server, --export-dir"
```

---

## Task 11: Update GUI for Orchestrated Mode

**Files:**
- Modify: `src/discord_ferry/gui.py`
- Test: `tests/test_gui.py` (existing — add/update tests)

**Context:** The GUI needs mode selection, Discord credential inputs, ToS disclaimer, and export progress screen. This is the largest single task. Read the full `gui.py` during implementation.

Key changes:
1. Mode selection (orchestrated vs offline toggle)
2. Discord token + server ID inputs (masked, with help modal)
3. ToS disclaimer checkbox
4. Export progress screen between setup and validate
5. Smart resume dialog

**This task should be split into sub-steps during implementation.** Read the full gui.py first.

**Step 1: Read and understand current gui.py structure**
**Step 2: Add mode toggle to setup screen**
**Step 3: Add Discord credential inputs**
**Step 4: Add export progress screen**
**Step 5: Wire up smart resume**
**Step 6: Test screen flow**
**Step 7: Commit**

```
git add src/discord_ferry/gui.py tests/test_gui.py
git commit -m "feat: update GUI for orchestrated mode — Discord creds, export progress, smart resume"
```

---

## Task 12: Update Documentation

**Files:**
- Modify: `docs/` (multiple files)

**Context:** Rewrite user guide to show orchestrated flow as primary path with offline as secondary. Do this after all code tasks are complete.

**Step 1: Update getting started guide**
**Step 2: Update CLI reference**
**Step 3: Add FAQ entries**
**Step 4: Update architecture docs**
**Step 5: Commit**

```
git add docs/
git commit -m "content: rewrite docs for 1-click orchestrated migration flow"
```

---

## Task 13: Final Verification and Version Bump

**Files:**
- Modify: `src/discord_ferry/__init__.py` (version bump)
- Modify: `pyproject.toml` (version bump)

**Step 1: Run full verification**

```
uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest
```

Expected: All pass with ~350+ tests.

**Step 2: Version bump**

Minor version bump (new feature): `1.1.0` -> `1.2.0`. Update both `src/discord_ferry/__init__.py` and `pyproject.toml`.

**Step 3: Commit via /ship skill**

Use the `/ship` skill for the final commit.

---

## Summary

| Task | Description | Est. New Tests |
|------|-------------|----------------|
| 1 | Export exception classes | 4 |
| 2 | FerryConfig Discord fields | 4 |
| 3 | MigrationState export_completed | 3 |
| 4 | DCEExport json_path field | 2 |
| 5 | Exporter manager (binary mgmt) | 8 |
| 6 | Exporter runner (subprocess) | 10 |
| 7 | Engine export integration | 2 |
| 8 | Streaming parser (ijson) | 2 |
| 9 | Metadata-only parsing | 1 |
| 10 | CLI orchestrated mode | 3 |
| 11 | GUI orchestrated mode | 4 |
| 12 | Documentation rewrite | 0 |
| 13 | Final verification + bump | 0 |
| **Total** | | **~43 new tests** |
