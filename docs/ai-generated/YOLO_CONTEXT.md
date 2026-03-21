# YOLO-FFMPEG-MCP Context

*Compressed project state - keep under 200 lines. Update after major changes.*

## Project Identity
**YOLO-FFMPEG-MCP**: Master orchestrator for video processing workflows via Model Context Protocol (MCP). Coordinates external video processing libraries without duplicating their functionality.

## System Architecture

### Core Components
```
src/
├── server.py                  # MCP server entry point
├── file_manager.py           # File operations and path management
├── ffmpeg_wrapper.py         # FFmpeg execution coordination  
├── komposition_processor.py  # Music video workflow processing
├── download_service.py       # YouTube/content download
└── containerized_ffmpeg.py   # Docker-isolated FFmpeg execution
```

### External Integrations
- **Komposteur JAR**: Beat-synchronization and music composition engine
- **VideoRenderer JAR**: FFmpeg optimization and video processing
- **Build Detective**: CI/build failure analysis and automation
- **MCP Protocol**: Claude Code integration for video workflows

### Data Flow
1. **MCP Client** → Tool calls → **YOLO Server**
2. **YOLO Server** → Coordinates → **External JARs** (Komposteur/VideoRenderer)
3. **File Manager** → Manages → **Video/Audio Assets** 
4. **Results** → Back to → **MCP Client**

## Key Interfaces

### MCP Tools (Primary)
- `list_files()`: Discover available media assets
- `create_video_from_description()`: Natural language → video workflow
- `process_komposition_file()`: Beat-synchronized video processing
- `download_youtube_video()`: Content acquisition

### External JAR Communication
- **Komposteur**: Via subprocess calls to uber-kompost JAR
- **VideoRenderer**: Direct Java bridge integration
- **Error Handling**: Graceful degradation when JARs unavailable

## Development Patterns

### File Management
- **Source**: `/tmp/music/source` (input media)
- **Temp**: `/tmp/music/temp` (processing workspace)  
- **Finished**: `/tmp/music/finished` (output videos)
- **Registry**: JSON-based file tracking with deterministic IDs

### Async Patterns
- **MCP Tools**: All async/await for non-blocking client interaction
- **External Calls**: Subprocess management with timeout handling
- **Error Propagation**: Structured error responses to MCP client

### Build Detective Integration
- **BD-First Protocol**: Use BD analysis before LLM token consumption for CI issues
- **Local CI**: `scripts/bd_local_ci.py` for pre-push validation
- **Automated Analysis**: BD tools for GitHub Actions failure diagnosis

## Integration Boundaries

### What YOLO Controls
- **MCP Protocol Compliance**: Tool definitions, async handling, error responses
- **File Operations**: Asset management, path resolution, cleanup
- **Workflow Coordination**: Orchestrating external processing steps
- **Client Communication**: MCP server lifecycle and tool routing

### What External Systems Control
- **Video Processing**: Komposteur handles beat-sync, VideoRenderer handles effects
- **FFmpeg Execution**: External systems manage FFmpeg command construction
- **Audio Analysis**: Specialized libraries for beat detection and audio processing
- **CI/Build Systems**: GitHub Actions, Docker builds, dependency management

## Anti-Patterns (Lessons Learned)

### ❌ Over-Engineering Indicators
- **Same Error Persisting**: Multiple attempts with different approaches
- **Architectural Drift**: Simple fixes requiring tech stack changes
- **Solution >> Problem**: 50+ line fixes for single error messages

### ✅ Healthy Development Patterns  
- **Progressive Error Resolution**: Each fix reveals new, more specific errors
- **BD-First Analysis**: Environment comparison before code changes
- **Optional Dependencies**: Graceful degradation (e.g., docker import)

## Current State & Known Issues

### Working Well
- **MCP Integration**: Stable protocol compliance and tool routing
- **External JAR Communication**: Reliable subprocess management
- **File Management**: Deterministic IDs and path resolution
- **Build Detective**: Effective CI failure analysis

### Active Uncertainties
- **Integration Complexity**: Managing multiple external dependencies
- **Performance**: Large video processing workflows
- **Error Recovery**: Graceful handling of external system failures

### Technical Debt
- **Documentation Scattered**: Multiple overlapping documentation files  
- **Error Handling**: Inconsistent patterns across modules
- **Test Coverage**: Limited integration testing with external JARs

## Agent Workflow Context
*Specialized agents should read this section for domain awareness*

### modular-architect Focus
- **Respect External Boundaries**: Don't duplicate Komposteur/VideoRenderer functionality
- **MCP Compliance**: Maintain tool definitions and async patterns
- **File Management**: Consider registry and path management patterns

### reviewer-readonly Focus  
- **Integration Safety**: Changes shouldn't break JAR communication
- **MCP Protocol**: Verify tool definitions remain valid
- **Async Correctness**: Proper await usage in tool implementations

---
*Update this file when major architectural changes occur. Keep it as the single source of truth for project understanding.*