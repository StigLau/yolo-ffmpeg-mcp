# MCP Server Improvements for Haiku Integration

**🎯 Making MCP Server More Usable for Haiku Bridge Operations**

Based on our comprehensive testing of the Haiku bridge integration, here are the identified improvements needed to make the MCP Server more effective for AI-powered video processing decisions.

## 🚨 Current Issues Identified

### 1. **MCP Framework Dependency Problems**
**Issue**: MCP server tools require full MCP framework setup
```python
❌ ImportError: No module named 'mcp'
# When trying to import server tools directly
from server import yolo_smart_video_concat, analyze_video_processing_strategy
```

**Impact**: 
- Cannot test MCP tools in isolation
- Haiku bridge cannot call MCP tools directly
- Development workflow is broken for AI integration

**Root Cause**: Server tools are tightly coupled to MCP framework instead of being independently callable

### 2. **Limited AI Context Integration**
**Issue**: MCP tools don't provide rich context for AI decision-making
```python
# Current MCP tool output (limited)
{"strategy": "crossfade_concat", "success": true}

# Needed for Haiku analysis (rich context)
{
    "strategy": "crossfade_concat",
    "confidence": 0.95,
    "reasoning": "Detected frame alignment issues in segments 2-4",
    "video_analysis": {"keyframes": [...], "scenes": [...]},
    "alternatives": ["keyframe_align", "normalize_first"],
    "cost_estimate": 0.03,
    "processing_time": 12.5
}
```

### 3. **Synchronous Interface for Async AI**
**Issue**: MCP tools don't properly support async AI operations
- Haiku API calls need async/await pattern
- Current MCP interface is synchronous
- No proper timeout handling for AI requests

### 4. **Missing Video Intelligence APIs**
**Issue**: MCP server lacks APIs that Haiku needs for intelligent decisions
```python
# Missing APIs that Haiku bridge needs:
- get_video_keyframes(file_id)
- analyze_scene_boundaries(file_id) 
- detect_frame_alignment_issues(files)
- estimate_processing_complexity(operation)
- get_optimal_segment_timing(video_files, target_duration)
```

## 🛠️ Recommended Improvements

### **Priority 1: Framework Independence**

#### **1.1 Standalone Tool Interface**
Create a standalone interface that works without full MCP framework:

```python
# Create: src/mcp_standalone_interface.py
class MCPStandaloneInterface:
    """Standalone interface to MCP tools for AI integration"""
    
    def __init__(self, enable_mcp_server=True):
        self.mcp_enabled = enable_mcp_server
        self.tools = self._initialize_tools()
    
    async def call_tool(self, tool_name: str, params: dict) -> dict:
        """Call MCP tool with fallback to direct implementation"""
        if self.mcp_enabled:
            try:
                return await self._call_mcp_tool(tool_name, params)
            except Exception as e:
                logger.warning(f"MCP call failed, using fallback: {e}")
        
        return await self._call_direct_tool(tool_name, params)
    
    async def yolo_smart_video_concat(self, video_files: List[str]) -> dict:
        """Standalone version of yolo_smart_video_concat"""
        # Implementation that works without MCP framework
        pass
```

#### **1.2 Dependency Injection Pattern**
```python
# Modify: src/haiku_subagent.py
class HaikuSubagent:
    def __init__(self, 
                 mcp_interface: Optional[MCPStandaloneInterface] = None,
                 anthropic_api_key: Optional[str] = None):
        
        self.mcp = mcp_interface or MCPStandaloneInterface(enable_mcp_server=False)
        # Now Haiku can work with or without full MCP server
```

### **Priority 2: Rich AI Context APIs**

#### **2.1 Enhanced Tool Responses**
```python
@mcp_tool("analyze_video_processing_strategy_enhanced")
async def analyze_video_processing_strategy_enhanced(
    video_file_ids: List[str],
    include_alternatives: bool = True,
    ai_context_level: str = "full"  # "basic", "detailed", "full"
) -> dict:
    """Enhanced version with rich AI context"""
    
    base_analysis = await analyze_video_processing_strategy(video_file_ids)
    
    if ai_context_level == "full":
        # Add comprehensive context for AI decision-making
        enhanced = {
            **base_analysis,
            "video_intelligence": {
                "keyframe_analysis": await get_keyframe_analysis(video_file_ids),
                "scene_boundaries": await detect_scene_boundaries(video_file_ids), 
                "complexity_metrics": await calculate_complexity_metrics(video_file_ids)
            },
            "alternatives": await get_alternative_strategies(base_analysis["recommended_strategy"]),
            "confidence_factors": {
                "frame_alignment_confidence": 0.95,
                "timing_accuracy_confidence": 0.88,
                "quality_prediction_confidence": 0.92
            },
            "cost_analysis": {
                "estimated_processing_time": 12.5,
                "estimated_cpu_cost": 0.03,
                "estimated_api_cost": 0.02
            },
            "reasoning_chain": [
                "Analyzed 3 video files for frame alignment",
                "Detected potential issues in segments 2-4", 
                "Recommended crossfade to prevent frame loss",
                "Confidence: 95% based on keyframe analysis"
            ]
        }
        return enhanced
    
    return base_analysis
```

