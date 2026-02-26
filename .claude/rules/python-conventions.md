---
globs:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Python Conventions

## Language Version

Target Python 3.10+. Use modern features:
- `match`/`case` statements where appropriate
- `X | Y` union type syntax (not `Union[X, Y]`)
- `dataclasses` with `field(default_factory=...)` for mutable defaults
- `from __future__ import annotations` only if needed for forward refs

## Async-First

All API and I/O code uses `async`/`await`. The migration engine is fully async. Use:
- `aiohttp` for HTTP requests (Autumn uploads)
- `aiofiles` for file I/O where beneficial
- `asyncio.sleep()` for rate limit delays

## Type Hints

- All public function signatures must have type hints
- Use `pathlib.Path` for all file paths (not `os.path` or raw strings)
- Prefer `str | None` over `Optional[str]`
- Use `dict[str, str]` not `Dict[str, str]` (lowercase generics, Python 3.10+)

## Code Style

- **ruff** for linting and formatting (line-length 100)
- **mypy strict** for type checking
- **Google-style docstrings** on public functions only
- No docstrings on private/internal functions unless logic is non-obvious
- No comments that restate what the code does

## Data Models

Use `@dataclass` for all data models (as specified in the brief):
- `FerryConfig` in `config.py`
- `MigrationState` in `state.py`
- `MigrationEvent` in `core/events.py`
- Parser models in `parser/models.py`

## Error Handling

- Custom exceptions defined in `errors.py`
- Never use bare `except:` — always catch specific exceptions
- Use `except Exception as e:` only at top-level error boundaries
- Log errors to `MigrationState.errors` with phase, context, and message

## Testing

- pytest + pytest-asyncio for async tests
- Test fixtures (sample DCE JSON) in `tests/fixtures/`
- Use `aioresponses` for mocking HTTP calls
- Test file naming: `test_{module}.py`
- Focus on pure logic modules first: parser, transforms, state

## Imports

Standard library first, then third-party, then local. Ruff enforces this.

```python
import asyncio
from pathlib import Path

import aiohttp
import stoat

from discord_ferry.config import FerryConfig
from discord_ferry.core.events import MigrationEvent
```
