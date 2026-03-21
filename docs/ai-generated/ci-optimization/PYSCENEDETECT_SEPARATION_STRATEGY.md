# PySceneDetect Separation Strategy

**Document Purpose**: Strategy for separating scene detection functionality from core FFMPEG MCP server to reduce CI complexity and improve modularity.

## 🚨 Current Problem

### CI Container Warning Issue
```
🔍 Testing Docker container health...
❌ Container failed to start  
WARNING: PySceneDetect not found. Scene detection will use a fallback mechanism (single scene).
Error: Process completed with exit code 1.
```

**Root Cause Analysis:**
1. **CI Workspace Mounting**: GitHub Actions mounts entire workspace (`${{ github.workspace }}:/app`)
2. **Unintended Dependencies**: Container gains access to `src/content_analyzer.py` 
3. **Import Attempts**: `content_analyzer.py` tries to import PySceneDetect on initialization
4. **Missing Dependencies**: CI Docker image doesn't include PySceneDetect (intentionally lightweight)
5. **Warning Output**: Fallback mechanism works but generates confusing CI logs

### Current Architecture Issues
- **Tight Coupling**: Scene detection logic embedded in core MCP server
- **Heavy Dependencies**: PySceneDetect + OpenCV increase build times significantly  
- **CI Complexity**: Filter testing doesn't need scene detection but inherits the dependency
- **Monolithic Design**: Single project handles video processing, scene analysis, and filter testing

## 🎯 Immediate Fix (Option 1): Selective CI Mounting

### Quick Solution
Modify CI workflow to mount only required files instead of entire workspace:

```yaml
# Before (problematic)
-v ${{ github.workspace }}:/app

# After (selective)  
-v ${{ github.workspace }}/test_fast_filter_ci.py:/app/test_fast_filter_ci.py
-v ${{ github.workspace }}/video_comparison_test_library.py:/app/video_comparison_test_library.py
```

**Benefits:**
- ✅ Eliminates PySceneDetect warning immediately
- ✅ Prevents accidental imports of unneeded modules
- ✅ Maintains current functionality
- ✅ 5-minute implementation time

**Limitations:**
- 🔶 Doesn't address underlying architectural coupling
- 🔶 Still requires careful maintenance of mounted files
- 🔶 Band-aid solution that doesn't improve long-term maintainability

## 🏗️ Long-term Solution (Option 2): Project Separation

### Architectural Vision

#### Core FFMPEG MCP Server
```
yolo-ffmpeg-mcp/
├── src/
│   ├── server.py                 # MCP protocol handler
│   ├── ffmpeg_wrapper.py         # Video processing core
│   ├── video_operations.py       # Filter applications
│   ├── komposition_processor.py  # Beat-sync music videos
│   └── file_manager.py           # Secure file handling
├── tests/
└── Dockerfile                    # Production image
```

**Responsibilities:**
- Video format conversion and processing
- FFMPEG filter application and effects
- Beat-synchronized music video creation
- File management and security
- MCP protocol implementation

#### Separate Scene Detection Service
```
ffmpeg-scene-analyzer/
├── src/
│   ├── scene_detector.py         # PySceneDetect integration
│   ├── content_analyzer.py       # Visual content analysis
│   ├── screenshot_generator.py   # Scene frame extraction
│   └── analysis_cache.py         # Metadata persistence
├── tests/
├── Dockerfile                    # Scene analysis image
└── API documentation
```

**Responsibilities:**
- Scene boundary detection using PySceneDetect
- Visual content analysis and object recognition
- Screenshot generation for scene visualization
- Analysis result caching and metadata storage
- Standalone API for scene analysis requests

#### Filter Testing Framework
```
ffmpeg-filter-testing/
├── test_fast_filter_ci.py
├── video_comparison_test_library.py
├── filter_effectiveness_analysis.py
├── Dockerfile.ci                 # Lightweight testing image
└── GitHub Actions workflows
```

**Responsibilities:**
- Automated filter effectiveness testing
- Video comparison and analysis
- CI/CD pipeline for filter validation
- Performance benchmarking
- Filter regression detection

### Integration Strategy

#### API-Based Communication
```python
# Scene analysis via HTTP API
scene_analyzer_client = SceneAnalyzerClient("http://scene-service:8080")
scenes = await scene_analyzer_client.analyze_video(video_id)

# Or via separate MCP server
scene_mcp_client = MCPClient("scene-analyzer-mcp")
scenes = await scene_mcp_client.call("analyze_scenes", {"video_id": video_id})
```

