Ok # FFMPEG MCP Server - INTELLIGENT VIDEO EDITING ✅

## Project Status: ADVANCED CONTENT-AWARE SYSTEM ✅
This is an intelligent FFMPEG MCP server with AI-powered content understanding. The system now has "eyes" to understand video content and provide smart editing suggestions without manual timecode specification.

### 🎬 MUSIC VIDEO CREATION PROVEN ✅
Successfully created complete music video using intelligent scene detection, automatic screenshot generation, and smart concatenation workflows. The system can autonomously identify best scenes, combine clips, and add audio tracks.

### 🎵 BEAT-SYNCHRONIZED KOMPOSITION SYSTEM ✅
Implemented advanced komposition JSON processing for beat-synchronized music videos. Supports precise BPM timing, video stretching, and multi-segment workflows with 120 BPM = 8 seconds per 16 beats formula.

### 🎤 SPEECH DETECTION & AUDIO ANALYSIS ✅
Implemented AI-powered speech detection using Silero VAD with pluggable backend architecture. Provides precise speech timestamps, quality assessment, and intelligent editing suggestions for advanced audio-video synchronization workflows.

### 📐 FORM-FACTOR CONTROL SYSTEM ✅ **NEW**
Intelligent aspect ratio and cropping management system that solves the portrait→landscape mismatch problem. Users can now specify target format upfront and preview exactly how videos will be cropped before processing. Includes smart cropping options (center, letterbox, blur background) and platform-specific presets (YouTube, Instagram, TikTok).

## Quick Start

### 🐳 Docker Setup (Recommended)
```bash
# Build and run with Docker (production-ready)
./build-docker.sh run

# Or development mode with MCP Inspector
./build-docker.sh dev

# View logs and status
docker-compose logs -f
docker-compose ps
```

### 🛠️ Local Development
```bash
# Start the MCP server locally
uv run python -m src.server

# Test with MCP Inspector (running at http://127.0.0.1:6274)
npx @modelcontextprotocol/inspector uv run python -m src.server

# Run all tests (unit + end-to-end + intelligent analysis)
python run_tests.py

# Run specific tests
uv run pytest tests/test_ffmpeg_integration.py -v -s                    # Unit tests
uv run python tests/test_end_to_end_music_video.py                     # Full workflow test
uv run python tests/test_intelligent_content_analysis.py               # Content analysis test
uv run pytest tests/test_komposition_music_video.py -v -s              # Komposition system test
```

## MCP Server Configuration for Claude Code

### 🐳 Docker Configuration (Recommended)
```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "nc",
      "args": ["localhost", "8000"],
      "cwd": "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp"
    }
  }
}
```

### 🛠️ Local Development Configuration
```json
{
  "mcpServers": {
    "ffmpeg-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.server"],
      "cwd": "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp"
    }
  }
}
```

## Available MCP Tools (Complete Production System ✅)
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
9. **get_scene_screenshots(file_id)** - Get scene screenshots with URLs for visual scene selection 📸

### Speech Detection & Audio Analysis Tools 🎤
10. **detect_speech_segments(file_id, force_reanalysis=False, threshold=0.5, min_speech_duration=250, min_silence_duration=100)** - AI-powered speech detection with precise timestamps using Silero VAD
11. **get_speech_insights(file_id)** - Comprehensive speech analysis with quality metrics, timing patterns, and editing suggestions

### Form-Factor & Aspect Ratio Management Tools 📐 **NEW**
12. **analyze_video_formats(file_ids)** - Analyze aspect ratios of multiple videos and suggest optimal target format
13. **preview_format_conversion(file_id, target_format, crop_mode, timestamp)** - Generate preview image showing how video will be cropped/fitted
14. **create_format_conversion_plan(file_ids, target_format, crop_mode)** - Create detailed plan for converting videos to consistent format
15. **get_format_presets()** - Get available format presets (YouTube, Instagram, TikTok, etc.) with cropping options

### Workflow Management Tools 🔧
16. **list_generated_files()** - List all processed files in temp directory with metadata 
17. **batch_process(operations)** - Execute multi-step workflows with atomic transaction support

### Beat-Synchronized Music Video Tools 🎵
18. **process_komposition_file(komposition_path)** - Create beat-synchronized music videos from komposition JSON
19. **process_transition_effects_komposition(komposition_path)** - Process komposition with advanced transition effects tree

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
- **✅ Beat-Synchronized Videos**: Komposition JSON processing with precise BPM timing (120 BPM = 8s per 16 beats)
- **✅ Video Stretching**: FFmpeg setpts/atempo filters for perfect beat synchronization
- **✅ Transition Effects**: Gradient wipe, crossfade, and opacity transitions with effects tree processing
- **✅ Advanced Effects System**: Non-destructive layered effects architecture based on documents/Describing_effects.md
- **✅ Speech Detection**: AI-powered speech detection using Silero VAD with pluggable backend architecture
- **✅ Speech Analysis**: Comprehensive quality metrics, timing patterns, and intelligent editing suggestions

