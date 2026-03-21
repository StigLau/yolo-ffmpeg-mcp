# FFMPEG MCP Server Implementation Specification

## Quick Start Instructions for Claude Code

### Initial Setup
```bash

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize Python project with uv
uv init
uv venv  # Creates .venv automatically
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Add dependencies using uv
uv add mcp fastmcp pydantic
# Note: asyncio is part of Python standard library
```

### Project Structure
```
ffmpeg-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py           # Main MCP server implementation
│   ├── ffmpeg_wrapper.py   # FFMPEG command builder and executor
│   ├── file_manager.py     # File mapping and security layer
│   ├── validators.py       # Input validation utilities
│   └── config.py          # Configuration management
├── tests/
│   ├── test_server.py
│   ├── test_ffmpeg.py
│   └── test_security.py
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Development environment
├── pyproject.toml        # Project configuration (uv managed)
├── uv.lock              # Lock file for reproducible builds
├── .python-version      # Python version specification
└── README.md            # Documentation
```

## Core Implementation Requirements

### 1. File Management System
```python
# file_manager.py
class FileManager:
    def __init__(self):
        self.file_map = {}  # {id: actual_path}
        self.source_dir = Path("/tmp/music/source")
        self.temp_dir = Path("/tmp/music/temp")
        
    def register_file(self, file_path: str) -> str:
        """Register a file and return its ID reference"""
        # Generate unique ID (e.g., "file_123456")
        # Validate file exists and is in allowed directory
        # Add to mapping
        
    def resolve_id(self, file_id: str) -> Optional[Path]:
        """Convert ID reference to actual path"""
        # Validate ID exists
        # Return actual path
        
    def create_temp_file(self, extension: str) -> tuple[str, Path]:
        """Create temporary file and return (id, path)"""
        # Generate unique temp file
        # Register in mapping
        # Return ID and path
```

### 2. FFMPEG Command Builder
```python
# ffmpeg_wrapper.py
class FFMPEGWrapper:
    ALLOWED_OPERATIONS = {
        "convert": ["-c:v", "libx264", "-c:a", "aac"],
        "extract_audio": ["-vn", "-acodec", "copy"],
        "trim": ["-ss", "{start}", "-t", "{duration}"],
        "resize": ["-vf", "scale={width}:{height}"],
        "normalize_audio": ["-af", "loudnorm"]
    }
    
    def build_command(self, operation: str, input_path: Path, 
                     output_path: Path, **params) -> List[str]:
        """Build safe FFMPEG command"""
        # Validate operation is allowed
        # Build command with proper escaping
        # Return command array for subprocess
```

### 3. Main MCP Server
```python
# server.py
from mcp.server.fastmcp import FastMCP
import os

# Initialize with configuration
mcp = FastMCP("ffmpeg-mcp")
file_manager = FileManager()
ffmpeg = FFMPEGWrapper()

# Environment variable for FFMPEG location
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "/usr/bin/ffmpeg")

@mcp.tool()
async def list_files() -> dict:
    """List available source files"""
    files = []
    for file in file_manager.source_dir.glob("*.mp3"):
        file_id = file_manager.register_file(file)
        files.append({"id": file_id, "name": file.name})
    return {"files": files}

@mcp.tool()
async def process_ffmpeg(command: str) -> dict:
    """Execute FFMPEG command with ID references"""
    # Parse command to extract {id} references
    # Resolve IDs to actual paths
    # Validate and execute command
    # Return logs with IDs instead of paths
    
@mcp.tool()
async def get_file_info(file_id: str) -> dict:
    """Get metadata for a file by ID"""
    # Resolve file path
    # Run ffprobe to get metadata
    # Return sanitized metadata
```

### 4. Security Configuration
```python
# config.py
class SecurityConfig:
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.mp3', '.mp4', '.wav', '.flac', '.m4a'}
    
    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Process timeout (5 minutes)
    PROCESS_TIMEOUT = 300
    
    # Resource limits
    MEMORY_LIMIT = "512M"
    CPU_LIMIT = "1.0"
```

### 5. Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install FFMPEG and curl for uv
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Create non-root user
RUN useradd -m -u 1000 mcp

# Set up directories
RUN mkdir -p /tmp/music/source /tmp/music/temp && \
    chown -R mcp:mcp /tmp/music

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY src/ ./src/
USER mcp

# Use uv to run the server
CMD ["uv", "run", "python", "-m", "mcp.server.stdio", "src.server:mcp"]
```

## Key Implementation Notes

### Phase 1: Basic Functionality
1. Implement file listing and registration
2. Create simple FFMPEG command execution (hardcoded operations)
3. Add basic security validation
4. Test with MCP Inspector

### Phase 2: Enhanced Features
1. Parse complex FFMPEG commands with {id} substitution
2. Add progress reporting for long operations
3. Implement file cleanup and session management
4. Add comprehensive logging

### Phase 3: Production Readiness
1. Complete security hardening
2. Add OAuth 2.1 authentication
3. Implement distributed state management
4. Performance optimization

## Testing Commands
```bash
# Run locally with uv
uv run python -m mcp.server.stdio src.server:mcp

# Test with Inspector
npx @modelcontextprotocol/inspector --stdio uv run python -m mcp.server.stdio src.server:mcp

# Run in Docker
docker build -t ffmpeg-mcp .
docker run -it ffmpeg-mcp

# Development workflow with uv
uv add --dev pytest pytest-asyncio  # Add dev dependencies
uv run pytest                        # Run tests
uv sync                             # Sync dependencies from lock file
```

## UV-Specific Development Benefits
1. **Fast dependency resolution**: uv resolves and installs dependencies 10-100x faster than pip
2. **Reproducible builds**: `uv.lock` ensures exact same versions across environments
3. **Built-in virtual environment management**: No need for separate venv commands
4. **Python version management**: Automatically uses `.python-version` file
5. **Simplified Docker builds**: Faster container builds with uv's caching

## Example Usage Flow
1. Client calls `list_files()` → receives list with IDs
2. Client calls `process_ffmpeg("ffmpeg -i {file_001} -c:a mp3 {output_001}")`
3. Server resolves IDs, validates command, executes FFMPEG
4. Server returns sanitized logs with ID references

## Critical Security Checklist
- [ ] All file paths validated against whitelist directories
- [ ] FFMPEG commands parsed and validated before execution
- [ ] No direct path exposure in responses
- [ ] Process execution with timeout
- [ ] Resource limits enforced
- [ ] Comprehensive input sanitization
- [ ] Audit logging for all operations

This specification provides Claude Code with concrete implementation details while maintaining flexibility for optimization and enhancement during development.