---
name: testing
description: Test infrastructure, CI patterns, and pytest configuration for yolo-ffmpeg-mcp
allowed-tools: Read, Grep, Glob, Bash
---

## When to Use This

- Running or writing tests
- Debugging CI failures
- Adding test coverage for new tool modules
- Understanding test organization

## Quick Start

### Run CI tests (safe, no external deps)
```bash
uv run pytest tests/ci/ -x -q
```

### Run all tests (may need services)
```bash
uv run pytest tests/ -v -s
```

### Run specific test file
```bash
uv run pytest tests/ci/test_unit_core.py -x -q
```

## Test Organization

| Directory | Purpose | CI Safe? |
|-----------|---------|----------|
| `tests/ci/` | Core unit tests, no external deps | Yes |
| `tests/dev/` | Developer tests, may need FFmpeg/APIs | No |
| `tests/docker/` | Container-specific tests | No |
| `tests/integration/` | Full integration tests | No |
| `tests/data/`, `tests/files/` | Test fixtures and media | N/A |

## Writing Tests for Tool Modules

Each `src/tools/*.py` module should have corresponding CI tests:

```python
# tests/ci/test_my_tool.py
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_deps():
    deps = MagicMock()
    deps.file_manager = MagicMock()
    deps.ffmpeg = MagicMock()
    return deps

@pytest.mark.asyncio
async def test_my_tool_function(mock_deps):
    # Test tool registration and basic behavior
    pass
```

## Known Flaky Tests

- `test_typescript_mcp_compilation` — depends on TypeScript MCP presence
- Tests importing `docker` — optional dependency, may skip

## pytest Configuration

- Config in `pyproject.toml` and `pytest.ini`
- Skips: archive, komposteur, registry, llm-validation directories
- Markers: `asyncio` for async tests

## Related Skills

- ci-debugging, core-philosophy