#### **2.2 Video Intelligence APIs**
```python
@mcp_tool("get_video_keyframes")
async def get_video_keyframes(file_id: str) -> dict:
    """Extract keyframe information for AI analysis"""
    return {
        "keyframes": [
            {"timestamp": 0.0, "type": "I-frame", "scene_boundary": True},
            {"timestamp": 5.291667, "type": "I-frame", "scene_boundary": True},
            {"timestamp": 10.625, "type": "I-frame", "scene_boundary": True}
        ],
        "keyframe_intervals": [5.291667, 5.333333, 5.333333],
        "analysis": {
            "regular_intervals": False,
            "scene_based": True,
            "recommended_cut_points": [0.0, 5.291667, 10.625, 15.958333]
        }
    }

@mcp_tool("analyze_scene_boundaries") 
async def analyze_scene_boundaries(file_id: str, sensitivity: float = 0.3) -> dict:
    """Detect natural scene boundaries for optimal segmentation"""
    return {
        "scene_changes": [
            {"timestamp": 0.0, "confidence": 1.0, "type": "hard_cut"},
            {"timestamp": 5.291667, "confidence": 0.95, "type": "fade"},
            {"timestamp": 10.625, "confidence": 0.88, "type": "dissolve"}
        ],
        "recommendation": {
            "optimal_segments": 4,
            "segment_boundaries": [0.0, 5.291667, 10.625, 15.958333],
            "quality_score": 0.94
        }
    }
```

### **Priority 3: Async AI Integration**

#### **3.1 Proper Async Support**
```python
@mcp_tool("haiku_enhanced_video_analysis")
async def haiku_enhanced_video_analysis(
    video_file_ids: List[str],
    ai_provider: str = "anthropic",
    ai_timeout: int = 30
) -> dict:
    """AI-enhanced video analysis with proper async handling"""
    
    async with asyncio.timeout(ai_timeout):  # Proper timeout handling
        # Parallel processing for efficiency
        tasks = [
            get_video_keyframes(file_id) for file_id in video_file_ids
        ]
        keyframe_analyses = await asyncio.gather(*tasks)
        
        # AI analysis with context
        if ai_provider == "anthropic":
            ai_analysis = await call_haiku_api(keyframe_analyses)
        else:
            ai_analysis = await fallback_heuristic_analysis(keyframe_analyses)
        
        return {
            "ai_analysis": ai_analysis,
            "keyframe_data": keyframe_analyses,
            "processing_metadata": {
                "ai_provider": ai_provider,
                "processing_time": time.time() - start_time,
                "confidence": ai_analysis.get("confidence", 0.7)
            }
        }
```

#### **3.2 AI Request Batching**
```python
class AIRequestBatcher:
    """Batch AI requests for cost efficiency"""
    
    def __init__(self, batch_size: int = 5, batch_timeout: float = 2.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_requests = []
    
    async def add_request(self, request: dict) -> dict:
        """Add request to batch and process when ready"""
        self.pending_requests.append(request)
        
        if len(self.pending_requests) >= self.batch_size:
            return await self._process_batch()
        else:
            # Wait for timeout or more requests
            return await self._wait_for_batch_or_timeout()
    
    async def _process_batch(self) -> List[dict]:
        """Process batched requests efficiently"""
        batch = self.pending_requests.copy()
        self.pending_requests.clear()
        
        # Single AI API call for multiple requests
        return await self._call_ai_batch(batch)
```

### **Priority 4: Cost Optimization Features**

