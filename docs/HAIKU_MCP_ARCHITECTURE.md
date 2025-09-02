# Haiku MCP Server Architecture

## Executive Summary

Design for a **cost-optimized MCP server** that wraps small, efficient LLMs (Haiku, Gemini Flash 2.0) to handle FFMPEG operations. This addresses token efficiency problems identified in the current YOLO-FFMPEG-MCP by using cheaper models for technical operations.

## Current Problems (YOLO-FFMPEG-MCP)

### Token Waste Issues
- **Verbose FFMPEG Logs**: 2000+ character responses for simple operations ($0.03 per operation)
- **YouTube Download Explosion**: 27,838 token responses exceeding limits
- **Parameter Inconsistencies**: Failed operations requiring expensive retries
- **Hanging Operations**: analyze_video_content burning tokens indefinitely

### Cost Analysis
- **Current**: Sonnet processing FFMPEG logs ($0.075 per operation)  
- **Target**: Haiku technical processing ($0.001 per operation) - **75x cost reduction**

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Claude Sonnet (User Interface)              │
│                                                             │
│  "Create music video with YouTube song and effects"        │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Haiku MCP Server (NEW)                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           MCP Tool Registry                             │ │
│  │  • create_music_video                                   │ │
│  │  • download_youtube_video                               │ │
│  │  • process_video_file                                   │ │
│  │  • batch_operations                                     │ │
│  └─────────────────────┬───────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────────┐ │
│  │         LLM Abstraction Layer                           │ │
│  │                                                         │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │ │
│  │  │   Haiku     │ │ Gemini      │ │    Other LLM    │   │ │
│  │  │   $0.25/1M  │ │ Flash 2.0   │ │   (Pluggable)   │   │ │
│  │  │   tokens    │ │ $0.075/1M   │ │                 │   │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │ │
│  └─────────────────────┬───────────────────────────────────┘ │
│                        │                                     │
│  ┌─────────────────────▼───────────────────────────────────┐ │
│  │           Technical Execution Layer                     │ │
│  │                                                         │ │
│  │  • FFMPEG Command Generation & Execution               │ │
│  │  • YouTube Download Management                          │ │
│  │  • File Registry & Path Management                     │ │
│  │  • Response Sanitization (Remove Logs)                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Design Principles

### 1. **LLM-First Architecture**
- **Small LLM Specialization**: Use cheap models for technical tasks
- **Response Sanitization**: Strip verbose logs before returning to user
- **Token Optimization**: Minimize tokens in/out at every layer
- **Configurable Models**: Hot-swappable LLM backends

### 2. **Cost Optimization**
- **75x Cost Reduction**: $0.075 → $0.001 per operation
- **Batch Processing**: Group operations to reduce API calls
- **Response Caching**: Cache common FFMPEG patterns
- **Smart Fallbacks**: Degrade gracefully on model failures

### 3. **Pragmatic Implementation**
- **Working > Perfect**: Get basic operations solid first
- **Iterative Enhancement**: Start with core tools, expand gradually  
- **No Over-Engineering**: Avoid complex patterns until proven necessary
- **Clear Boundaries**: Separate LLM logic from FFMPEG execution

## Component Architecture

### 1. MCP Server Core (`server.py`)
```python
class HaikuMCPServer:
    def __init__(self, config: ServerConfig):
        self.llm_client = LLMClientFactory.create(config.llm_provider)
        self.tool_registry = ToolRegistry()
        self.response_sanitizer = ResponseSanitizer()
    
    async def handle_tool_call(self, tool_name: str, params: dict):
        # 1. Route to LLM with sanitized prompt
        # 2. Execute technical operations
        # 3. Sanitize response (remove logs)
        # 4. Return minimal response
```

**Key Features:**
- **Tool Registration**: Dynamic tool discovery
- **Request Routing**: Smart routing to appropriate LLM
- **Response Sanitization**: Remove verbose logs/metadata
- **Error Handling**: Graceful degradation on LLM failures

### 2. LLM Abstraction Layer (`llm_clients/`)
```python
class BaseLLMClient:
    async def process_request(self, prompt: str, context: dict) -> LLMResponse:
        pass

class HaikuClient(BaseLLMClient):
    # Optimized for technical operations
    # Cost: $0.25/1M tokens
    
class GeminiFlashClient(BaseLLMClient):
    # Alternative cost-effective model  
    # Cost: $0.075/1M tokens
```

**Configuration-Driven Selection:**
```yaml
llm_config:
  primary: haiku
  fallback: gemini_flash
  models:
    haiku:
      api_key: ${ANTHROPIC_API_KEY}
      model: claude-3-haiku-20240307
    gemini_flash:
      api_key: ${GOOGLE_AI_KEY}
      model: gemini-2.0-flash
```

