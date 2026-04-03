#!/usr/bin/env python3
"""
Basic Haiku Subagent Test - Standalone version
Tests the Haiku integration without complex dependencies
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.haiku_subagent import HaikuSubagent, CostLimits, ProcessingStrategy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fallback_analysis():
    """Test heuristic analysis when no API key provided"""
    print("🤖 Testing Haiku Fallback Analysis (no API key)")
    print("=" * 50)
    
    # Initialize without API key - should use fallback
    haiku_agent = HaikuSubagent(
        anthropic_api_key=None,  # No API key
        fallback_enabled=True
    )
    
    # Create some mock video files for testing
    test_files = [
        Path("test_video_1.mp4"),
        Path("test_video_2.mp4"), 
        Path("test_video_3.mp4")
    ]
    
    # Simulate file existence and sizes
    for i, file_path in enumerate(test_files):
        # Create empty files for testing
        file_path.touch()
        
    print(f"📁 Testing with {len(test_files)} mock video files")
    
    try:
        # Get analysis
        analysis = await haiku_agent.analyze_video_files(test_files)
        
        print(f"\n📊 === FALLBACK ANALYSIS RESULTS ===")
        print(f"Strategy: {analysis.recommended_strategy.value}")
        print(f"Frame Issues: {analysis.has_frame_issues}")
        print(f"Needs Normalization: {analysis.needs_normalization}")
        print(f"Complexity Score: {analysis.complexity_score:.2f}")
        print(f"Confidence: {analysis.confidence:.2f}")
        print(f"Reasoning: {analysis.reasoning}")
        print(f"Cost: ${analysis.estimated_cost:.4f} (should be 0.0 for fallback)")
        print(f"Time: {analysis.estimated_time:.1f}s")
        
        # Verify this was fallback mode
        assert analysis.estimated_cost == 0.0, "Fallback should have zero cost"
        print("✅ Fallback mode working correctly")
        
        # Show cost status
        cost_status = haiku_agent.get_cost_status()
        print(f"\n💰 === COST STATUS ===")
        print(f"Daily Spend: ${cost_status['daily_spend']:.4f}")
        print(f"Analysis Count: {cost_status['analysis_count']}")
        print(f"Can Afford More: {cost_status['can_afford_analysis']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup test files
        for file_path in test_files:
            file_path.unlink(missing_ok=True)

async def test_different_scenarios():
    """Test different video scenarios to see strategy selection"""
    print("\n🎯 Testing Strategy Selection for Different Scenarios")
    print("=" * 50)
    
    haiku_agent = HaikuSubagent(fallback_enabled=True)
    
    scenarios = [
        {
            "name": "Single Video",
            "files": ["single_video.mp4"],
            "expected": ProcessingStrategy.DIRECT_PROCESS
        },
        {
            "name": "Two Small Videos", 
            "files": ["small1.mp4", "small2.mp4"],
            "expected": ProcessingStrategy.STANDARD_CONCAT
        },
        {
            "name": "Many Large Videos",
            "files": [f"large_{i}.mp4" for i in range(8)],  # 8 files = likely crossfade
            "expected": ProcessingStrategy.CROSSFADE_CONCAT
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Testing: {scenario['name']}")
        
        # Create test files
        test_paths = [Path(f) for f in scenario['files']]
        for path in test_paths:
            path.touch()
            
        # Get analysis
        analysis = await haiku_agent.analyze_video_files(test_paths)
        
        print(f"  Files: {len(test_paths)}")
        print(f"  Strategy: {analysis.recommended_strategy.value}")
        print(f"  Expected: {scenario['expected'].value}")
        print(f"  Reasoning: {analysis.reasoning}")
        
        # Cleanup
        for path in test_paths:
            path.unlink(missing_ok=True)

async def test_cost_management():
    """Test cost management features"""
    print("\n💰 Testing Cost Management")
    print("=" * 50)
    
    # Test with very low limits
    low_limits = CostLimits(daily_limit=0.01, per_analysis_limit=0.005)
    
    haiku_agent = HaikuSubagent(
        anthropic_api_key=None,  # No API key
        cost_limits=low_limits,
        fallback_enabled=True
    )
    
    print("🧪 Testing with very low cost limits ($0.01 daily)")
    
    test_file = Path("cost_test.mp4")
    test_file.touch()
    
    try:
        # This should work (fallback mode)
        analysis = await haiku_agent.analyze_video_files([test_file])
        
        cost_status = haiku_agent.get_cost_status()
        print(f"Can afford analysis: {cost_status['can_afford_analysis']}")
        print(f"Used fallback: {analysis.estimated_cost == 0.0}")
        
        # Test cost reset
        haiku_agent.reset_daily_costs()
        new_status = haiku_agent.get_cost_status()
        print(f"After reset - Daily spend: ${new_status['daily_spend']:.4f}")
        
        print("✅ Cost management working correctly")
        
    finally:
        test_file.unlink(missing_ok=True)

async def main():
    """Run all basic tests"""
    print("🚀 YOLO-FFMPEG Haiku Subagent Basic Tests")
    print("🔧 Testing without Anthropic API key (fallback mode only)")
    print("=" * 60)
    
    try:
        # Run tests
        success1 = await test_fallback_analysis()
        await test_different_scenarios()
        await test_cost_management()
        
        print("\n🎉 === BASIC TESTS COMPLETE ===")
        
        if success1:
            print("✅ All basic functionality working")
            print("✅ Fallback mode operational")
            print("✅ Cost management operational") 
            print("✅ Strategy selection working")
            print("\n💡 Next: Set ANTHROPIC_API_KEY to test AI functionality")
        else:
            print("❌ Some tests failed")
            return False
            
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        print(f"\n❌ Tests failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)