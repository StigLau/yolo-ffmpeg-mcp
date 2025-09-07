# Komposteur MCP Server - TypeScript Implementation

This is a TypeScript MCP server that wraps the Komposteur uberjar to provide LLMs with intelligent music video creation capabilities through YouTube downloads, S3 integration, and kompost.json file processing.

## What This Project Does

**Primary Mission**: Provide LLMs with seamless access to Komposteur's music video creation pipeline through a clean, cost-effective TypeScript MCP interface.

**Core Value Proposition**:
- **Seamless Integration**: Native TypeScript MCP server for maximum LLM compatibility
- **Komposteur Wrapper**: Direct access to kompost.json processing, YouTube downloads, S3 operations
- **Cost-Optimized**: Lean implementation focused on essential functionality
- **Development-First**: Built for rapid prototyping and testing workflows

## Architecture Overview

### MCP Server Design
**Philosophy**: Thin TypeScript wrapper around battle-tested Java Komposteur uberjar.

- **MCP Layer**: TypeScript server handling LLM communication protocols
- **JAR Integration**: Direct subprocess calls to Komposteur uberjar functionality
- **File Management**: Structured handling of kompost.json, media files, S3 assets
- **Error Handling**: Graceful degradation with meaningful error responses to LLMs

### Core Functionality Areas

1. **YouTube Download Integration**
   - Wrapper around Komposteur's YouTube download capabilities
   - Metadata extraction and file management
   - Quality/format selection automation

2. **S3 Operations**
   - Upload/download of media files via Komposteur
   - Asset management for music video creation
   - Efficient caching and storage strategies

3. **Kompost.json Processing**
   - JSON file validation and processing
   - Music video composition orchestration
   - Beat synchronization and timing management

## ⚠️ **ZERO ROOT DIRECTORY POLLUTION PROTOCOL** ⚠️

**CRITICAL RULE**: AI-generated files MUST NEVER appear in project root.

**Directory Structure Standards**:
```
komposteur-mcp-ts/
├── src/
│   ├── main/ts/           # Core TypeScript implementation
│   │   ├── server/        # MCP server implementation
│   │   ├── komposteur/    # Komposteur wrapper logic
│   │   └── types/         # TypeScript definitions
│   └── test/ts/           # Test suites
├── docs/                  # Documentation and guides
├── scripts/               # Build and deployment scripts
├── generated/             # ALL AI-generated content goes here
│   ├── media/            # Downloaded/processed media files
│   ├── kompost-files/    # Generated kompost.json files
│   └── temp/             # Processing temporary files
└── examples/             # Usage examples and templates
```

**File Value Classification**:
- **Keep**: Source code (`src/`), essential configs, documentation, tests
- **Generated**: All AI content goes to `generated/` subdirectories
- **Never Stage**: Timestamped files, logs, large binaries, `node_modules/`

## Developer Interaction Preferences

### Communication Style
- **Concise Responses**: Minimize token usage, answer directly
- **Senior Developer Context**: Assume deep technical knowledge
- **Ask When Uncertain**: Better to clarify than implement incorrectly
- **3-Line Rule**: If fix is likely <10 lines, analyze more than implement

### Development Philosophy
- **Lean and Focused**: Avoid feature creep, stick to core functionality
- **Test-First**: Basic validation before expanding features
- **Question Architectural Changes**: No major changes without explicit approval
- **File Organization**: Group similar files logically, use clear naming

### Anti-Patterns to Avoid
- **Root Directory Clutter**: All generated content goes to structured folders
- **Over-Engineering**: Start simple, expand only when needed
- **Assumption-Driven Development**: Ask instead of guessing requirements
- **Token Waste**: Efficient, targeted responses unless detail explicitly requested

## Technical Implementation Strategy

### Komposteur Integration Approach
**Local Development**: Use latest JARs from `~/.m2/repository/` for fast iteration
**Production**: GitHub Packages with proper version control
**JAR Execution**: Subprocess calls with proper error handling and logging

### MCP Server Implementation
**Tool Registration**: Register essential Komposteur operations as MCP tools
**Error Handling**: Meaningful error responses that guide LLM behavior
**Type Safety**: Full TypeScript typing for all interfaces and data structures