### 3. Technical Execution Layer (`execution/`)
```python
class FFMPEGExecutor:
    async def execute_command(self, command: str) -> ExecutionResult:
        # Execute FFMPEG with timeout protection
        # Capture minimal success/failure info
        # Strip verbose logs before returning
        
class YouTubeDownloader:
    async def download_video(self, url: str, options: dict) -> DownloadResult:
        # Use yt-dlp with progress tracking
        # Return file info, not massive metadata dump
```

**Response Sanitization:**
- **FFMPEG Logs**: Keep only success/failure + duration
- **Download Metadata**: Return file_id, title, duration - skip format arrays
- **Error Messages**: Concise error description, not full stack traces

### 4. File Management (`file_registry/`)
```python
class FileRegistry:
    def register_file(self, path: str) -> FileID:
        # Generate deterministic file IDs
        # Store minimal metadata
        # Efficient file discovery
```

## Tool Implementation Strategy

### Phase 1: Core Operations
```python
@mcp_tool
async def create_music_video(description: str, duration: Optional[int]) -> VideoResult:
    """Single atomic operation for music video creation"""
    
@mcp_tool  
async def download_youtube_audio(url: str) -> AudioFile:
    """Download audio with sanitized response"""
    
@mcp_tool
async def process_video_file(file_id: str, operation: str, params: dict) -> VideoResult:
    """Basic video processing operations"""
```

### Phase 2: Advanced Features
```python
@mcp_tool
async def batch_video_operations(operations: List[Operation]) -> BatchResult:
    """Efficient batch processing"""
    
@mcp_tool
async def analyze_video_content(file_id: str) -> ContentAnalysis:
    """AI-powered content analysis (fixed timeout)"""
```

## Configuration Management

### Server Configuration (`config.yaml`)
```yaml
server:
  name: "haiku-ffmpeg-mcp"
  version: "1.0.0"
  port: 3001

llm:
  primary: "haiku"
  fallback: "gemini_flash"
  timeout_seconds: 30
  max_retries: 2

ffmpeg:
  timeout_seconds: 120
  temp_directory: "/tmp/haiku-mcp"
  cleanup_on_exit: true

logging:
  level: "INFO"
  include_ffmpeg_logs: false
  sanitize_responses: true

response_limits:
  max_tokens: 1000
  strip_metadata: true
  include_performance_stats: false
```

## Implementation Phases

### Phase 1: MVP (Week 1)
- **Basic MCP Server**: Tool registration, request handling
- **Haiku Integration**: Single LLM client with basic operations
- **Core Tools**: create_music_video, download_youtube_audio, process_video_file
- **Response Sanitization**: Remove FFMPEG logs, limit response size

### Phase 2: Multi-LLM Support (Week 2)
- **LLM Abstraction**: Pluggable LLM clients
- **Gemini Flash Integration**: Alternative cost-effective model
- **Configuration Management**: YAML-based model selection
- **Fallback Logic**: Graceful degradation on model failures

### Phase 3: Advanced Features (Week 3)
- **Batch Operations**: Efficient multi-operation processing
- **Caching Layer**: Cache common FFMPEG patterns
- **Performance Monitoring**: Track token usage and costs
- **Advanced Tools**: Video analysis, content intelligence

## Success Metrics

### Cost Efficiency
- **Target**: 75x cost reduction vs current YOLO-MCP
- **Measurement**: Track $/operation across different model configurations
- **Goal**: <$0.01 per typical music video creation

### Response Quality
- **Response Size**: <1000 tokens per operation (vs 25k+ currently)
- **Success Rate**: >95% successful operations
- **Response Time**: <10s for typical operations

### User Experience
- **Tool Compatibility**: Drop-in replacement for YOLO-MCP tools
- **Error Clarity**: Clear, actionable error messages
- **Operation Reliability**: No hanging operations, proper timeouts

## Integration Testing

### Test Against Current YOLO-MCP
```python
# Same user prompts, compare:
# 1. Cost per operation
# 2. Response quality
# 3. Success rates
# 4. Response times

async def test_music_video_creation():
    yolo_result = await yolo_mcp.create_music_video("Create beat-sync video")
    haiku_result = await haiku_mcp.create_music_video("Create beat-sync video")
    
    compare_results(yolo_result, haiku_result)
```

### Compatibility Validation
- **Tool Signatures**: Identical input/output formats
- **File Registry**: Compatible file ID system  
- **Error Handling**: Consistent error response format
- **Performance**: Faster execution with lower cost

## Future Enhancements

### Advanced LLM Features
- **Multi-Model Routing**: Route different operations to optimal models
- **Adaptive Configuration**: Auto-tune model selection based on performance
- **Custom Fine-Tuning**: Fine-tune models for specific FFMPEG patterns

### Integration Ecosystem
- **Komposteur Integration**: Seamless beat-sync video processing
- **VideoRenderer Bridge**: Leverage existing optimizations
- **Build Detective**: Enhanced CI analysis with cost-effective models

This architecture provides a **cost-optimized, LLM-wrapped MCP server** that solves the token efficiency problems while maintaining compatibility with existing workflows.