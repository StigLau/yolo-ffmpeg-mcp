# MCP Server Configuration Guide for Claude Desktop

## Essential Configuration Requirements

After extensive troubleshooting, the following configuration is **essential** for the FFMPEG MCP server to work correctly with Claude Desktop:

### Claude Desktop Configuration File
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.venv/bin/python",
      "args": ["-m", "src.server"],
      "cwd": "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp",
      "env": {
        "PYTHONPATH": "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp"
      }
    }
  }
}
```

## Critical Configuration Elements

### 1. **Full Python Path Required**
- ❌ `"command": "uv"` - Does not work
- ❌ `"command": "python"` - Does not work  
- ✅ `"command": "/path/to/.venv/bin/python"` - **Required**

The full path to the virtual environment Python executable is essential.

### 2. **PYTHONPATH Environment Variable**
```json
"env": {
  "PYTHONPATH": "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp"
}
```

This is **critical** for Python to find the `src` module. Without this, you get:
```
ModuleNotFoundError: No module named 'src'
```

### 3. **Working Directory (cwd)**
```json
"cwd": "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp"
```

Must be set to the project root directory.

### 4. **Module Import Format**
```json
"args": ["-m", "src.server"]
```

Use module import format, not direct file path.

## Common Configuration Mistakes

### ❌ Using UV Command
```json
{
  "command": "uv",
  "args": ["run", "python", "-m", "src.server"]
}
```
**Issue**: Claude Desktop cannot properly invoke `uv run` commands.

### ❌ Missing PYTHONPATH
```json
{
  "command": "/path/to/python",
  "args": ["-m", "src.server"],
  "cwd": "/path/to/project"
}
```
**Issue**: Python cannot find the `src` module without PYTHONPATH.

### ❌ Direct File Path
```json
{
  "args": ["src/server.py"]
}
```
**Issue**: Relative imports in `server.py` fail without module context.

## Verification Steps

### 1. Check Log Files
Monitor these files for startup errors:
- `/Users/stiglau/Library/Logs/Claude/mcp.log`
- `/Users/stiglau/Library/Logs/Claude/mcp-server-ffmpeg-mcp.log`

### 2. Manual Server Test
```bash
cd /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp
PYTHONPATH=/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp \
  .venv/bin/python -m src.server
```

### 3. Expected Log Output
When working correctly, you should see:
```
[info] [ffmpeg-mcp] Initializing server...
[info] [ffmpeg-mcp] Server started and connected successfully
```

Without errors about missing modules or file paths.

## Troubleshooting

### Common Error Messages

1. **`ModuleNotFoundError: No module named 'src'`**
   - Solution: Add PYTHONPATH environment variable

2. **`can't open file '//src/server.py'`**
   - Solution: Use full Python path, not `uv` command

3. **`Server transport closed unexpectedly`**
   - Solution: Check that all dependencies are installed in venv

### Debug Commands
```bash
# Check Python path
/path/to/.venv/bin/python -c "import sys; print(sys.path)"

# Test module import
PYTHONPATH=/path/to/project /path/to/.venv/bin/python -c "import src.server"

# Verify virtual environment
ls -la /path/to/.venv/bin/python
```

## Architecture Notes

The server uses FastMCP with relative imports:
```python
from .file_manager import FileManager
from .ffmpeg_wrapper import FFMPEGWrapper
# etc.
```

This requires:
1. Module-style execution (`-m src.server`)
2. PYTHONPATH pointing to project root
3. Proper virtual environment with all dependencies

## Testing Configuration

Use the provided `test_mcp_configuration.py` script to verify setup:
```bash
python test_mcp_configuration.py
```

This will test server startup, tool discovery, and basic connectivity.