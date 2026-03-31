# FFMPEG MCP Server - Intelligent Video Processing

An MCP server for AI-guided FFmpeg video processing: scene detection, beat-synchronized music videos, speech analysis, and multi-agent orchestration.

## Quick Start

```bash
# Start the MCP server
uv run python -m src.server

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m src.server

# Run CI tests
uv run pytest tests/ci/ -x -q

# Run all tests (excluding integration/docker)
uv run pytest tests/ -v -s
```

## Project Rules

- **Discuss before implementing**: Changes >10 LOC require discussion first
- **YOLO prefix**: When prefixed with "YOLO", implement directly without discussion
- **Minimal comments**: Only on function definitions when needed
- **Senior developer context**: Deep technical knowledge assumed
- **Concise responses**: Minimize token usage, answer directly
- **Never pollute root**: AI-generated files go in `docs/ai-generated/`
- **External LLM research**: For research-heavy tasks, create info-documents for external LLM consumption

## KCP Discovery Chain

This project uses Knowledge Context Protocol for AI discoverability:

```
knowledge.yaml          # KCP manifest: units, intents, triggers
CLAUDE.md               # Project instructions (you are here)
.claude/skills/         # Executable skills for agent sessions
.claude/agents/         # Subagent definitions (FastTrack, Build Detective, etc.)
.claude/subagents/      # Subagent implementations
```

Load order: `knowledge.yaml` -> `CLAUDE.md` -> relevant skills (on trigger match)

## Model Delegation Strategy

| Model | Use For | Examples |
|-------|---------|---------|
| **Haiku** | File reads, status checks, simple operations | `list_files`, `get_file_info`, cost checks |
| **Sonnet** | Multi-file changes, tool module edits, test fixes | Editing tool modules, fixing imports |
| **Opus** | Architecture decisions, ambiguous requirements | Refactoring server structure, new tool design |

Default to the cheapest model that can handle the task. The project's own HaikuSubagent uses this pattern for video analysis ($0.02-0.10/analysis with daily limits).

## Session Resilience

- **Resumption**: Check `git log --oneline -5` and `git diff --stat` to understand session state
- **Test verification**: Always run `uv run pytest tests/ci/ -x -q` before committing
- **Partial work**: If interrupted mid-refactor, check `src/tools/__init__.py` for module registration consistency
- **Known flaky**: `tests/ci/test_ci_working.py::test_typescript_mcp_compilation` (depends on TypeScript MCP that may not be present)

## Project Structure

```
src/                    # Python source code
  server.py             # Thin orchestrator: init components, delegate to tools/
  server_deps.py        # ServerDeps namedtuple + timing_decorator
  tools/                # Modular MCP tool registration (13 modules)
    __init__.py          # register_all() iterates ALL_MODULES
    file_management.py   # list_files, process_file, batch_process, etc.
    komposition.py       # Beat-synchronized music video processing
    komposition_generation.py  # Description-to-video pipeline
    composition.py       # Speech-aware composition planning
    speech.py            # Speech detection (Silero VAD)
    video_effects.py     # Visual effects and chains
    audio_effects.py     # Audio processing and mastering
    format_management.py # Aspect ratio and format conversion
    video_comparison.py  # A/B video comparison
    download_youtube.py  # YouTube download/upload/Shorts
    haiku_integration.py # AI-powered video strategy
    process_monitoring.py # Timeout and zombie process management
    prompts.py           # MCP prompt definitions
  config.py             # SecurityConfig: paths, limits, extensions
  file_manager.py       # File registry and ID system
  ffmpeg_wrapper.py     # Safe FFmpeg command building
  content_analyzer.py   # AI-powered scene detection
  komposition_processor.py  # Beat-synchronized processing
  speech_detector.py    # Silero VAD speech detection
  format_manager.py     # Aspect ratio and format management
  haiku_subagent.py     # Claude Haiku for video analysis
  timeout_manager.py    # Operation timeout management
tests/                  # Test suite
  ci/                   # CI-safe tests (no external deps)
  dev/                  # Developer tests (may need services)
  docker/               # Docker-specific tests
  data/                 # Test fixtures
  files/                # Test media files
docs/                   # All documentation
  guides/               # Setup guides, specs, workflows
  ai-generated/         # AI-written docs (organized by topic)
  architecture/         # Architecture planning docs
scripts/                # Utility and test scripts
tools/                  # Analysis and debugging tools
examples/               # Komposition examples, effect templates
docker/                 # Dockerfile variants
deployment/             # Deploy configs (docker-compose, build scripts)
config/                 # Configuration files
presets/                # Effect presets (JSON)
integration/            # External integrations (Komposteur, etc.)
.claude/skills/         # Agent skills
.claude/agents/         # Subagent role definitions
.claude/subagents/      # Subagent implementations
```

## Architecture: Modular Tool Pattern

The server follows a clean delegation pattern:

```
server.py (orchestrator)
  -> initializes all components (FileManager, FFMPEGWrapper, etc.)
  -> bundles into ServerDeps namedtuple
  -> calls register_all(mcp, deps) from tools/__init__.py
     -> each tool module: register(mcp, deps) using @mcp.tool()
```

**Adding a new tool module:**
1. Create `src/tools/my_tool.py` with `def register(mcp, deps):`
2. Add to imports and `ALL_MODULES` list in `src/tools/__init__.py`
3. Use `deps.component_name` to access shared components
4. Apply `@timing_decorator` for operation logging

## Safety Protocols

- **API Key handling**: `ANTHROPIC_API_KEY` from env, with `HaikuSubagent.client is None` fallback
- **Cost controls**: `CostLimits(daily_limit=5.0, per_analysis_limit=0.10)` enforced by HaikuSubagent
- **File security**: Extension whitelist, 500MB size limit, sandboxed directories
- **Process safety**: Timeout manager with cleanup callbacks, zombie process detection
- **Optional imports**: Heavy deps wrapped in `try/except ImportError` for CI compatibility

## MCP Configuration

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/Users/stiglau/utvikling/privat/yolo-ffmpeg-mcp"
    }
  }
}
```

## Dependencies (UV managed)

- `mcp` / `fastmcp` - MCP protocol
- `pydantic` - Data validation
- `anthropic` - Claude Haiku subagent
- `opencv-python` / `scenedetect` - Video analysis
- `pytest` + `pytest-asyncio` - Testing
- `aiohttp` - Async HTTP
- `docker` - Container management (optional)
