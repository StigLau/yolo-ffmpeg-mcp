---
name: ci-debugging
description: CI/CD debugging and Build Detective analysis patterns. Activated when investigating CI failures, Docker build issues, or test pipeline problems.
allowed-tools: Read, Grep, Glob, Bash
---

# CI Debugging Patterns

## When to Use

- CI pipeline fails (GitHub Actions, local pytest)
- Docker build errors or container startup failures
- Tests pass locally but fail in CI
- Import errors or missing dependency issues
- Flaky or intermittent test failures

## First Response Protocol

1. **Read the actual error** -- not the symptom, the root cause line
2. **Compare environments**: CI vs local EXACTLY (`python --version`, `uv sync` state)
3. **Check main branch**: Does it have this issue? (`git stash && git checkout main && uv run pytest tests/ci/ -x -q`)
4. **Simplest fix first**: Usually 1-3 lines

## Build Detective Integration

- Run BD analysis BEFORE expensive LLM operations
- BD reports available via Build Detective subagent (`.claude/agents/build-detective.md`)
- High confidence (>8/10) = direct implementation
- Use BD confidence scores to validate changes

## Common CI Pitfalls

### Import Errors (Most Common)
```python
# Pattern: Make heavy deps optional so CI tests don't require them
try:
    import docker
except ImportError:
    docker = None  # Graceful degradation in CI

# Pattern: Use src.module imports, not flat imports
# WRONG: from haiku_subagent import HaikuSubagent
# RIGHT: from src.haiku_subagent import HaikuSubagent
```

### Missing haiku-mcp-ts Directory
The TypeScript MCP sub-project was removed during restructure. Tests must skip:
```python
@pytest.mark.skipif(
    not Path('haiku-mcp-ts').exists(),
    reason="haiku-mcp-ts directory not present"
)
def test_typescript_feature(self):
    ...
```

### Path Issues
- CI uses different working directories than local dev
- Use `Path(__file__).parent` for test-relative paths
- Test fixtures: `tests/files/` (single location)
- Temp output: `/tmp/kompo/haiku-ffmpeg/ci-working/`

### pytest Return Value Warning
```python
# WRONG: test functions returning True triggers PytestReturnNotNoneWarning
def test_something():
    ...
    return True  # Don't do this

# RIGHT: use assertions, no return
def test_something():
    assert result is not None
```

### Docker Build Issues
- Check if base image has required system packages
- Verify COPY paths match actual file locations after restructure
- Layer caching: order Dockerfile commands by change frequency

## Anti-Pattern: The Whack-a-Mole Cycle

```
Real Issue: Missing try/except (3 lines)
  -> LLM Fix 1: Dockerfile changes
  -> LLM Fix 2: src/ restructuring
  -> LLM Fix 3: 301-line workflow replacement
  -> Real Fix: try/except ImportError (3 lines)
```

**90% of CI failures from LLM code changes are simple fixes.**

## Key File Paths

- CI tests: `tests/ci/` (safe, no external deps required)
- Test config: `pyproject.toml` (pytest section)
- GitHub Actions: `.github/workflows/`
- Tool registration: `src/tools/__init__.py` (register_all with error isolation)

## Key Gotchas

- `test_typescript_mcp_compilation` is a known flaky test -- always needs skip guard
- Tests using `subprocess.run(['python3', ...])` won't have uv-managed deps; use direct imports instead
- `analyze_video_files()` expects `List[Path]`, not `List[str]`
- Run `uv run pytest tests/ci/ -x -q` not `pytest` directly (needs uv environment)
