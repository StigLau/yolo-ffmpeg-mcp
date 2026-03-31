---
name: core-philosophy
description: Over-engineering prevention and consultation rules. Activated when making code changes, debugging CI, or proposing architectural modifications.
allowed-tools: Read, Grep, Glob, Bash
---

# Core Philosophy: Simplicity First

## When to Use

- Making any code change (check against principles)
- Debugging CI or runtime issues
- Proposing architectural modifications
- Reviewing PRs or evaluating approach complexity
- Any fix that seems to grow beyond 10 lines

## The Central Principle

**Simpler is usually correct.** If the root cause is likely <10 lines, spend MORE time analyzing than implementing.

## Mandatory Consultation Rules

**NEVER** change base images, package managers, or core dependencies without explicit permission:
- Tech stack changes (Alpine->Debian, pip->UV, Python versions) require approval
- Always present options: "Fix Alpine deps vs switch to Debian - which?"
- Wait for permission before implementing
- If fix requires >10 lines, PAUSE and reconsider

## Over-Engineering Detection

### Warning Signs (STOP and reassess)
- Same error persisting after 2+ attempts with different approaches
- "Simple" fix requiring tech stack or architectural changes
- Each fix creates more problems than it solves
- 50+ line fix for a single error message
- Adding a new dependency to fix an existing feature

### Good Multi-Fix Pattern
- Each fix reveals a NEW, SPECIFIC error (progress)
- Targeted changes addressing actual underlying issues
- No architectural rewrites -- just corrected specific mismatches

## Root Cause Analysis Protocol

```
1. Ask: "Is this treating a symptom or the root cause?"
2. Compare CI environment vs local environment EXACTLY
3. Check: Does main branch have this issue?
4. Look for the SIMPLEST explanation first
5. If fix requires >10 lines, PAUSE and reconsider
```

## The Optional Import Pattern
```python
# Heavy dependencies that may not be available in all environments
try:
    import docker
    import cv2
    import scenedetect
except ImportError:
    docker = None  # Server starts without docker support
    cv2 = None     # Video analysis degrades gracefully
```

## Modular Registration with Error Isolation
```python
# src/tools/__init__.py -- one broken module won't crash the server
def register_all(mcp, deps):
    for module in ALL_MODULES:
        try:
            module.register(mcp, deps)
            registered.append(module.__name__)
        except Exception as e:
            logger.error("Failed to register %s: %s", module.__name__, e)
```

## Key File Paths

- Server entry: `src/server.py` (thin orchestrator)
- Dependencies bundle: `src/server_deps.py` (ServerDeps namedtuple)
- Tool registration: `src/tools/__init__.py` (register_all with isolation)
- Security config: `src/config.py` (SecurityConfig)

## Key Gotchas

- This project is exploratory/research; Komposteur is production-ready
- The server was split from a 7248-line monolith into 13 modules -- old references to `server.py` containing tools are stale
- `from server import app` is the OLD pattern; now use `from src.tools import ...` or `from src.server import ...`
- Always run `uv run pytest tests/ci/ -x -q` before committing changes
