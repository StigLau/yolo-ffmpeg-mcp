# Cloud Music Video Creator - AI-Powered Komposition System

**Mission**: Create a production-ready Cloud Run service that empowers users to create professional music videos through AI-guided komposition workflows.

## What This System Does

**Core Value**: Transform music video creation from complex technical workflows into intuitive creative conversations, backed by proven AI analysis and processing intelligence.

**User Journey**:
1. **Create**: User describes their music video vision through natural language
2. **Compose**: System generates structured komposition with beat-synchronized segments
3. **Refine**: User iterates on komposition through conversational interface
4. **Produce**: System creates final video using cost-optimized AI pipeline
5. **Persist**: Kompositions and outputs are managed across sessions

## System Architecture

### Three-Tier LLM Architecture

**Tier 1: User-Facing LLM (Gemini Pro 2.5)**
- **Role**: Creative partner and conversation orchestrator
- **Responsibilities**: 
  - Natural language understanding of user creative intent
  - Komposition conceptualization and refinement
  - User experience and creative guidance
  - High-level workflow orchestration
- **Configuration**: Swappable via deployment config (Gemini/Claude/OpenAI)

**Tier 2: MCP Server Layer**
- **Role**: Tool and capability bridge
- **Responsibilities**:
  - Registry operations (komposition CRUD, file management)
  - Video processing orchestration
  - Resource management and coordination
  - State management across user sessions

**Tier 3: Processing LLM (Gemini Flash/Haiku)**
- **Role**: Technical execution specialist
- **Responsibilities**:
  - FFmpeg command generation and optimization
  - Video analysis and strategy selection
  - Beat synchronization calculations
  - Technical validation and error recovery
- **Configuration**: Swappable via deployment config (Flash/Haiku/Claude/GPT-4o-mini)

### Component Architecture

```
┌─────────────────────────────────────────┐
│           User Interface                │
│        (Web/API Frontend)               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Gemini Pro 2.5 LLM               │
│    (Creative & Orchestration)           │
└─────────────────┬───────────────────────┘
                  │ MCP Protocol
┌─────────────────▼───────────────────────┐
│          MCP Server Layer               │
│  ┌─────────────┬─────────────┬─────────┐ │
│  │  Registry   │ Komposition │ Storage │ │
│  │  Manager    │ Processor   │ Manager │ │
│  └─────────────┴─────────────┴─────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     Processing LLM (Flash/Haiku)        │
│     (FFmpeg & Technical Operations)     │
└─────────────────────────────────────────┘
```

## Development Principles

### From YOLO-FFMPEG-MCP Learnings

**✅ Adopt These Proven Patterns:**
- **FastTrack Cost Analysis**: $0.02-0.05 per operation vs $125 manual
- **Hierarchical Agent Architecture**: Master orchestrator with specialist subagents
- **Progressive Error Resolution**: Each fix should reveal new, more specific errors
- **File Organization Discipline**: Zero root pollution, structured temp directories
- **Build Detective Integration**: Pre-commit validation and failure analysis

**❌ Avoid These Anti-Patterns:**
- **LLM Over-Engineering**: "3-Line Rule" - analyze more than implement
- **Root Directory Pollution**: All generated files go to designated temp areas
- **Same-Error Recursion**: Compare environments before architectural changes
- **Git Submodules**: Use proper dependency management instead

### Cloud Run Specific Guidelines

**Stateless Design Requirements**:
- **No Persistent Local Storage**: Use temp directories that clean up after requests
- **Session State Management**: External storage for komposition state across requests
- **Cold Start Optimization**: Pre-warm critical components (FastTrack analysis)
- **Resource Limits**: Container-aware processing with appropriate timeouts

**Cost Optimization Strategy**:
- **LLM Tier Selection**: Route to cheapest capable model
- **Batch Processing**: Group operations when possible
- **Caching Strategy**: Intelligent caching of analysis and intermediate results
- **Budget Controls**: Daily/monthly limits with graceful degradation

## Directory Structure

```
cloud-music-video-creator/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── llm/              # LLM integration (Gemini Pro/Flash)
│   ├── mcp/              # MCP server implementation
│   ├── models/           # Data models and schemas
│   ├── services/         # Business logic services
│   ├── registry/         # Komposition and file registry
│   ├── komposition/      # Komposition processing logic
│   ├── storage/          # Storage abstraction layer
│   └── utils/            # Shared utilities
├── docs/                 # System documentation
├── tests/                # Test suites
├── examples/             # Example kompositions and workflows
├── config/               # Configuration files
├── deployment/           # Cloud Run deployment configs
├── scripts/              # Development and deployment scripts
└── static/               # Static assets (if needed)
```

## Data Models

### Core Entities

**Komposition**:
- Structured representation of a music video (JSON format from YOLO learnings)
- Beat-synchronized segments with visual effects
- Audio/video source references
- Processing metadata and quality scores

**User Session**:
- Current komposition being worked on
- Conversation context (without storing full conversation)
- Processing state and intermediate results

**Media Registry**:
- File metadata and location references (temp/cloud storage)
- Processing status and quality metrics
- Access patterns and cleanup policies
- **Note**: Current design works with temp storage; AWS/Google Cloud integration planned for future phase

## Development Workflow

### Key Questions to Answer During Development

1. **Storage Abstraction**: Design registry interface that works with both temp files and future cloud storage
2. **Session Management**: How to maintain context across stateless requests without storing full conversations
3. **Error Recovery**: How to gracefully handle LLM failures and provide fallback options
4. **Scalability**: How to handle multiple concurrent users and komposition processing
5. **Testing Strategy**: How to test multi-LLM workflows without excessive API costs

### Implementation Phases

**Phase 1**: Core MCP server with komposition processing
**Phase 2**: User-facing LLM integration with basic UI
**Phase 3**: Registry system with temp storage
**Phase 4**: Cloud Run deployment and optimization
**Phase 5**: Advanced features and cloud storage integration

## Quality Assurance

### From YOLO Testing Learnings
- **Integration Tests**: Real workflow validation with example kompositions
- **Cost Monitoring**: Track LLM usage and processing costs in tests
- **Error Simulation**: Test fallback behaviors when LLMs fail
- **Performance Baselines**: Measure processing times and resource usage

### Production Readiness Checklist
- [ ] Multi-LLM integration working reliably
- [ ] MCP server provides all required tools
- [ ] Registry system handles file lifecycle properly
- [ ] Cloud Run deployment configuration complete
- [ ] Error handling and fallback systems tested
- [ ] Cost controls and monitoring implemented
- [ ] User interface provides intuitive creative workflow

## Technical Standards

### Code Quality
- **Type Hints**: Full Python typing for better IDE support and error detection
- **Documentation**: Docstrings for all public interfaces
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: Structured logging for debugging and monitoring

### Architecture Constraints
- **Single Responsibility**: Each component has clear, focused purpose
- **Dependency Injection**: Testable, configurable component relationships
- **Configuration Management**: Environment-based configuration for different deployments
- **API Versioning**: Future-proof API design for evolution

---

**Remember**: This is a production system for real users. Every design decision should prioritize user experience, cost efficiency, and maintainability over cleverness or complexity.