## Available FFMPEG Operations
- **convert** - Convert video/audio format
- **extract_audio** - Extract audio from video
- **trim** - Trim video/audio (requires: start, duration)
- **resize** - Resize video (requires: width, height)
- **normalize_audio** - Normalize audio levels
- **to_mp3** - Convert to MP3 format (192k bitrate)
- **replace_audio** - Replace video audio with another audio file
- **concatenate_simple** - Smart concatenate two videos with automatic resolution/audio handling
- **image_to_video** - Convert image to video clip (requires duration in seconds)
- **reverse** - Reverse video and audio playback
- **gradient_wipe** - Gradient wipe transition between videos (requires second_video, duration, offset)
- **crossfade_transition** - Crossfade transition between videos (requires second_video, duration, offset)
- **opacity_transition** - Opacity-based transition with transparency control

## File Management and Visual Content
- **Source directory**: `/tmp/music/source/` (contains test videos)
- **Temp directory**: `/tmp/music/temp/` (generated outputs)
- **Screenshots directory**: `/tmp/music/screenshots/{sourceRef}/` (scene screenshots)
- **Metadata directory**: `/tmp/music/metadata/` (analysis cache)
- **Security**: All file access restricted to allowed directories only
- **File IDs**: Format `file_12345678` for secure reference

### Screenshot System 📸
- **Automatic Generation**: Screenshots created from scene start times during analysis
- **URL Access**: Configurable base URL for screenshot access (default: `https://kompo.st/screenshots`)
- **Organized Storage**: Screenshots stored by video name in dedicated folders
- **High Quality**: FFMPEG extracts high-quality JPG frames for visual scene selection
- **Scene Mapping**: Each screenshot linked to scene timing and content analysis data

## Security Features (All Implemented)
- ✅ ID-based file references (no direct path exposure)
- ✅ Directory access restrictions to `/tmp/music/source` and `/tmp/music/temp`
- ✅ File size validation (100MB limit)
- ✅ Extension validation (mp3, mp4, wav, flac, m4a, avi, mkv, mov, webm, ogg)
- ✅ Process timeout protection (5 minutes)
- ✅ Command whitelisting and parameter validation
- ✅ Input sanitization and error handling

## Project Structure (Organized for LLM Navigation)

**REFERENCE**: See `PROJECT_STRUCTURE.md` for complete layout guide

### Core System (`src/`)
- **MCP Server**: `server.py`, `file_manager.py`, `config.py`
- **Video Processing**: `ffmpeg_wrapper.py`, `content_analyzer.py`, `video_normalizer.py`
- **Composition System**: `komposition_*.py`, `music_video_builder.py`, `composition_planner.py`
- **Speech Detection**: `speech_*.py`, `enhanced_speech_analyzer.py`
- **Resource Management**: `resource_manager.py`, `deterministic_id_generator.py`

### Testing (`tests/`)
- **CI/CD**: `ci/test_*.py` - Automated pipeline tests
- **Production**: `test_*_integration.py` - Core functionality tests
- **Development**: `dev/test_*.py` - Feature development tests

### Examples & Tools
- **Workflows**: `examples/video-workflows/` - Moved all `create_*.py` scripts
- **Komposition Examples**: `examples/komposition-examples/` - All JSON compositions
- **Analysis Tools**: `tools/analysis/` - Debugging and analysis utilities
- **Scripts**: `scripts/` - Utility scripts (`main.py`, `run_tests.py` moved here)

### Archive
- **Legacy Tests**: `archive/legacy-tests/` - Historical `test_*.py` files from root

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

## 📚 Additional Documentation

### Core Documentation
- **[PRODUCTION_RECOMMENDATIONS.md](documents/PRODUCTION_RECOMMENDATIONS.md)** - Critical fixes, architecture lessons, and implementation priorities
- **[WORKFLOW_EXAMPLES.md](documents/WORKFLOW_EXAMPLES.md)** - Complete production workflows with code examples
- **[IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md)** - Comprehensive quality assessment and 4-week improvement roadmap

### Speech Detection Research & Planning
- **[SPEECH_DETECTION_FEATURE_SPEC.md](SPEECH_DETECTION_FEATURE_SPEC.md)** - Feature specification for speech detection and audio synchronization
- **[AUDIO_PROCESSING_FINDINGS.md](documents/AUDIO_PROCESSING_FINDINGS.md)** - Implementation research and technology stack recommendations

### Docker & Deployment
- **[DOCKER_SETUP.md](documents/DOCKER_SETUP.md)** - Complete Docker containerization guide with production deployment
- **[build-docker.sh](build-docker.sh)** - Automated Docker build and deployment script

## 📚 Key Learnings & Architecture Insights

