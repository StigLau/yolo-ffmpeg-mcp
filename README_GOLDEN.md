# FFMPEG MCP Server 🎬

An advanced Model Context Protocol (MCP) server providing intelligent video and audio processing capabilities through FFMPEG operations, enhanced with AI-powered composition planning and speech analysis.

## ✨ Features

### 🎯 Core Video Operations
- **File Management**: Secure discovery, validation, and metadata extraction
- **Basic Processing**: Extract audio, trim, resize, convert, concatenate
- **Advanced Operations**: Audio replacement, normalization, transitions
- **Format Support**: MP4, AVI, MP3, WAV, FLAC, JPEG, PNG and more

### 🧠 AI-Powered Intelligence
- **Speech Analysis**: Detect speech segments with natural pause detection
- **Intelligent Composition**: AI-planned video layouts with beat synchronization
- **Content Analysis**: Scene detection and object recognition
- **Multi-modal Optimization**: Balance video quality + speech preservation + timing

### 🛠️ MCP Integration
- **58 MCP Tools**: Full Model Context Protocol compliance for LLM integration
- **14 Advanced AI Tools**: Intelligent composition and analysis features
- **Real-time Processing**: Streaming operations with progress tracking
- **Batch Operations**: Multi-step workflows with atomic transactions

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- FFMPEG installed (`brew install ffmpeg` on macOS)
- Virtual environment with dependencies

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd yolo-ffmpeg-mcp

# Install dependencies
source .venv/bin/activate
# Dependencies already included in venv

# Test the server
python main.py
```

### Basic Usage
```bash
# Start MCP server
python main.py

# With MCP Inspector (development)
mcp dev main.py

# Copy test media files to source directory
mkdir -p /tmp/music/source
cp .testdata/*.mp4 /tmp/music/source/
```

## 🎵 Example Workflows

### Create a Music Video
```python
# Via MCP protocol in LLM interaction:
# 1. "List available video files"
files = await list_files()

# 2. "Analyze the first video"
analysis = await get_file_info(file_id)

# 3. "Merge two videos into a music video"
result = await process_file(video1_id, "concatenate_simple", second_video=video2_id)
```

### Intelligent Composition
```python
# AI-powered composition planning
plan = await generate_composition_plan(
    source_filenames=["video1.mp4", "video2.mp4"],
    background_music="track.mp3",
    total_duration=24.0,
    bpm=120
)

# Execute the intelligent plan
result = await process_composition_plan(plan)
```

### Speech-Aware Editing
```python
# Detect speech segments
speech = await detect_speech_segments(file_id, threshold=0.5)

# Get speech insights
insights = await get_speech_insights(file_id)

# Process with speech preservation
result = await process_speech_komposition("composition.json")
```

## 📁 Project Structure

```
├── src/                          # MCP Server Implementation
│   ├── server.py                 # Main MCP server (58 tools)
│   ├── enhanced_speech_analyzer.py  # Speech detection & analysis
│   ├── composition_planner.py    # Intelligent composition planning
│   ├── content_analyzer.py       # AI video content analysis
│   ├── ffmpeg_wrapper.py         # FFMPEG command interface
│   └── ...                       # Additional processing modules
├── .testdata/                    # Test Media Files
│   ├── JJVtt947FfI_136.mp4      # 1280x720 test video (17MB)
│   ├── _wZ5Hof5tXY_136.mp4      # 720x1280 test video (10MB)
│   └── *.mp3, *.flac            # Audio test files
├── tests/                        # Comprehensive Test Suite
│   ├── test_intelligent_composition.py
│   ├── test_speech_implementation.py
│   └── test_*.py                 # 12+ test files
├── create_*.py                   # Production Example Scripts
├── *.json                        # Working Configuration Examples
└── main.py                       # Server Entry Point
```

## 🧪 Testing

### Run Test Suite
```bash
# Basic operations
python test_basic_operations.py

# Advanced composition
python test_intelligent_composition.py

# Speech analysis
python test_speech_implementation.py

# All tests
python run_tests.py
```

### Test with Real Media
```bash
# Copy test files to source directory
cp .testdata/*.mp4 /tmp/music/source/

# Start server and test via MCP protocol
python main.py
```

## 🔧 Configuration

### Environment Variables
```bash
export FFMPEG_SOURCE_DIR="/tmp/music/source"    # Source files
export FFMPEG_TEMP_DIR="/tmp/music/temp"        # Temporary processing
export FFMPEG_SCREENSHOTS_DIR="/tmp/music/screenshots"  # Screenshots
export FFMPEG_PATH="ffmpeg"                     # FFMPEG binary path
```

### Security Settings
- **File Size Limit**: 500MB maximum
- **Process Timeout**: 5 minutes
- **Allowed Extensions**: Video, audio, image formats only
- **Sandboxed Operations**: Secure file system access

## 🎬 MCP Tools Reference

### Core Tools
- `list_files()` - Discover available media files
- `get_file_info(file_id)` - Extract detailed metadata
- `process_file(file_id, operation, **params)` - Execute FFMPEG operation
- `get_available_operations()` - List all supported operations

### Advanced Tools
- `analyze_composition_sources(filenames)` - Multi-source analysis
- `generate_composition_plan(sources, music, duration, bpm)` - AI planning
- `detect_speech_segments(file_id, threshold)` - Speech detection
- `create_video_from_description(description, mode)` - Natural language creation

### Batch Operations
- `batch_process(operations)` - Multi-step workflows
- `list_generated_files()` - Track outputs
- `cleanup_temp_files()` - Resource management

## 📚 Documentation

- **`RESTORATION_SUMMARY.md`**: Project restoration and file changes
- **`documents/`**: Advanced implementation guides
- **`*.json`**: Working configuration examples
- **`create_*.py`**: Production workflow examples

## 🎯 Production Examples

### Beat-Synchronized Video
```bash
python create_beat_synchronized_video.py
```

### Speech-Aware Music Video
```bash
python working_demo_production.py
```

### Advanced Composition
```bash
python create_final_production.py
```

## 🛡️ Requirements

- **Python**: 3.13+
- **FFMPEG**: Latest version with codec support
- **Memory**: 512MB+ for processing
- **Storage**: Space for temporary files and outputs
- **Dependencies**: FastMCP, Pydantic, AsyncIO support

## 🚀 Integration

### Claude Desktop
Add to MCP configuration:
```json
{
  "mcpServers": {
    "ffmpeg-processor": {
      "command": "python",
      "args": ["/path/to/main.py"]
    }
  }
}
```

### Custom LLM Integration
Connect via MCP protocol to access all 58 tools for intelligent video processing.

---

**Status**: ✅ Production Ready  
**Version**: Golden State Restored (July 26, 2025)  
**Focus**: Advanced MCP server for AI-driven video editing  

Ready to create amazing AI-powered video content! 🎬✨