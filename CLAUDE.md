# FFMPEG MCP Server - Intelligent Video Processing

An MCP server for AI-guided FFmpeg video processing: scene detection, beat-synchronized music videos, speech analysis, and multi-agent orchestration.

## Quick Start

```bash
# Start the MCP server
uv run python -m src.server

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m src.server

# Run tests
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

## Project Structure

```
src/                    # Python source code (MCP server, processors, analyzers)
tests/                  # Test suite (ci/, dev/, docker/, data/, files/)
docs/                   # All documentation
  guides/               # Setup guides, specs, workflows
  ai-generated/         # AI-written docs (organized by topic)
  architecture/         # Architecture planning docs
  external-research/    # Research from external sources
  archive/              # Historical docs
scripts/                # Utility and test scripts
tools/                  # Analysis and debugging tools
examples/               # Komposition examples, effect templates, video workflows
docker/                 # Dockerfile variants
deployment/             # Deploy configs (docker-compose, build scripts)
config/                 # Configuration files
presets/                # Effect presets (JSON)
integration/            # External integrations (Komposteur, etc.)
archive/                # Legacy test code
.claude/skills/         # Agent skills (core-philosophy, video-processing, ci-debugging, multi-agent)
```

## Key Source Files

| File | Purpose |
|------|---------|
| `src/server.py` | Main MCP server with all tool definitions |
| `src/ffmpeg_wrapper.py` | Safe FFmpeg command building |
| `src/content_analyzer.py` | AI-powered scene detection |
| `src/komposition_processor.py` | Beat-synchronized video processing |
| `src/speech_detector.py` | Silero VAD speech detection |
| `src/video_comparison_tool.py` | A/B video comparison |
| `src/format_manager.py` | Aspect ratio and format management |

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

- `mcp` - MCP protocol (FastMCP)
- `pydantic` - Data validation
- `pytest` + `pytest-asyncio` - Testing
