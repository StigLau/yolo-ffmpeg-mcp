#!/usr/bin/env python3
"""
Comprehensive tests for MCP Hybrid Bridge - Priority 1: Framework Independence

Tests both MCP framework integration and standalone operation modes.
"""

import asyncio
import json
import pytest
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_hybrid_bridge import MCPHybridBridge, BridgeMode, ToolResult

class TestMCPHybridBridge:
    """Comprehensive test suite for MCP Hybrid Bridge"""
    
    @pytest.fixture
    def bridge_standalone(self):
        """Bridge forced to standalone mode"""
        return MCPHybridBridge(preferred_mode=BridgeMode.STANDALONE)
    
    @pytest.fixture
    def bridge_auto(self):
        """Bridge in auto-detect mode"""
        return MCPHybridBridge(preferred_mode=BridgeMode.HYBRID_AUTO)
    
    @pytest.fixture
    def test_video_files(self, tmp_path):
        """Create test video files"""
        video_files = []
        for i in range(3):
            video_file = tmp_path / f"test_video_{i}.mp4"
            video_file.write_bytes(b"fake video data" * 1000)  # ~15KB files
            video_files.append(str(video_file))
        return video_files
    
    def test_bridge_initialization_standalone(self, bridge_standalone):
        """Test bridge initializes correctly in standalone mode"""
        assert bridge_standalone.operational_mode == BridgeMode.STANDALONE
        assert len(bridge_standalone.standalone_tools) > 0
        assert "yolo_smart_video_concat" in bridge_standalone.standalone_tools
    
    def test_bridge_initialization_auto(self, bridge_auto):
        """Test bridge initializes correctly in auto mode"""
        # Should be standalone since MCP framework likely not available in tests
        assert bridge_auto.operational_mode in [BridgeMode.STANDALONE, BridgeMode.MCP_FRAMEWORK]
        assert len(bridge_auto.standalone_tools) > 0
    
    def test_framework_detection(self):
        """Test MCP framework detection logic"""
        bridge = MCPHybridBridge()
        
        # Detection should complete without errors
        assert isinstance(bridge.mcp_available, bool)
        
        # Should have appropriate operational mode
        if bridge.mcp_available:
            assert bridge.operational_mode == BridgeMode.MCP_FRAMEWORK
        else:
            assert bridge.operational_mode == BridgeMode.STANDALONE
    
    @pytest.mark.asyncio
    async def test_standalone_yolo_smart_video_concat(self, bridge_standalone, test_video_files):
        """Test standalone video concatenation"""
        result = await bridge_standalone.yolo_smart_video_concat(test_video_files)
        
        assert result.success is True
        assert result.method == "standalone"
        assert result.execution_time > 0
        
        # Check result data
        data = result.data
        assert "recommended_strategy" in data
        assert "confidence" in data
        assert "reasoning" in data
        assert data["success"] is True
        assert len(data["files_processed"]) == 3  # All files should exist
    
    @pytest.mark.asyncio
    async def test_standalone_analyze_video_strategy(self, bridge_standalone, test_video_files):
        """Test standalone video strategy analysis"""
        result = await bridge_standalone.analyze_video_processing_strategy(test_video_files)
        
        assert result.success is True
        assert result.method == "standalone"
        
        data = result.data
        assert "recommended_strategy" in data
        assert "confidence" in data
        assert "complexity_score" in data
        assert "has_frame_issues" in data
        assert "file_analysis" in data
        assert len(data["file_analysis"]) == 3
    
    @pytest.mark.asyncio
    async def test_standalone_cost_status(self, bridge_standalone):
        """Test standalone cost status"""
        result = await bridge_standalone.get_haiku_cost_status()
        
        assert result.success is True
        assert result.method == "standalone"
        
        data = result.data
        assert "daily_spend" in data
        assert "daily_limit" in data
        assert "remaining_budget" in data
        assert data["can_afford_analysis"] is True
    
    @pytest.mark.asyncio
    async def test_nonexistent_files_handling(self, bridge_standalone):
        """Test handling of nonexistent files"""
        nonexistent_files = ["nonexistent1.mp4", "nonexistent2.mp4"]
        
        result = await bridge_standalone.yolo_smart_video_concat(nonexistent_files)
        
        assert result.success is True  # Should handle gracefully
        data = result.data
        assert len(data["files_processed"]) == 0  # No files should be processed
        assert "reasoning" in data
    
    @pytest.mark.asyncio
    async def test_mixed_existing_nonexistent_files(self, bridge_standalone, test_video_files):
        """Test handling of mix of existing and nonexistent files"""
        mixed_files = test_video_files[:2] + ["nonexistent.mp4"]
        
        result = await bridge_standalone.yolo_smart_video_concat(mixed_files)
        
        assert result.success is True
        data = result.data
        assert len(data["files_processed"]) == 2  # Only existing files
        assert data["analysis"]["total_files"] == 3
        assert data["analysis"]["existing_files"] == 2
    
    @pytest.mark.asyncio
    async def test_empty_file_list(self, bridge_standalone):
        """Test handling of empty file list"""
        result = await bridge_standalone.yolo_smart_video_concat([])
        
        assert result.success is True
        data = result.data
        assert len(data["files_processed"]) == 0
        assert "reasoning" in data
    
    @pytest.mark.asyncio
    async def test_single_file_processing(self, bridge_standalone, test_video_files):
        """Test single file processing logic"""
        result = await bridge_standalone.yolo_smart_video_concat([test_video_files[0]])
        
        assert result.success is True
        data = result.data
        assert data["recommended_strategy"] == "direct_process"
        assert data["confidence"] >= 0.8
        assert "Single file" in data["reasoning"]
    
    @pytest.mark.asyncio
    async def test_call_tool_interface(self, bridge_standalone, test_video_files):
        """Test universal call_tool interface"""
        result = await bridge_standalone.call_tool(
            "yolo_smart_video_concat",
            video_file_ids=test_video_files
        )
        
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.method == "standalone"
        assert result.execution_time > 0
        assert result.error is None
    
    @pytest.mark.asyncio 
    async def test_invalid_tool_name(self, bridge_standalone):
        """Test handling of invalid tool names"""
        result = await bridge_standalone.call_tool("nonexistent_tool")
        
        assert result.success is False
        assert result.error is not None
        assert "not available" in result.error
    
    def test_bridge_status(self, bridge_standalone):
        """Test bridge status reporting"""
        status = bridge_standalone.get_bridge_status()
        
        assert "operational_mode" in status
        assert "mcp_framework_available" in status
        assert "standalone_tools_available" in status
        assert "tools_registered" in status
        
        assert status["operational_mode"] == "standalone"
        assert isinstance(status["mcp_framework_available"], bool)
        assert status["standalone_tools_available"] > 0
        assert len(status["tools_registered"]) > 0
    
    @pytest.mark.asyncio
    async def test_performance_timing(self, bridge_standalone, test_video_files):
        """Test that operations complete within reasonable time"""
        start_time = time.time()
        
        result = await bridge_standalone.yolo_smart_video_concat(test_video_files)
        
        total_time = time.time() - start_time
        
        assert result.success is True
        assert result.execution_time <= total_time
        assert result.execution_time < 1.0  # Should be fast for small files
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, bridge_standalone, test_video_files):
        """Test concurrent tool operations"""
        tasks = [
            bridge_standalone.yolo_smart_video_concat(test_video_files),
            bridge_standalone.analyze_video_processing_strategy(test_video_files),
            bridge_standalone.get_haiku_cost_status()
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for result in results:
            assert result.success is True
            assert result.method == "standalone"
    
    @pytest.mark.asyncio
    async def test_file_info_operations(self, bridge_standalone, test_video_files):
        """Test file information operations"""
        # Test get_file_info
        result = await bridge_standalone.call_tool("get_file_info", file_id=test_video_files[0])
        
        assert result.success is True
        data = result.data
        assert "size" in data
        assert "extension" in data
        assert data["file_id"] == test_video_files[0]
        
        # Test list_files
        result = await bridge_standalone.call_tool("list_files")
        assert result.success is True
        assert "files" in result.data
        assert "count" in result.data

class TestHaikuIntegration:
    """Test Haiku subagent integration with hybrid bridge"""
    
    @pytest.mark.asyncio
    async def test_haiku_with_hybrid_bridge(self, tmp_path):
        """Test Haiku subagent with hybrid bridge integration"""
        
        # Create test files
        video_files = []
        for i in range(2):
            video_file = tmp_path / f"haiku_test_{i}.mp4"
            video_file.write_bytes(b"test video content" * 500)
            video_files.append(Path(str(video_file)))
        
        # Test with explicit bridge
        bridge = MCPHybridBridge(preferred_mode=BridgeMode.STANDALONE)
        
        try:
            from src.haiku_subagent import HaikuSubagent
            haiku = HaikuSubagent(mcp_bridge=bridge)
            
            # Test video analysis through hybrid bridge
            analysis = await haiku.analyze_video_files(video_files)
            
            assert analysis.has_frame_issues is not None
            assert analysis.confidence > 0
            assert analysis.recommended_strategy is not None
            assert len(analysis.reasoning) > 0
            
        except ImportError:
            pytest.skip("HaikuSubagent not available for integration test")

class TestPerformanceBenchmarks:
    """Performance benchmarks for hybrid bridge operations"""
    
    @pytest.mark.asyncio
    async def test_operation_speed_benchmarks(self, tmp_path):
        """Benchmark operation speeds"""
        
        bridge = MCPHybridBridge(preferred_mode=BridgeMode.STANDALONE)
        
        # Create varying file sizes
        test_cases = [
            {"name": "small", "size": 1024, "count": 1},      # 1KB, 1 file
            {"name": "medium", "size": 1024*100, "count": 3}, # 100KB, 3 files  
            {"name": "large", "size": 1024*1000, "count": 5}  # 1MB, 5 files
        ]
        
        benchmarks = {}
        
        for case in test_cases:
            # Create test files
            files = []
            for i in range(case["count"]):
                file_path = tmp_path / f"{case['name']}_{i}.mp4"
                file_path.write_bytes(b"x" * case["size"])
                files.append(str(file_path))
            
            # Benchmark operations
            start_time = time.time()
            result = await bridge.yolo_smart_video_concat(files)
            operation_time = time.time() - start_time
            
            benchmarks[case["name"]] = {
                "files": case["count"],
                "total_size_kb": (case["size"] * case["count"]) / 1024,
                "operation_time": operation_time,
                "success": result.success
            }
        
        # Verify performance expectations
        for name, benchmark in benchmarks.items():
            assert benchmark["success"] is True
            assert benchmark["operation_time"] < 2.0  # Should be under 2 seconds
            
        # Log benchmarks
        print("\n📊 Performance Benchmarks:")
        for name, benchmark in benchmarks.items():
            print(f"  {name.title()}: {benchmark['files']} files, "
                  f"{benchmark['total_size_kb']:.1f}KB, "
                  f"{benchmark['operation_time']:.3f}s")

# Integration test that can be run manually
async def manual_integration_test():
    """Manual integration test for development verification"""
    
    print("🔧 Manual Integration Test: MCP Hybrid Bridge")
    print("="*50)
    
    # Test bridge initialization
    bridge = MCPHybridBridge()
    status = bridge.get_bridge_status()
    
    print(f"✅ Bridge initialized: {status['operational_mode']} mode")
    print(f"🔗 MCP available: {status['mcp_framework_available']}")
    print(f"🛠️ Tools available: {status['standalone_tools_available']}")
    
    # Test with actual project files
    project_files = ["Oa8iS1W3OCM.mp4", "3xEMCU1fyl8.mp4", "PLnPZVqiyjA.mp4"]
    existing_files = [f for f in project_files if Path(f).exists()]
    
    if existing_files:
        print(f"\n🎬 Testing with {len(existing_files)} project videos...")
        
        result = await bridge.yolo_smart_video_concat(existing_files)
        print(f"📊 Concat analysis: {result.data['recommended_strategy']} "
              f"(confidence: {result.data['confidence']:.2f})")
        
        result = await bridge.analyze_video_processing_strategy(existing_files)
        print(f"🧠 Strategy analysis: {result.data['recommended_strategy']} "
              f"(complexity: {result.data['complexity_score']:.2f})")
    else:
        print("⚠️ No project video files found for testing")
    
    # Test cost status
    result = await bridge.get_haiku_cost_status()
    print(f"💰 Cost status: ${result.data['daily_spend']:.2f} / "
          f"${result.data['daily_limit']:.2f}")
    
    print("\n🎯 Integration test complete!")

if __name__ == "__main__":
    # Run manual integration test
    asyncio.run(manual_integration_test())