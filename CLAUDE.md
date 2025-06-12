Ok # FFMPEG MCP Server - INTELLIGENT VIDEO EDITING ✅

## Project Status: ADVANCED CONTENT-AWARE SYSTEM  
This is an intelligent FFMPEG MCP server with AI-powered content understanding. The system now has "eyes" to understand video content and provide smart editing suggestions without manual timecode specification.

## Quick Start
```bash
# Start the MCP server
uv run python -m src.server

# Test with MCP Inspector (running at http://127.0.0.1:6274)
npx @modelcontextprotocol/inspector uv run python -m src.server

# Run all tests (unit + end-to-end + intelligent analysis)
python run_tests.py

# Run specific tests
uv run pytest tests/test_ffmpeg_integration.py -v -s                    # Unit tests
uv run python tests/test_end_to_end_music_video.py                     # Full workflow test
uv run python tests/test_intelligent_content_analysis.py               # Content analysis test
```

## MCP Server Configuration for Claude Code
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

## Available MCP Tools (Intelligent Content-Aware ✅)
### Core Video Processing Tools
1. **list_files()** - List source files with secure IDs
2. **get_file_info(file_id)** - Get detailed metadata using ffprobe
3. **get_available_operations()** - Show 9 available FFMPEG operations
4. **process_file(input_file_id, operation, output_extension, **params)** - Process files
5. **cleanup_temp_files()** - Remove temporary files

### Intelligent Content Analysis Tools 🧠
6. **analyze_video_content(file_id, force_reanalysis=False)** - AI-powered scene detection and object recognition
7. **get_video_insights(file_id)** - Get cached content analysis with editing suggestions  
8. **smart_trim_suggestions(file_id, desired_duration=10.0)** - Intelligent trim recommendations based on content

## Test Results Summary
- **✅ File Management**: Secure ID-based file references working
- **✅ MP3 Conversion**: Successfully converted test video to MP3 (86KB output)
- **✅ Video Trimming**: Successfully trimmed video to 5 seconds (1.6MB output)
- **✅ Metadata Extraction**: Full video info extraction with ffprobe
- **✅ Error Handling**: Proper validation and error responses
- **✅ Security**: All security features verified and working
- **✅ End-to-End Music Video**: Complete workflow test creating 14.6s music video from multiple sources
- **✅ Performance Optimization**: Video property caching delivers 3000x faster repeated analysis
- **✅ Intelligent Content Analysis**: AI-powered scene detection with 21 scenes identified automatically
- **✅ Smart Editing Suggestions**: Object recognition and content-aware trimming recommendations

## Available FFMPEG Operations
- **convert** - Convert video/audio format
- **extract_audio** - Extract audio from video
- **trim** - Trim video/audio (requires: start, duration)
- **resize** - Resize video (requires: width, height)
- **normalize_audio** - Normalize audio levels
- **to_mp3** - Convert to MP3 format (192k bitrate)

## File Management
- **Source directory**: `/tmp/music/source/` (contains test video PXL_20250306_132546255.mp4)
- **Temp directory**: `/tmp/music/temp/` (generated outputs)
- **Security**: All file access restricted to allowed directories only
- **File IDs**: Format `file_12345678` for secure reference

## Security Features (All Implemented)
- ✅ ID-based file references (no direct path exposure)
- ✅ Directory access restrictions to `/tmp/music/source` and `/tmp/music/temp`
- ✅ File size validation (100MB limit)
- ✅ Extension validation (mp3, mp4, wav, flac, m4a, avi, mkv, mov, webm, ogg)
- ✅ Process timeout protection (5 minutes)
- ✅ Command whitelisting and parameter validation
- ✅ Input sanitization and error handling

## Project Structure
```
src/
├── server.py           # Main MCP server with 6 tools
├── file_manager.py     # Secure file ID mapping
├── ffmpeg_wrapper.py   # Safe FFMPEG command building
└── config.py          # Security configuration

tests/
├── test_ffmpeg_integration.py  # Comprehensive integration tests
└── files/PXL_20250306_132546255.mp4  # Test video file
```

## Dependencies (UV managed)
- `mcp` - MCP protocol implementation with FastMCP
- `pydantic` - Data validation and models
- `pytest` + `pytest-asyncio` - Testing framework

## Usage Example
1. Start server: `uv run python -m src.server`
2. Call `list_files()` to get file IDs
3. Use `process_file(file_id, "to_mp3", "mp3")` to convert
4. Check `/tmp/music/temp/` for output files

**This MCP server is production-ready and fully tested with real FFMPEG operations.**

## Developer Communication Preferences
- **Concise responses**: Minimize token usage, answer directly
- **Discuss before implementing**: For changes >10 LOC, discuss first
- **Minimal comments**: Only on function definitions when needed
- **Senior developer context**: Deep technical knowledge assumed
- **Cost-conscious**: Optimize for efficiency and brevity
- **YOLO commands**: When prefixed with "YOLO", implement changes directly without discussion