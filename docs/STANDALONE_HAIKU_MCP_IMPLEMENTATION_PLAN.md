# Standalone Haiku MCP Server Implementation Plan

## Overview

This document outlines the implementation plan for extracting the Haiku MCP TypeScript project into a standalone, reusable NPM/Bun package distributed via GitHub Packages.

## Background

**Current State**: The Haiku MCP server exists in `/workspace/yolo-ffmpeg-mcp/haiku-mcp-ts/` but is tightly coupled to this project structure.

**Target State**: A standalone `@kompo/haiku-mcp-server` package that can be consumed by multiple projects (yolo-ffmpeg-mcp, kompo.ai, and future projects).

## Implementation Strategy

### Phase 1: Repository Preparation

#### 1.1 Standalone Directory Structure
```
haiku-mcp-ts/                       # Enhanced existing directory
├── src/
│   ├── index.ts                    # NEW: Package entry point
│   ├── factory.ts                  # NEW: Server factory functions
│   ├── server.ts                   # EXISTING: Core MCP server
│   ├── llm/                        # EXISTING: LLM implementations
│   ├── tools/                      # EXISTING: Video processing tools
│   ├── registry/                   # EXISTING: File management
│   └── config.ts                   # EXISTING: Configuration
├── examples/                       # NEW: Usage examples
├── CLAUDE.md                       # NEW: AI agent instructions
├── package.json                    # UPDATED: Bun + GitHub Packages
├── bun.lockb                      # NEW: Bun lockfile (when generated)
└── README.md                      # UPDATED: Standalone documentation
```

#### 1.2 Key Architectural Decisions

**✅ KEEP (Proven Components)**:
- All 8 existing MCP tools (create_music_video, process_video_file, etc.)
- Dual LLM architecture (Anthropic Haiku + Gemini Flash)
- Direct ffmpeg command generation via LLM (no fluent-ffmpeg abstraction)
- File registry system with ID-based access
- YAML configuration with environment override
- TypeScript ES module architecture

**❌ RESIST (Kompo.ai Over-Engineering)**:
- Fluent-ffmpeg dependency (reduces AI flexibility)
- AWS Lambda optimization (adds unnecessary complexity)
- HTTP server embedding (violates separation of concerns)
- Unrealistic memory constraints (<200MB with video processing)

**➕ ADD (Packaging Requirements)**:
- Package entry points for different usage patterns
- Factory functions for custom configuration
- Comprehensive TypeScript exports
- Dual package manager support (bun preferred, npm fallback)

### Phase 2: Package Interface Design

#### 2.1 Export Strategy
```typescript
// src/index.ts - Main package entry point
export { HaikuMCPServer } from './server.js';
export { createHaikuServer, createCustomServer } from './factory.js';

// Individual components for custom implementations
export { VideoProcessor } from './tools/video-processor.js';
export { YouTubeDownloader } from './tools/youtube-downloader.js';
export { FileManager } from './registry/file-manager.js';
export { HaikuClient } from './llm/haiku-client.js';
export { GeminiFlashClient } from './llm/gemini-client.js';

// Type exports for TypeScript consumers
export type { BaseLLMClient } from './llm/types.js';
export type { VideoProcessRequest } from './tools/video-processor.js';
export type { HaikuConfig } from './config.js';
```

#### 2.2 Usage Patterns Support

**Pattern 1: Direct Server Usage (Most Common)**
```typescript
import { HaikuMCPServer } from '@kompo/haiku-mcp-server';
const server = new HaikuMCPServer();
await server.initialize();
await server.run(); // stdio transport
```

**Pattern 2: Custom Configuration**
```typescript
import { createHaikuServer } from '@kompo/haiku-mcp-server';
const server = await createHaikuServer({
  llm: { primary: 'anthropic', fallback: 'gemini' },
  ffmpeg: { outputDir: '/tmp/kompo/videos' },
  registry: { cacheDir: '/tmp/kompo/registry' }
});
```

