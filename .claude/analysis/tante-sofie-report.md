# Tante Sofie — Adversarial Analysis: yolo-ffmpeg-mcp

**Date**: 2026-03-31
**Analyst**: Claude Opus 4.6 (automated SDD sweep)
**Branch**: cleanup/project-restructure → claude/sdd-improvements

## Context

Recent major refactor: server.py split from 7,248 lines to 127-line orchestrator + 13 tool modules. This analysis focuses on post-refactor quality and broader project health.

## CRITICAL — Bugs Fixed This Session

### 1. Duplicate `@timing_decorator` on `list_files`
- **Severity**: MEDIUM (double timing, potential performance logging noise)
- **Location**: `src/tools/file_management.py:23-24`
- **Fix**: Removed duplicate decorator ✅

### 2. Duplicate Dependencies in pyproject.toml
- **Severity**: LOW (UV handles dedup, but confuses humans)
- **Location**: `pyproject.toml` — `pytest` and `pytest-asyncio` listed twice
- **Fix**: Removed duplicates ✅

## HIGH — Post-Refactor Concerns

### 3. Module Registration Consistency
- **Risk**: If a tool module's `register()` function raises, it silently breaks all subsequent modules
- **Location**: `src/tools/__init__.py` — `register_all()` iterates `ALL_MODULES`
- **Recommendation**: Add try/except per module with logging, so one broken module doesn't take down the server

### 4. Shared Mutable State via ServerDeps
- **Risk**: `ServerDeps` is a namedtuple (immutable), but its contents (FileManager, etc.) are mutable objects shared across all tool modules
- **Concern**: No synchronization for concurrent MCP requests
- **Recommendation**: Audit for thread safety if MCP server handles concurrent requests

### 5. Stale Documentation References
- **Risk**: Several docs reference the old monolithic `server.py` with 7,248 lines
- **Locations**: `docs/ai-generated/`, `docs/architecture/`
- **Recommendation**: Grep for "server.py" references that assume monolithic structure and update

## MEDIUM — Security

### 6. API Key in Environment
- **Status**: Acceptable pattern (env var, not hardcoded)
- **Concern**: No key rotation mechanism, no expiry checking
- **Mitigation**: Fallback mode works without key — good design

### 7. Cost Controls
- **Status**: Good — `CostLimits(daily_limit=5.0, per_analysis_limit=0.10)`
- **Concern**: Daily limit resets on server restart (in-memory tracking)
- **Recommendation**: Consider persistent cost tracking for production use

### 8. File Extension Whitelist
- **Status**: Good — SecurityConfig enforces extension whitelist
- **Concern**: 500MB limit is generous for MCP context
- **Recommendation**: Review if limit should be lower for non-video operations

## MEDIUM — Architecture

### 9. 13 Tool Modules — Cohesion Check
- `komposition.py` vs `komposition_generation.py` vs `composition.py` — naming is confusing
  - `komposition.py`: Beat-synchronized processing
  - `komposition_generation.py`: Description-to-video pipeline
  - `composition.py`: Speech-aware composition planning
- **Recommendation**: Consider renaming for clarity (e.g., `beat_sync.py`, `video_generation.py`, `speech_composition.py`)

### 10. Heavy Optional Dependencies
- `opencv-python`, `scenedetect`, `docker`, `google-generativeai` — all heavy
- Good: wrapped in `try/except ImportError`
- **Concern**: Dependency installation failures are silent
- **Recommendation**: Add health-check tool that reports which optional deps are available

## LOW — Code Quality

### 11. Prompts Module Size
- `src/tools/prompts.py` contains ~40KB of prompt content
- Mixes MCP prompt registration with large inline text
- **Recommendation**: Move prompt content to separate files, load at registration time

### 12. Test Coverage Gaps
- 77 test files but coverage unknown (no coverage tool configured)
- New tool modules from refactor may have inconsistent test coverage
- **Recommendation**: Add `pytest-cov` and establish baseline

### 13. Archive/Experimental Debt
- `archive/`, `experimental/` directories contain significant dead code
- `experimental/haiku-mcp-ts/`, `experimental/typescript-mcp/` — abandoned experiments
- **Recommendation**: Tag and prune after confirming no reusable patterns

## Recommendations (Priority Order)

1. **Add error isolation** in `register_all()` — prevent one module from breaking all
2. **Rename confusing tool modules** (komposition vs composition vs komposition_generation)
3. **Update stale docs** referencing monolithic server.py
4. **Add `pytest-cov`** for coverage visibility
5. **Add dependency health-check tool** reporting available optional deps
6. **Externalize prompts** from prompts.py into loadable files
7. **Prune archive/experimental** after inventory
