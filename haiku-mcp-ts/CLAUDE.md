# Haiku MCP Server - AI-Optimized Video Processing Package

## Mission Statement
**Primary Goal**: Provide cost-effective, intelligent video processing as a reusable NPM/Bun package via GitHub Packages, enabling seamless integration across multiple projects while maintaining enterprise-grade reliability.

**Core Value Proposition**:
- **99.7% Cost Reduction**: $0.02 Haiku analysis vs $125+ manual video decisions
- **Dual LLM Redundancy**: Anthropic Haiku primary + Gemini Flash fallback  
- **Enterprise Ready**: GitHub Packages distribution with full TypeScript support
- **8 Production Tools**: Complete MCP server functionality in packageable form

## Package Identity & Scope
- **Package Name**: `@kompo/haiku-mcp-server`
- **Target Consumers**: yolo-ffmpeg-mcp, kompo.ai, future video processing projects
- **Distribution**: GitHub Packages (private, internal use)
- **Runtime**: Node.js 18+ or Bun 1.0+ with ffmpeg/yt-dlp system dependencies

## Technical Architecture

### Core Components (DO NOT MODIFY WITHOUT CONSULTATION)
- **MCP Protocol**: @modelcontextprotocol/sdk - industry standard
- **LLM Integration**: Dual provider architecture (Anthropic + Google)  
- **Video Processing**: Direct ffmpeg command generation (no fluent-ffmpeg)
- **File Registry**: ID-based asset management with metadata
- **Configuration**: YAML-based config with env override capability

### Package Export Strategy
```typescript
// Primary exports - high-level usage
export { HaikuMCPServer, createHaikuServer }

// Component exports - custom implementations  
export { VideoProcessor, YouTubeDownloader, FileManager }
export { HaikuClient, GeminiFlashClient }

// Type exports - TypeScript support
export type { BaseLLMClient, VideoProcessRequest, HaikuConfig }
```

## ⚠️ MANDATORY CONSULTATION RULES ⚠️

**CRITICAL**: Always consult before ANY architectural changes.

**NEVER** change core dependencies without explicit permission:
- **MCP SDK Version**: Locked to tested compatibility
- **LLM SDKs**: Version coordination with parent projects required
- **Build System**: Bun-first approach, npm fallback if needed
- **Module System**: ES modules required for MCP compatibility

**Root Cause Analysis Protocol**:
1. Check if issue exists in parent yolo-ffmpeg-mcp first
2. Test with both Bun and npm to isolate package manager issues
3. Verify MCP protocol compliance before implementation changes
4. If fix requires >5 lines, PAUSE and document approach

## Consumer Integration Patterns

### Pattern 1: Direct Server (Most Common)
```typescript
import { HaikuMCPServer } from '@kompo/haiku-mcp-server';
const server = new HaikuMCPServer();
await server.initialize();
await server.run(); // stdio transport
```

### Pattern 2: HTTP Wrapper Integration
```typescript
import { createHaikuServer } from '@kompo/haiku-mcp-server';
const server = await createHaikuServer({
  llm: { primary: 'anthropic' },
  ffmpeg: { outputDir: '/tmp/videos' }
});
```

### Pattern 3: Custom Component Usage
```typescript  
import { VideoProcessor, HaikuClient } from '@kompo/haiku-mcp-server/lib';
const processor = new VideoProcessor(llmClient, ffmpegConfig);
```

## Development vs Production Strategy

**Package Distribution**:
- **Development**: Local bun link for rapid iteration
- **Production**: GitHub Packages with semantic versioning
- **Testing**: Comprehensive test suite before any publish

**Environment Configuration**:
- **Required**: ANTHROPIC_API_KEY  
- **Optional**: GEMINI_API_KEY (fallback), HAIKU_MCP_* config overrides
- **Validation**: Runtime key validation with clear error messages

## ⚠️ **PARENT PROJECT COORDINATION** ⚠️

### **Relationship Management**

**YOLO-FFMPEG-MCP** (Master Orchestrator):
- **Role**: Uses haiku-mcp-server as subprocess/package
- **Coordination**: Shares ffmpeg strategies and file registry patterns
- **Updates**: Breaking changes require YOLO compatibility testing

**KOMPO.AI** (Primary Consumer):  
- **Role**: HTTP wrapper around haiku-mcp-server package
- **Requirements**: All 8 MCP tools operational via HTTP API
- **Performance**: <2s startup, realistic memory baseline