**Pattern 3: Component-Level Usage**
```typescript
import { VideoProcessor, HaikuClient } from '@kompo/haiku-mcp-server/lib';
const client = new HaikuClient(config);
const processor = new VideoProcessor(client, ffmpegConfig);
```

### Phase 3: Bun Migration Strategy

#### 3.1 Conservative Migration Approach
- **Phase 3.1**: Add bun support while maintaining npm compatibility
- **Phase 3.2**: Optimize for bun-native features (TypeScript, testing)
- **Phase 3.3**: Full bun optimization while preserving npm fallback

#### 3.2 package.json Updates
```json
{
  "name": "@kompo/haiku-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "exports": {
    ".": "./dist/index.js",
    "./lib": "./dist/lib/index.js"
  },
  "scripts": {
    "build": "bun run tsc",
    "dev": "bun --watch src/server.ts",
    "start": "bun dist/server.js",
    "test": "bun test",
    "package": "bun run build && bun run test"
  },
  "engines": {
    "bun": ">=1.0.0",
    "node": ">=18.0.0"
  }
}
```

### Phase 4: GitHub Packages Distribution

#### 4.1 Repository Configuration
- **Registry**: `npm.pkg.github.com`
- **Scope**: `@kompo` organization
- **Visibility**: Private (internal use only)
- **Authentication**: GitHub token-based

#### 4.2 Publishing Strategy
- **Semantic Versioning**: 1.0.0 for initial release
- **Beta Testing**: 1.0.0-beta.x for pre-release validation
- **Automated CI**: GitHub Actions on tag push

### Phase 5: Consumer Integration Plan

#### 5.1 YOLO-FFMPEG-MCP Integration
```typescript
// Replace current local import
// OLD: import { HaikuMCPServer } from './haiku-mcp-ts/src/server.js';
// NEW: import { HaikuMCPServer } from '@kompo/haiku-mcp-server';
```

#### 5.2 Kompo.ai Integration
```bash
# Install as dependency
bun add @kompo/haiku-mcp-server

# Use in HTTP wrapper
import { createHaikuServer } from '@kompo/haiku-mcp-server';
```

## Risk Mitigation

### Technical Risks
1. **MCP Protocol Compatibility**: Maintain exact same tool interfaces
2. **Performance Regression**: Benchmark before/after migration
3. **Dependency Conflicts**: Test with consumer projects during development

### Project Risks
1. **Over-Engineering**: Resist unnecessary complexity from consumer wishes
2. **Breaking Changes**: Coordinate releases with consumer projects
3. **Maintenance Burden**: Keep package scope focused and minimal

## Success Criteria

### Functional Requirements
- ✅ All 8 MCP tools operational via package import
- ✅ Dual LLM support (Anthropic + Gemini) maintained
- ✅ File registry system fully functional
- ✅ Configuration flexibility preserved
- ✅ TypeScript support with full type definitions

### Performance Requirements
- ✅ Startup time: <2 seconds cold start
- ✅ Memory usage: Realistic baseline (not artificial <200MB constraint)
- ✅ Response time: <5 seconds for video operations
- ✅ Success rate: >95% for core MCP operations

### Integration Requirements
- ✅ Drop-in replacement for current yolo-ffmpeg-mcp usage
- ✅ Seamless kompo.ai HTTP wrapper integration
- ✅ GitHub Packages distribution working
- ✅ Bun and npm compatibility verified

## Implementation Timeline

**Week 1**: Package structure and entry points
**Week 2**: Factory functions and configuration management
**Week 3**: Bun migration and GitHub Packages setup
**Week 4**: Consumer integration testing and documentation

## Post-Implementation Coordination

### Parent Project Updates
1. **yolo-ffmpeg-mcp**: Update imports to use published package
2. **kompo.ai**: Replace basic MCP server with full package
3. **Documentation**: Update all references to new package structure

### Ongoing Maintenance
- **Version Coordination**: Align releases with consumer project needs
- **Performance Monitoring**: Track package performance across consumers
- **Feature Requests**: Evaluate against core video processing mission

This implementation plan ensures we create a high-quality, reusable package while maintaining the proven architecture and resisting unnecessary complexity from downstream consumers.