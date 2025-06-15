# Summary

PoC of wrapping FFMPEG and packaging it as Music Video scriptable from natural language. IE, how one can leverage existing libraries and APIs to be accessible to LLMs, do API discovery and find new use cases.
Working with a developer-LLM (Claude Code) which has access to the project, it can easily append functionality to the system, while running in "standard mode" - The end user talks to Claude Desktop which in turn talks to the MCP server, wrapping FFMPEG and other libraries. Standard mode is restricted by the functionality that was created up until now, but the LLM/Claude Desktop can find new usages of the provided functinality

# FFMPEG MCP Server 🎬

An intelligent video editing MCP server with AI-powered content analysis, speech detection, and automated music video creation.

## What is this?

This is a **Model Context Protocol (MCP) server** that lets AI assistants like Claude create, edit, and analyze videos using FFMPEG. Think of it as giving your AI assistant "eyes" to understand video content and "hands" to edit videos intelligently.

**Perfect for**: Music video creation, content analysis, automated editing, speech-synchronized videos, and intelligent video processing workflows.

## Quick Start 🚀

### For Claude Code Users
1. **Install Dependencies**
   ```bash
   pip install uv
   uv sync
   ```

2. **Add to Claude Code Configuration**
   
   Edit your Claude Code MCP configuration file:
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

3. **Start Using**
   - Place video files in `/tmp/music/source/`
   - Ask Claude to create music videos, analyze content, or edit videos
   - Find generated videos in `/tmp/music/temp/`

### For Aider Users
```bash
# Start MCP server in background
uv run python -m src.server &

# Use with Aider for video editing workflows
aider --mcp-server localhost:8000
```

### Docker Setup (Production)
```bash
# Build and run with Docker
./build-docker.sh run

# Development mode with MCP Inspector
./build-docker.sh dev
```

## What Makes This Special? ✨

- **AI Content Analysis** - Automatically understands video scenes, objects, and timing
- **Speech Detection** - Finds and preserves speech segments in videos  
- **Beat Synchronization** - Creates music videos perfectly timed to BPM
- **Smart Editing** - Suggests optimal cuts and transitions based on content analysis
- **Intelligent Workflows** - One command creates complete music videos from description

## Key Features 🎯

### Core Video Processing
- Convert formats, trim, resize, extract audio
- Professional-grade FFMPEG operations with safety validation
- Secure file handling with ID-based references

### Intelligent Analysis
- **Scene Detection**: Automatically identifies key video segments
- **Object Recognition**: Understands what's happening in your videos  
- **Smart Trim Suggestions**: AI recommends best parts to use
- **Visual Scene Selection**: Preview scenes with screenshot URLs

### Advanced Music Video Creation
- **Beat-Synchronized Editing**: Perfect timing to music BPM
- **Speech-Aware Processing**: Preserves dialogue while adding background music
- **Transition Effects**: Professional fade, wipe, and crossfade transitions
- **One-Command Creation**: Generate complete music videos from text descriptions

## New to MCP Servers? 🤔

**MCP (Model Context Protocol)** lets AI assistants connect to external tools and services. This server gives Claude video editing superpowers!

- **For Beginners**: [MCP Overview](https://modelcontextprotocol.io/)
- **Claude Code Setup**: [Official Documentation](https://docs.anthropic.com/en/docs/claude-code)
- **Aider Integration**: [Aider MCP Guide](https://aider.chat/docs/mcp.html)

## Example Workflows 🎬

### Create a Music Video
```
"Create a 30-second music video using lookin.mp4 and panning.mp4 with background music at 135 BPM"
```

### Analyze Video Content  
```
"Analyze this video and suggest the best 10-second clip for social media"
```

### Speech-Synchronized Video
```
"Extract speech from intro.mp4 and layer it over background music while keeping the original speech clear"
```

## Documentation 📚

- **[Getting Started Guide](documents/WORKFLOW_EXAMPLES.md)** - Complete production workflows
- **[Docker Setup](documents/DOCKER_SETUP.md)** - Production deployment guide  
- **[Feature Specifications](documents/)** - Technical details and advanced features
- **[CI/CD Guide](.github/workflows/ci.yml)** - Automated testing and deployment

## Production Ready ✅

- **Comprehensive Testing**: 16+ test files covering all workflows
- **CI/CD Pipeline**: GitHub Actions with Docker containers
- **Security First**: Input validation, process isolation, file restrictions
- **Real Video Processing**: Tested with actual video files and music tracks
- **Error Handling**: Graceful failure recovery and detailed error reporting

## Project Status

**PRODUCTION READY** - Complete intelligent video editing system with:
- ✅ 15+ MCP tools for video processing
- ✅ AI-powered content analysis and speech detection  
- ✅ Beat-synchronized music video creation
- ✅ Comprehensive test suite with CI/CD
- ✅ Docker containerization for production deployment
- ✅ Security-first architecture with proper validation

Built for creators, developers, and AI enthusiasts who want to push the boundaries of automated video editing.