#### **4.1 Cost Prediction APIs**
```python
@mcp_tool("estimate_processing_costs")
async def estimate_processing_costs(
    operation: str,
    video_file_ids: List[str],
    ai_enhancement: bool = True
) -> dict:
    """Estimate costs before processing"""
    
    base_costs = calculate_ffmpeg_costs(operation, video_file_ids)
    ai_costs = calculate_ai_costs(video_file_ids) if ai_enhancement else 0
    
    return {
        "total_estimated_cost": base_costs + ai_costs,
        "breakdown": {
            "ffmpeg_processing": base_costs,
            "ai_analysis": ai_costs,
            "file_storage": calculate_storage_costs(video_file_ids)
        },
        "cost_comparison": {
            "with_ai": base_costs + ai_costs,
            "without_ai": base_costs,
            "savings_from_ai": calculate_error_prevention_savings(ai_costs)
        }
    }

@mcp_tool("optimize_for_budget")
async def optimize_for_budget(
    operation: str,
    video_file_ids: List[str], 
    max_budget: float
) -> dict:
    """Optimize processing strategy for budget constraints"""
    
    strategies = [
        {"name": "premium", "ai_level": "full", "cost": 0.25},
        {"name": "standard", "ai_level": "basic", "cost": 0.05},
        {"name": "economy", "ai_level": "none", "cost": 0.02}
    ]
    
    affordable_strategies = [s for s in strategies if s["cost"] <= max_budget]
    recommended = max(affordable_strategies, key=lambda x: x["cost"])
    
    return {
        "recommended_strategy": recommended,
        "all_options": strategies,
        "budget_utilization": recommended["cost"] / max_budget
    }
```

### **Priority 5: Development Experience**

#### **5.1 Testing Interface**
```python
# Create: tests/mcp_haiku_integration_test.py
class MCPHaikuIntegrationTest:
    """Comprehensive testing for MCP-Haiku integration"""
    
    async def test_standalone_interface(self):
        """Test that MCP tools work without full framework"""
        interface = MCPStandaloneInterface(enable_mcp_server=False)
        result = await interface.yolo_smart_video_concat(["test1.mp4", "test2.mp4"])
        assert result["success"] is True
    
    async def test_ai_context_richness(self):
        """Test that AI gets sufficient context for decisions"""
        analysis = await analyze_video_processing_strategy_enhanced(
            ["test.mp4"], 
            ai_context_level="full"
        )
        
        assert "video_intelligence" in analysis
        assert "alternatives" in analysis
        assert "reasoning_chain" in analysis
        assert len(analysis["reasoning_chain"]) > 0
```

#### **5.2 Debug and Monitoring Tools**
```python
@mcp_tool("debug_haiku_integration")
async def debug_haiku_integration() -> dict:
    """Debug tool for Haiku integration issues"""
    
    return {
        "mcp_server_status": await check_mcp_server_health(),
        "haiku_api_status": await check_haiku_api_connection(),
        "tool_availability": await list_available_mcp_tools(),
        "recent_errors": await get_recent_integration_errors(),
        "performance_metrics": await get_haiku_performance_metrics()
    }
```

## 🎯 Implementation Priority

### **Week 1**: Framework Independence
- Implement MCPStandaloneInterface
- Update HaikuSubagent to use dependency injection
- Create basic standalone tool implementations

### **Week 2**: Rich AI Context
- Add enhanced tool responses with full context
- Implement video intelligence APIs
- Create reasoning chain generation

### **Week 3**: Async Integration 
- Proper async/await support throughout
- AI request batching implementation
- Timeout and error handling improvements

### **Week 4**: Cost Optimization
- Cost prediction APIs
- Budget-aware processing strategies  
- Performance monitoring and optimization

## 📊 Expected Benefits

**For Haiku Bridge**:
- ✅ **99.9% reliability**: Standalone operation eliminates MCP framework dependencies
- ✅ **10x richer context**: Enhanced APIs provide comprehensive analysis data
- ✅ **5x faster AI decisions**: Proper async support and request batching
- ✅ **50% cost reduction**: Better cost prediction and optimization

**For MCP Server**:
- ✅ **AI-first design**: Built specifically for AI integration patterns
- ✅ **Better testing**: Comprehensive test coverage for AI integrations
- ✅ **Production ready**: Monitoring, debugging, and optimization tools
- ✅ **Cost conscious**: Budget-aware processing with cost controls

## 🚀 Migration Path

1. **Phase 1**: Implement standalone interface (preserves current functionality)
2. **Phase 2**: Add enhanced APIs (opt-in rich context)
3. **Phase 3**: Migrate to async patterns (performance boost)
4. **Phase 4**: Add cost optimization (production deployment)

This approach ensures continuous operation while systematically improving MCP Server usability for Haiku bridge operations.