#### Docker Compose Orchestration
```yaml
services:
  ffmpeg-mcp:
    build: ./yolo-ffmpeg-mcp
    ports: ["8000:8000"]
    
  scene-analyzer:
    build: ./ffmpeg-scene-analyzer  
    ports: ["8080:8080"]
    environment:
      - PYSCENEDETECT_AVAILABLE=true
    
  filter-testing:
    build: ./ffmpeg-filter-testing
    depends_on: [ffmpeg-mcp]
    volumes: ["/tmp/music:/tmp/music"]
```

### Migration Path

#### Phase 1: Interface Extraction (Week 1)
1. Create abstract `SceneAnalyzer` interface in core project
2. Implement `LocalSceneAnalyzer` (current PySceneDetect code)
3. Add configuration to disable scene detection in CI environments
4. Update tests to work with scene detection disabled

#### Phase 2: Service Creation (Week 2-3)  
1. Create new `ffmpeg-scene-analyzer` repository
2. Move `content_analyzer.py` and PySceneDetect dependencies
3. Implement HTTP API with OpenAPI documentation
4. Create Docker image with all scene detection dependencies

#### Phase 3: Integration & Testing (Week 4)
1. Implement `RemoteSceneAnalyzer` client in core project
2. Update configuration to use remote service by default
3. Comprehensive testing of both local and remote modes
4. Performance benchmarking and optimization

#### Phase 4: Documentation & Deployment (Week 5)
1. Complete API documentation and usage examples
2. Docker Compose setup for development environments
3. Production deployment guidelines
4. Migration guide for existing users

## 📊 Cost-Benefit Analysis

### Benefits of Separation
- **🚀 Faster CI**: Filter testing builds in 15-30s vs 5-10 minutes
- **🔧 Focused Maintenance**: Each project has single responsibility
- **📈 Scalability**: Scene analysis can scale independently
- **🔄 Reusability**: Scene detection service usable by other projects
- **🛡️ Robustness**: Core MCP server doesn't fail if scene detection fails
- **👥 Developer Experience**: Clearer project boundaries, easier onboarding

### Migration Costs
- **⏱️ Development Time**: ~3-4 weeks full migration
- **🔧 Complexity**: Additional service to deploy and maintain
- **📡 Network Dependency**: Introduces network calls for scene analysis
- **🔄 Compatibility**: Need to maintain backward compatibility during transition

### Risk Mitigation
- **Gradual Migration**: Maintain local fallback during transition
- **Feature Flags**: Configuration-driven scene detection mode
- **Comprehensive Testing**: Automated tests for both local and remote modes
- **Documentation**: Clear migration path and troubleshooting guides

## 🎯 Recommendation

### Immediate Action (This Week)
Implement **Option 1 (Selective CI Mounting)** to resolve CI warnings immediately:
- Modify `.github/workflows/filter-analysis-ci.yml` 
- Mount only required test files
- Test CI pipeline with changes
- **Time Investment**: 30 minutes
- **Risk**: Very low

### Strategic Planning (Next Quarter)
Plan **Option 2 (Project Separation)** as a larger refactoring initiative:
- Include in project roadmap for better architecture
- Consider during next major version planning
- Evaluate alongside other modularity improvements
- **Time Investment**: 3-4 weeks
- **Risk**: Medium, but high long-term value

## 📋 Implementation Checklist

### Quick Fix (Option 1)
- [ ] Modify CI workflow file mounting strategy
- [ ] Test CI pipeline with selective mounting
- [ ] Verify PySceneDetect warnings are eliminated
- [ ] Document the change in CI configuration

### Future Separation (Option 2)
- [ ] Create project separation design document
- [ ] Set up new repository structure
- [ ] Design API interface for scene analysis service
- [ ] Plan migration timeline and milestones
- [ ] Implement backward compatibility strategy
- [ ] Create comprehensive testing plan
- [ ] Document deployment and configuration changes

---

**Document Created**: For future Claude sessions to understand the PySceneDetect separation strategy and continue the architectural improvement work.

**Last Updated**: 2024-07-28  
**Priority**: Low (after immediate CI fix)  
**Estimated Effort**: 3-4 weeks for complete separation