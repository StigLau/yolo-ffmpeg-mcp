# FFMPEG MCP Server - Project Structure Guide

**Updated**: 2026-03-30 (post-modular restructure)

This document provides a comprehensive overview of the project structure after the
split from a monolithic `server.py` (7248 lines) into 13 modular tool files.

## Core System (`src/`)

### MCP Server (Modular Architecture)
- **`server.py`** - Thin orchestrator: initializes components, delegates to `tools/`
- **`server_deps.py`** - `ServerDeps` namedtuple bundling all shared components
- **`tools/__init__.py`** - `register_all()` iterates `ALL_MODULES` with per-module error isolation
- **`tools/file_management.py`** - list_files, process_file, batch_process, etc.
- **`tools/komposition.py`** - Beat-synchronized music video processing
- **`tools/komposition_generation.py`** - Description-to-video pipeline
- **`tools/composition.py`** - Speech-aware composition planning
- **`tools/speech.py`** - Speech detection (Silero VAD)
- **`tools/video_effects.py`** - Visual effects and chains
- **`tools/audio_effects.py`** - Audio processing and mastering
- **`tools/format_management.py`** - Aspect ratio and format conversion
- **`tools/video_comparison.py`** - A/B video comparison
- **`tools/download_youtube.py`** - YouTube download/upload/Shorts
- **`tools/haiku_integration.py`** - AI-powered video strategy
- **`tools/process_monitoring.py`** - Timeout and zombie process management
- **`tools/prompts.py`** - MCP prompt definitions

### Shared Components
- **`file_manager.py`** - Secure file ID mapping and validation
- **`config.py`** - `SecurityConfig`: paths, limits, extensions
- **`ffmpeg_wrapper.py`** - Safe FFMPEG command building and execution
- **`content_analyzer.py`** - AI-powered video content analysis
- **`komposition_processor.py`** - Beat-synchronized processing
- **`speech_detector.py`** - Silero VAD speech detection
- **`format_manager.py`** - Aspect ratio and format management
- **`haiku_subagent.py`** - Claude Haiku for video analysis
- **`timeout_manager.py`** - Operation timeout management
- **`models.py`** - `FileInfo`, `ProcessResult` Pydantic models

## Testing Infrastructure (`tests/`)

| Directory | Purpose | CI Safe? |
|-----------|---------|----------|
| `tests/ci/` | Core unit tests, no external deps | Yes |
| `tests/dev/` | Developer tests, may need FFmpeg/APIs | No |
| `tests/docker/` | Container-specific tests | No |
| `tests/data/`, `tests/files/` | Test fixtures and media | N/A |

### Key CI Tests
- `test_unit_core.py` - Core component unit tests
- `test_ci_working.py` - Server functionality (direct imports)
- `test_mcp_server_verification.py` - Tool module structure verification
- `test_integration_basic.py` - Basic integration tests
- `test_workflow_minimal.py` - Minimal workflow validation

## Documentation (`docs/`)

- **`docs/guides/`** - Setup guides, specs, workflows
- **`docs/ai-generated/`** - AI-written docs (organized by topic)
- **`docs/architecture/`** - Architecture planning docs
- **`docs/reports/`** - Analysis reports

## KCP Discovery Chain

```
knowledge.yaml          # KCP manifest: units, intents, triggers
CLAUDE.md               # Project instructions
.claude/skills/         # Executable skills for agent sessions
.claude/agents/         # Subagent definitions
.claude/subagents/      # Subagent implementations
```

## Deployment

- **`docker/`** - Dockerfile variants
- **`deployment/`** - Deploy configs (docker-compose, build scripts)
- **`config/`** - Configuration files

## LLM Navigation Guide

**Adding a new tool**: Create `src/tools/my_tool.py` with `def register(mcp, deps):`, add to `src/tools/__init__.py`

**Core Video Processing**: `src/ffmpeg_wrapper.py`, `src/content_analyzer.py`

**Music Video Creation**: `src/tools/komposition.py`, `src/tools/komposition_generation.py`

**Speech Detection**: `src/tools/speech.py`, `src/speech_detector.py`

**Testing**: `tests/ci/` -- run with `uv run pytest tests/ci/ -x -q`

**Examples**: `examples/komposition-examples/`, `examples/video-workflows/`