### 🎯 Successful Design Patterns
- **Content-First Analysis**: Scene detection before editing provides intelligent suggestions
- **Screenshot URLs**: Visual scene selection dramatically improves user experience  
- **Caching System**: 3000x performance improvement with persistent metadata storage
- **Smart Concatenation**: Automatic resolution/audio compatibility handling with orientation normalization
- **Security by Design**: ID-based file references prevent path traversal

### 🔧 Production Workflow Insights
- **Music Video Pattern**: video-first editing, audio post-processing works excellently
- **Scene-Based Editing**: Users prefer visual scene selection over manual timecode entry
- **Intelligent Suggestions**: AI-driven trim suggestions save significant time
- **Batch Operations**: Multi-step workflows need atomic transaction support

### ⚠️ Identified Gaps & Future Enhancements

#### ✅ Recently Implemented (Addressing Production Gaps)
1. **Generated File Tracking**: `list_generated_files()` - tracks all temp outputs with metadata ✅
2. **Batch Processing API**: `batch_process(operations)` - atomic multi-step workflows with chaining ✅
3. **Video Rotation Fix**: Smart orientation handling in concatenation - prevents 90° rotation issues ✅
4. **Komposition JSON Processing**: Beat-synchronized music video creation with precise timing ✅
5. **Image-to-Video Fix**: Fixed duration parameter handling in image_to_video operation ✅
6. **File Resolution System**: Fixed komposition processor file ID resolution ✅

#### 🚨 Remaining Future Enhancements  
1. **Image Integration**: Missing tools to insert images between video clips
2. **Progress Tracking**: No real-time feedback for long-running video operations
3. **Error Recovery**: Failed operations leave orphaned temp files

#### 🎤 Speech Detection & Audio Synchronization (In Development)
**Next Major Feature**: Intelligent speech detection and audio synchronization capabilities

**Planned MCP Tools**:
```python
# Speech detection and transcription
detect_speech_segments(file_id, options)           # VAD processing with timestamps
transcribe_speech(file_id, segments, options)      # STT with word-level timing
get_speech_insights(file_id)                       # Analysis and quality metrics

# Audio synchronization and mixing  
synchronize_speech_audio(video_id, speech_segments, music_track)  # Layer speech over music
mix_audio_tracks(primary_audio, background_audio, options)        # Advanced audio mixing
```

**Technology Stack** (Research Complete):
- **Primary**: Silero VAD + OpenAI Whisper + FFmpeg mixing
- **Alternatives**: WebRTC VAD, WhisperX, Vosk (pluggable backends)
- **Timeline Sync**: Word-level timestamps for perfect video-speech alignment

#### 🎯 Remaining Recommended Features
```python
# Additional tools that would complete the system:
insert_image(video_id, image_id, time)   # Add images to video timeline
get_operation_progress(job_id)           # Real-time progress updates
cleanup_failed_operations()              # Error recovery and cleanup
create_video_preset(name, operations)    # Save common workflows as presets
```

### 💡 Architecture Lessons
- **File ID Consistency**: Current system regenerates IDs between runs - breaks user references
- **Temp File Lifecycle**: Need explicit temp file management in MCP interface
- **Operation Chaining**: Users naturally want to chain operations - needs first-class support
- **Visual Feedback**: Screenshots dramatically improve content selection accuracy
- **Video Orientation**: Mixed portrait/landscape videos require smart orientation normalization to prevent rotation artifacts
- **Beat Timing System**: 120 BPM formula (16 beats = 8 seconds) enables precise music video synchronization
- **Pre-Input Args**: FFmpeg operations requiring arguments before -i input need special parameter handling

## Developer Communication Preferences
- **Concise responses**: Minimize token usage, answer directly
- **Discuss before implementing**: For changes >10 LOC, discuss first
- **Minimal comments**: Only on function definitions when needed
- **Senior developer context**: Deep technical knowledge assumed
- **Cost-conscious**: Optimize for efficiency and brevity
- **YOLO commands**: When prefixed with "YOLO", implement changes directly without discussion

## AI-Generated Documentation Organization
- **AI-Generated Files**: All .md files created by Claude/AI assistants should be moved to `documents/ai-generated/` folder
- **Task-Based Organization**: Group documents by the task/feature they address with concise folder names
- **Purpose**: Enables easier tracking of which documentation is AI-generated vs human-authored, and groups related docs together
- **Folder Structure**: 
  - `documents/` - Human-authored documentation and specifications
  - `documents/ai-generated/mcp-config/` - MCP server configuration and interface docs
  - `documents/ai-generated/workflow-analysis/` - Workflow efficiency and analysis documents
  - `documents/ai-generated/komposition/` - Beat-synchronized video creation system docs
  - `documents/ai-generated/speech-detection/` - Speech detection and audio processing docs
  - `documents/ai-generated/feature-requests/` - Feature requests and continuation guides
- **Implementation**: Claude should proactively organize AI-generated files into task-based subfolders with concise names