### **Version Coordination Protocol**
```bash
# Before any breaking change:
1. Test with yolo-ffmpeg-mcp integration
2. Verify kompo.ai HTTP wrapper compatibility  
3. Update CHANGELOG.md with consumer impact notes
4. Coordinate release timing across projects
```

### **Shared Learning Integration**
- **FastTrack Insights**: Video analysis learnings flow back to yolo-ffmpeg-mcp
- **Cost Optimization**: Token usage patterns shared with parent projects
- **Error Patterns**: Failed processing cases documented for ecosystem improvement

## Quality Assurance Standards

### **CI/CD Requirements**
```bash
# Local validation before publish:
bun test                    # Unit test suite
bun run build              # TypeScript compilation  
bun run lint               # Code quality checks
bun run package            # Full package validation
```

### **Performance Benchmarks** 
- **Startup Time**: <2 seconds cold start
- **Memory Usage**: Realistic baseline (video processing context)
- **Response Time**: <5 seconds for video operations
- **Success Rate**: >95% for core MCP tools

### **Consumer Testing Protocol**
- **Integration Tests**: Verify all 8 MCP tools via stdio transport
- **HTTP Wrapper**: Test via kompo.ai integration pattern
- **Error Scenarios**: Validate graceful degradation patterns

## Publishing & Distribution

### **GitHub Packages CI/CD**
- **Registry**: `npm.pkg.github.com`
- **Scope**: `@kompo` organization
- **Authentication**: GitHub token via NODE_AUTH_TOKEN
- **Publishing Triggers**:
  - **Beta**: Push to feature/standalone-haiku-mcp-server branch
  - **Release**: GitHub release creation
  - **Manual**: Commit message containing `[publish]`

### **Version Strategy**
- **Beta Releases**: Auto-timestamped beta versions for testing
- **Semantic Versioning**: 1.0.0+ for stable releases
- **Dual Runtime**: Tested with both Bun and npm for compatibility

### **Package Structure**
```
dist/
├── index.js                 # Main entry point
├── index.d.ts              # TypeScript definitions
├── server.js               # Direct server usage
├── factory.js              # Factory functions
└── lib/                    # Component library
    ├── tools/              # Video processing tools
    ├── llm/               # LLM clients
    └── registry/          # File management
```

## Resistance Strategy Against Over-Engineering

### **KOMPO.AI Push-Back Points**
- **❌ NO fluent-ffmpeg**: Keep LLM-direct command generation for maximum intelligence
- **❌ NO Lambda optimization**: Focus on container deployment, not serverless complexity
- **❌ NO HTTP server embedding**: Clean MCP interface only, HTTP concerns belong in consumer
- **❌ NO unrealistic memory constraints**: Set realistic targets based on video processing requirements

### **Core Principle Maintenance**
- **LLM-Driven Intelligence**: Direct ffmpeg command generation via AI analysis
- **Clean Separation**: MCP protocol compliance without HTTP/REST concerns
- **Performance Realism**: Benchmarks based on actual video processing workloads
- **Dual Provider Reliability**: Anthropic primary + Google fallback for resilience

## Success Metrics & Monitoring

**Package Success Indicators**:
- **Consumer Adoption**: Successfully integrated by 2+ projects (yolo-ffmpeg-mcp + kompo.ai)
- **Version Stability**: <5% breaking changes per quarter
- **Performance**: Meets all benchmark requirements consistently
- **Developer Experience**: Positive feedback from consumer project teams

**Warning Indicators**:
- **Integration Failures**: Consumer projects struggling with updates
- **Performance Regression**: Benchmarks falling below requirements
- **Version Conflicts**: Dependency mismatches with parent projects
- **Documentation Gaps**: Consumer teams requesting missing usage patterns

## Implementation Status

### **Completed**
- ✅ Package structure and export strategy
- ✅ Factory functions for custom configuration
- ✅ GitHub Packages CI/CD pipeline
- ✅ Dual runtime support (Bun + npm)
- ✅ TypeScript definitions and build process

### **Next Steps**
1. **Complete server configuration integration** (factory function support)
2. **Test package build and publishing** locally
3. **Create comprehensive README** for consumer documentation
4. **Validate MCP protocol compliance** with existing tools
5. **Test integration** with yolo-ffmpeg-mcp parent project

This CLAUDE.md ensures the standalone haiku-mcp-server maintains its role as a reliable, high-performance package while coordinating effectively with its parent and consumer projects, resisting unnecessary complexity while delivering proven video processing intelligence.