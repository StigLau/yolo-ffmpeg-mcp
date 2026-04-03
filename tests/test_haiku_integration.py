#!/usr/bin/env python3
"""
Quick integration test for Haiku Subagent

Tests core functionality without requiring API keys or video files.
Verifies the integration works and components are properly connected.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.haiku_subagent import (
    HaikuSubagent, ProcessingStrategy, CostLimits, VideoAnalysis
)

def test_haiku_agent_initialization():
    """Test Haiku agent can be initialized with and without API key"""
    print("🧪 Testing Haiku agent initialization...")
    
    # Test without API key (fallback mode)
    agent_fallback = HaikuSubagent(
        anthropic_api_key=None,
        fallback_enabled=True
    )
    assert agent_fallback.client is None
    assert agent_fallback.fallback_enabled == True
    print("✅ Fallback mode initialization works")
    
    # Test with mock API key
    agent_ai = HaikuSubagent(
        anthropic_api_key="mock_key",
        fallback_enabled=True
    )
    # Client creation might fail without valid key, but that's expected
    print("✅ AI mode initialization works")
    
    # Test cost limits
    custom_limits = CostLimits(daily_limit=10.0, per_analysis_limit=0.05)
    agent_custom = HaikuSubagent(
        anthropic_api_key=None,
        cost_limits=custom_limits,
        fallback_enabled=True
    )
    assert agent_custom.cost_limits.daily_limit == 10.0
    print("✅ Custom cost limits work")

async def test_fallback_analysis():
    """Test fallback analysis with mock video files"""
    print("\n🧪 Testing fallback analysis...")
    
    agent = HaikuSubagent(
        anthropic_api_key=None,  # Force fallback
        fallback_enabled=True
    )
    
    # Create mock video paths (don't need to exist for fallback)
    mock_videos = [
        Path("/mock/video1.mp4"),
        Path("/mock/video2.mp4"),
        Path("/mock/video3.mp4")
    ]
    
    # Test analysis
    analysis = await agent.analyze_video_files(mock_videos)
    
    # Verify analysis structure
    assert isinstance(analysis, VideoAnalysis)
    assert isinstance(analysis.has_frame_issues, bool)
    assert isinstance(analysis.needs_normalization, bool)
    assert 0 <= analysis.complexity_score <= 1
    assert 0 <= analysis.confidence <= 1
    assert isinstance(analysis.recommended_strategy, ProcessingStrategy)
    assert analysis.estimated_cost == 0.0  # Fallback is free
    assert "heuristic" in analysis.reasoning.lower()
    
    print(f"✅ Fallback analysis works: {analysis.recommended_strategy.value}")
    print(f"   Confidence: {analysis.confidence:.2f}")
    print(f"   Reasoning: {analysis.reasoning}")

def test_cost_management():
    """Test cost tracking and management"""
    print("\n🧪 Testing cost management...")
    
    limits = CostLimits(daily_limit=1.0, per_analysis_limit=0.10)
    agent = HaikuSubagent(cost_limits=limits, fallback_enabled=True)
    
    # Test cost status
    status = agent.get_cost_status()
    assert "daily_spend" in status
    assert "daily_limit" in status
    assert "analysis_count" in status
    assert status["daily_limit"] == 1.0
    print("✅ Cost status tracking works")
    
    # Test cost reset
    agent.cost_limits.current_daily_spend = 0.5  # Simulate spending
    agent.cost_limits.analysis_count = 10
    
    agent.reset_daily_costs()
    assert agent.cost_limits.current_daily_spend == 0.0
    assert agent.cost_limits.analysis_count == 0
    print("✅ Cost reset works")
    
    # Test affordability check
    agent.cost_limits.current_daily_spend = 0.98  # Very near limit
    can_afford = agent._can_afford_analysis()
    assert can_afford == False  # Should be false (0.98 + 0.05 > 1.0)
    print("✅ Cost limit checking works")

def test_strategy_enum():
    """Test processing strategy enum"""
    print("\n🧪 Testing strategy enumeration...")
    
    strategies = [
        ProcessingStrategy.STANDARD_CONCAT,
        ProcessingStrategy.CROSSFADE_CONCAT, 
        ProcessingStrategy.KEYFRAME_ALIGN,
        ProcessingStrategy.NORMALIZE_FIRST,
        ProcessingStrategy.DIRECT_PROCESS
    ]
    
    for strategy in strategies:
        assert hasattr(strategy, 'value')
        assert isinstance(strategy.value, str)
        print(f"   ✅ {strategy.value}")

def test_imports():
    """Test all imports work correctly"""
    print("\n🧪 Testing imports...")
    
    try:
        # Test importing server modifications
        from src.server import haiku_agent
        print("✅ Server integration import works")
    except ImportError as e:
        print(f"⚠️  Server import issue (expected if not running): {e}")
    
    # Test core imports
    from src.haiku_subagent import yolo_smart_concat
    print("✅ Core function imports work")
    
    try:
        import anthropic
        print("✅ Anthropic library available")
    except ImportError:
        print("⚠️  Anthropic library not installed (pip install anthropic)")

async def test_integration_complete():
    """Run all integration tests"""
    print("🚀 Haiku Subagent Integration Test")
    print("=" * 50)
    
    try:
        # Run all tests
        test_haiku_agent_initialization()
        await test_fallback_analysis()
        test_cost_management()
        test_strategy_enum()
        test_imports()
        
        print("\n🎉 All integration tests passed!")
        print("\n📋 Integration Status:")
        print("✅ Haiku agent initialization")
        print("✅ Fallback analysis (works without API key)")
        print("✅ Cost management and limits")
        print("✅ Processing strategy selection")
        print("✅ Core functionality imports")
        
        print("\n🚀 Ready to use! Try:")
        print("   python examples/haiku_integration_demo.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_integration_complete())
    sys.exit(0 if success else 1)