### File Management Strategy
**Input Processing**: Validate kompost.json files before JAR execution
**Output Handling**: Structured storage of generated media and metadata
**Cleanup Protocols**: Automatic cleanup of temporary files and failed operations

## Project Scope and Constraints

### Core Feature Set (MVP)
1. **YouTube Download Tool**: Download videos via Komposteur JAR
2. **Kompost.json Processor**: Parse and execute kompost compositions
3. **S3 Integration Tool**: Upload/download media files
4. **Status Monitoring**: Check processing status and results

### Explicitly Out of Scope
- **Video Processing Logic**: Komposteur JAR handles all FFmpeg operations
- **Beat Detection**: Komposteur provides music synchronization
- **Advanced UI**: This is a backend MCP server only
- **Custom Video Effects**: Use Komposteur's built-in capabilities

### Future Enhancement Areas
- **Cost Tracking**: Integration with budget monitoring systems
- **Batch Processing**: Multiple video processing workflows
- **Advanced S3 Features**: More sophisticated asset management
- **Performance Optimization**: Caching and pipeline improvements

## Build and Deployment

### Development Workflow
```bash
# Initial setup
npm install

# Development with hot reload
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint and format
npm run lint
```

### CI/CD Integration
- **Local CI**: Run tests and linting before commit
- **Build Validation**: Ensure TypeScript compilation success
- **JAR Availability**: Verify Komposteur JAR accessibility
- **Integration Tests**: Basic MCP server functionality validation

## Error Handling and Monitoring

### Graceful Degradation
- **JAR Unavailable**: Clear error messages to LLM about missing dependencies
- **Network Issues**: Retry logic for S3 and YouTube operations
- **Malformed Input**: Validation with helpful correction suggestions
- **Resource Limits**: Memory and disk space monitoring

### Logging Strategy
- **Development**: Verbose logging for debugging
- **Production**: Structured JSON logs for monitoring
- **Error Context**: Include sufficient context for troubleshooting
- **Performance Metrics**: Track operation timing and success rates

## Integration with Existing Ecosystem

### YOLO-FFMPEG-MCP Coordination
- **Complementary Roles**: YOLO handles video processing, this handles Komposteur workflow
- **Shared Standards**: Common file organization and error handling patterns
- **Interoperability**: Compatible data formats and communication protocols

### Learning from Existing Implementations
- **FastTrack Integration**: Learn from cost-optimization strategies
- **Build Detective Patterns**: Apply CI/CD validation approaches
- **File Management**: Follow established directory organization principles

## Success Criteria

### Technical Metrics
- **LLM Integration**: Seamless communication via MCP protocol
- **Reliability**: >95% success rate for core operations
- **Performance**: <2s response time for status/validation operations
- **Maintainability**: Clear code structure enabling easy modifications

### User Experience Goals
- **Intuitive Interface**: LLMs can easily discover and use available tools
- **Clear Error Messages**: Actionable feedback when operations fail
- **Predictable Behavior**: Consistent responses across different usage patterns
- **Minimal Cognitive Load**: Simple, focused feature set

---

## Development Guidelines

### When Starting Work
1. **Read this CLAUDE.md** to understand project context and constraints
2. **Check existing structure** before creating new files or directories
3. **Ask questions** when uncertain about implementation approaches
4. **Start minimal** - implement core functionality before adding features

### File Creation Protocol
- **All generated content** goes to `generated/` subdirectories
- **Source code** follows `src/main/ts/` and `src/test/ts/` structure
- **Documentation** goes to `docs/` with clear categorization
- **Scripts and tools** go to `scripts/` directory

### Quality Standards
- **TypeScript First**: Full type safety, no `any` types without justification
- **Error Handling**: Every operation should have appropriate error handling
- **Documentation**: Code should be self-documenting with clear naming
- **Testing**: Core functionality should have basic test coverage

### Constraints and Boundaries
- **No Architectural Changes** without explicit permission
- **Komposteur JAR** is the authoritative implementation for music video logic
- **MCP Protocol** compliance is non-negotiable
- **File Organization** rules are strict and must be followed

This project exists to make Komposteur's capabilities easily accessible to LLMs through a clean, efficient TypeScript interface. Keep it simple, focused, and maintainable.