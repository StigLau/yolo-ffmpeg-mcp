#!/usr/bin/env python3
"""
Simple QuickCut-AI Test
======================

Test the Haiku subagent analysis functionality with minimal dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.haiku_subagent import HaikuSubagent, CostLimits

async def test_quickcut_analysis():
    """Test QuickCut-AI analysis only"""
    
    print("🎬 QUICKCUT-AI ANALYSIS TEST")
    print("=" * 40)
    print("Testing intelligent video analysis")
    print()
    
    # Test video files
    test_videos = [
        Path("testdata/test_video1.mp4"),  # 1280x720@30fps, 5s
        Path("testdata/test_video2.mp4"),  # 1920x1080@24fps, 3s  
        Path("testdata/test_video3.mp4")   # 1280x720@25fps, 4s
    ]
    
    print(f"📹 TEST VIDEOS:")
    for i, video in enumerate(test_videos, 1):
        if video.exists():
            size = video.stat().st_size / 1024
            print(f"  {i}. {video.name} ({size:.1f} KB)")
        else:
            print(f"  {i}. {video.name} (MISSING)")
    print()
    
    # Initialize QuickCut-AI in fallback mode
    print("🧠 Initializing QuickCut-AI...")
    quickcut_ai = HaikuSubagent(
        anthropic_api_key=None,  # Test fallback mode
        cost_limits=CostLimits(daily_limit=1.0),
        fallback_enabled=True
    )
    print("✅ QuickCut-AI ready (fallback mode)")
    print()
    
    # Run analysis
    print("🔍 Running intelligent analysis...")
    try:
        analysis = await quickcut_ai.analyze_video_files(test_videos)
        
        print(f"📊 ANALYSIS RESULTS:")
        print(f"  Strategy: {analysis.recommended_strategy.value}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        print(f"  Frame Issues: {'Yes' if analysis.has_frame_issues else 'No'}")
        print(f"  Needs Normalization: {'Yes' if analysis.needs_normalization else 'No'}")
        print(f"  Complexity: {analysis.complexity_score:.2f}")
        print(f"  Cost: ${analysis.estimated_cost:.4f}")
        print(f"  Reasoning: {analysis.reasoning}")
        print()
        
        # Cost status
        cost_status = quickcut_ai.get_cost_status()
        print(f"💰 COST STATUS:")
        print(f"  Daily spend: ${cost_status['daily_spend']:.4f}")
        print(f"  Analyses run: {cost_status.get('analysis_count', 0)}")
        print()
        
        print("✅ QuickCut-AI analysis successful!")
        print("🚀 Ready for full video processing with smart AI decisions")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_quickcut_analysis())
    sys.exit(0 if result else 1)