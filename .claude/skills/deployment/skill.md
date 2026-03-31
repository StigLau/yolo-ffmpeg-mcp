---
name: deployment
description: Docker deployment and MCP server configuration for yolo-ffmpeg-mcp
allowed-tools: Read, Grep, Glob, Bash
---

## When to Use This

- Deploying the MCP server
- Building Docker images
- Configuring MCP client connections
- Troubleshooting server startup

## Quick Start

### Local (development)
```bash
uv run python -m src.server
```

### MCP Inspector (testing)
```bash
npx @modelcontextprotocol/inspector uv run python -m src.server
```

### Docker
```bash
cd docker/ffmpeg-runner
docker build -t ffmpeg-mcp .
docker run -p 8080:8080 ffmpeg-mcp
```

## MCP Client Configuration

Add to Claude Desktop or any MCP client's config:

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/path/to/yolo-ffmpeg-mcp"
    }
  }
}
```

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `ANTHROPIC_API_KEY` | No | None | Haiku subagent (fallback mode without) |
| `HAIKU_DEBUG` | No | true | Debug logging for subagent |
| `ANALYTICS_ENABLED` | No | true | Firebase analytics toggle |

## Docker Variants

- `docker/ffmpeg-runner/` — FFmpeg execution environment
- `deployment/docker-compose.yml` — Full stack deployment

## Troubleshooting

- **Import errors**: Check `uv sync` ran successfully
- **Missing FFmpeg**: Install via `brew install ffmpeg` or use Docker
- **API key issues**: Server works without key (fallback mode), but Haiku analysis disabled

## Related Skills

- testing, core-philosophy
