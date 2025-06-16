# FFMPEG MCP Server - Project Context

## Project Status: COMPLETE AND FUNCTIONAL ✅

This is a fully working FFMPEG MCP (Model Context Protocol) server with comprehensive testing completed.

## Architecture Overview

### Core Components
- **FileManager** (`src/file_manager.py`) - Secure file handling with ID-based references
- **FFMPEGWrapper** (`src/ffmpeg_wrapper.py`) - Safe FFMPEG command building and execution
- **SecurityConfig** (`src/config.py`) - Security settings and validation
- **Server** (`src/server.py`) - Main MCP server with 6 tools

### Key Features
- **Security**: ID-based file references (no direct path exposure)
- **Validation**: File size, extension, and directory restrictions
- **Operations**: 6 FFMPEG operations (convert, extract_audio, trim, resize, normalize_audio, to_mp3)
- **Error Handling**: Comprehensive error handling and timeout protection

## File Structure
```
/Users/stiglau/utvikling/privat/yolo-ffmpeg-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py           # Main MCP server (6 tools)
│   ├── file_manager.py     # File mapping and security
│   ├── ffmpeg_wrapper.py   # FFMPEG command builder
│   └── config.py          # Security configuration
├── tests/
│   ├── __init__.py
│   └── test_ffmpeg_integration.py  # Comprehensive integration tests
├── tests/files/
│   └── PXL_20250306_132546255.mp4  # Test video file
├── pyproject.toml         # UV project configuration
├── uv.lock               # Dependencies lock file
└── CLAUDE.md             # MCP server documentation
```

## Working Directories
- **Source files**: `/tmp/music/source/` (contains test video)
- **Temp files**: `/tmp/music/temp/` (generated outputs)

## Dependencies (UV managed)
- `mcp` - MCP protocol implementation
- `pydantic` - Data validation
- `pytest` + `pytest-asyncio` - Testing framework

## MCP Tools Available
1. **list_files()** - List source files with secure IDs
2. **get_file_info(file_id)** - Get detailed metadata 
3. **get_available_operations()** - Show FFMPEG operations
4. **process_file(input_file_id, operation, output_extension, **params)** - Process files
5. **cleanup_temp_files()** - Remove temporary files

## Test Results (ALL PASSING ✅)
- File listing and registration
- Metadata extraction with ffprobe
- MP3 conversion (86KB output generated)
- Video trimming (1.6MB output generated)
- Error handling and validation
- Security features verified

## Current Server Status
- **MCP Inspector running** at http://127.0.0.1:6274
- **Test video available**: PXL_20250306_132546255.mp4 (8.6MB, 3.57s duration)
- **Generated outputs**: MP3 and trimmed MP4 files in temp directory

## Key Commands
```bash
# Start MCP server
uv run python -m src.server

# Test with Inspector  
npx @modelcontextprotocol/inspector uv run python -m src.server

# Run tests
uv run pytest tests/test_ffmpeg_integration.py -v -s

# Install dependencies
uv add mcp pydantic
uv add --dev pytest pytest-asyncio
```

## Security Implementation
- File access restricted to allowed directories only
- All file references use secure IDs (format: `file_12345678`)
- Input validation for extensions, file sizes, operations
- Process timeout protection (5 minutes)
- Command whitelisting with parameter validation

## FFMPEG Operations
- **convert**: Video/audio format conversion
- **extract_audio**: Extract audio from video 
- **trim**: Trim video/audio (requires start, duration params)
- **resize**: Resize video (requires width, height params)
- **normalize_audio**: Normalize audio levels
- **to_mp3**: Convert to MP3 format

## Next Steps for Claude
1. Server is fully functional and tested
2. Can be used immediately for FFMPEG operations
3. Ready for integration with Claude Code MCP configuration
4. All security measures implemented and verified

**This project is production-ready with comprehensive testing completed.**