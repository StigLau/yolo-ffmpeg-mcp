# Haiku MCP Server Integration Guide

## Package Installation & Setup

### Method 1: Local Development (Recommended)

```bash
# In haiku-mcp-ts directory
bun install
bun run build
bun link

# In your consumer project
bun link @stiglau/komposteur-mcp-server
```

### Method 2: GitHub Packages

```bash
# Configure GitHub Packages access
echo "@stiglau:registry=https://npm.pkg.github.com" >> .npmrc
echo "//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}" >> .npmrc

# Install package
bun install @stiglau/komposteur-mcp-server
```

## HTTP Bridge Integration

### Simple HTTP Server Wrapper

```typescript
import { spawn } from 'child_process';
import express from 'express';

const app = express();
app.use(express.json());

// Generic MCP tool endpoint
app.post('/api/mcp/call-tool', async (req, res) => {
  const { tool, arguments: args } = req.body;

  // Spawn MCP server as subprocess
  const mcpServer = spawn('bun', ['run', '@stiglau/komposteur-mcp-server'], {
    stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY }
  });

  // Send MCP request
  const mcpRequest = {
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: { name: tool, arguments: args }
  };

  mcpServer.stdin.write(JSON.stringify(mcpRequest) + '\n');

  // Handle response
  mcpServer.stdout.on('data', (data) => {
    const response = JSON.parse(data.toString());
    res.json(response.result);
  });
});

// List available tools
app.get('/api/mcp/list-tools', async (req, res) => {
  // Similar pattern for tool discovery
});

app.listen(3001, () => {
  console.log('MCP HTTP Bridge running on port 3001');
});
```

## Available Tools

The MCP server provides 8 video processing tools:

1. **haiku_video_analysis** - AI-powered video analysis
2. **create_music_video** - Combine video + audio with crossfades
3. **download_youtube_video** - YouTube content acquisition
4. **add_file_to_registry** - File management
5. **get_file_info** - Metadata retrieval
6. **list_files** - Registry listing
7. **get_registry_status** - System status
8. **remove_file_from_registry** - Cleanup operations

### Example Tool Calls

```bash
# Video analysis
curl -X POST http://localhost:3001/api/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "haiku_video_analysis",
    "arguments": {
      "video_path": "/tmp/video.mp4",
      "analysis_type": "full"
    }
  }'

# Music video creation
curl -X POST http://localhost:3001/api/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_music_video",
    "arguments": {
      "video_file": "video_001",
      "audio_file": "audio_001",
      "output_file": "/tmp/output.mp4",
      "duration": 30
    }
  }'
```

## Configuration

### Required Environment Variables

```bash
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_google_key_here  # Optional fallback
```

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg yt-dlp

# macOS
brew install ffmpeg yt-dlp

# Verify installation
ffmpeg -version
yt-dlp --version
```

### YAML Configuration

Create `config/config.yaml`:

```yaml
server:
  name: "haiku-mcp-server"
  version: "1.0.0"

llm:
  primary: "anthropic"
  fallback: "google"
  timeout_seconds: 30
  max_retries: 3

models:
  anthropic:
    provider: "anthropic"
    model: "claude-3-haiku-20240307"
    api_key: "${ANTHROPIC_API_KEY}"
    max_tokens: 4096
  google:
    provider: "google"
    model: "gemini-1.5-flash"
    api_key: "${GEMINI_API_KEY}"
    max_tokens: 4096

ffmpeg:
  timeout_seconds: 300
  temp_directory: "/tmp/kompo/haiku-ffmpeg"
  cleanup_on_exit: true

youtube:
  timeout_seconds: 120
  max_duration_seconds: 600
  quality: "best[height<=720]"

logging:
  level: "INFO"
  include_ffmpeg_logs: false
  sanitize_responses: true

response_limits:
  max_tokens: 4000
  strip_metadata: true
  include_performance_stats: false
```

## Error Handling

### Common Issues

1. **Missing API Keys**: Set ANTHROPIC_API_KEY environment variable
2. **FFmpeg Not Found**: Install system dependencies
3. **Permission Errors**: Ensure temp directory is writable
4. **Transport Timeout**: Increase timeout_seconds in config

### Response Format

All tool responses follow this structure:

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\"success\": true, \"result\": {...}}"
    }
  ],
  "isError": false
}
```

Parse the `text` field as JSON for actual tool results.

## Performance Considerations

- **Startup Time**: ~2 seconds cold start
- **Memory Usage**: ~100MB baseline + video processing overhead
- **Concurrent Requests**: Spawn separate MCP processes for parallel processing
- **Cost Optimization**: Haiku model costs ~$0.02 per video analysis

## LLM Integration Tips

1. **Tool Discovery**: Always call `/api/mcp/list-tools` first
2. **File Management**: Use registry system for file ID references
3. **Error Handling**: Parse JSON responses and check `success` field
4. **Configuration**: Environment variables override YAML settings
5. **Debugging**: Enable logging.include_ffmpeg_logs for troubleshooting