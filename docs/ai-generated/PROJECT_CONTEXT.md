# FFMPEG MCP Server - Project Context

**Updated**: 2026-03-30 (post-modular restructure)

## Architecture Overview

The server was restructured from a monolithic `server.py` (7248 lines) into a modular
architecture with 13 tool modules, each registered independently.

### Core Components
- **Server** (`src/server.py`) - Thin orchestrator: init components, delegate to tools/
- **ServerDeps** (`src/server_deps.py`) - Namedtuple bundling all shared components
- **Tool Modules** (`src/tools/`) - 13 modules, each with `register(mcp, deps)`
- **FileManager** (`src/file_manager.py`) - Secure file handling with ID-based references
- **FFMPEGWrapper** (`src/ffmpeg_wrapper.py`) - Safe FFMPEG command building and execution
- **SecurityConfig** (`src/config.py`) - Security settings and validation

### Registration Flow
```
server.py (orchestrator)
  -> initializes all components (FileManager, FFMPEGWrapper, etc.)
  -> bundles into ServerDeps namedtuple
  -> calls register_all(mcp, deps) from tools/__init__.py
     -> each tool module: register(mcp, deps) using @mcp.tool()
     -> failures are isolated per-module (logged, not fatal)
```

### Tool Modules (`src/tools/`)
| Module | Purpose |
|--------|---------|
| `file_management.py` | list_files, process_file, batch_process |
| `komposition.py` | Beat-synchronized music video processing |
| `komposition_generation.py` | Description-to-video pipeline |
| `composition.py` | Speech-aware composition planning |
| `speech.py` | Speech detection (Silero VAD) |
| `video_effects.py` | Visual effects and chains |
| `audio_effects.py` | Audio processing and mastering |
| `format_management.py` | Aspect ratio and format conversion |
| `video_comparison.py` | A/B video comparison |
| `download_youtube.py` | YouTube download/upload/Shorts |
| `haiku_integration.py` | AI-powered video strategy |
| `process_monitoring.py` | Timeout and zombie process management |
| `prompts.py` | MCP prompt definitions |

## Working Directories
- **Source files**: `/tmp/music/source/`
- **Temp files**: `/tmp/music/temp/`
- **Screenshots**: `/tmp/music/screenshots/{sourceRef}/`
- **Metadata**: `/tmp/music/metadata/`

## Dependencies (UV managed)
- `mcp` / `fastmcp` - MCP protocol
- `pydantic` - Data validation
- `anthropic` - Claude Haiku subagent
- `opencv-python` / `scenedetect` - Video analysis
- `pytest` + `pytest-asyncio` - Testing
- `aiohttp` - Async HTTP
- `docker` - Container management (optional)

## Key Commands
```bash
# Start MCP server
uv run python -m src.server

# Test with Inspector
npx @modelcontextprotocol/inspector uv run python -m src.server

# Run CI tests
uv run pytest tests/ci/ -x -q

# Run all tests
uv run pytest tests/ -v -s
```

## Security Implementation
- File access restricted to allowed directories only
- All file references use secure IDs (format: `file_12345678`)
- Input validation for extensions, file sizes (500MB limit), operations
- Process timeout protection with cleanup callbacks
- Optional imports: heavy deps wrapped in `try/except ImportError`
- API key handling: `ANTHROPIC_API_KEY` from env, with fallback mode
- Cost controls: `CostLimits(daily_limit=5.0, per_analysis_limit=0.10)`