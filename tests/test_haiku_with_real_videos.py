#!/usr/bin/env python3
"""
Haiku Subagent Test with Real Video Files
Tests the Haiku integration using actual video files from the test directory
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.haiku_subagent import HaikuSubagent, CostLimits

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_real_videos():
    """Test analysis with real video files"""
    print("🎬 Testing Haiku Analysis with Real Video Files")
    print("=" * 50)
    
    # Find real video files
    video_dir = Path(__file__).parent / "tests" / "files"
    video_files = list(video_dir.glob("*.mp4"))
    
    if not video_files:
        print("❌ No video files found in tests/files directory")
        return False
        
    print(f"📁 Found {len(video_files)} video files:")
    for video in video_files:
        try:
            size_mb = video.stat().st_size / (1024 * 1024)
            print(f"  - {video.name} ({size_mb:.1f}MB)")
        except Exception as e:
            print(f"  - {video.name} (error reading size: {e})")
    
    # Test with fallback mode first
    print(f"\n🤖 Testing Fallback Analysis")
    haiku_agent = HaikuSubagent(fallback_enabled=True)
    
    analysis = await haiku_agent.analyze_video_files(video_files)
    
    print(f"\n📊 === FALLBACK ANALYSIS RESULTS ===")
    print(f"Strategy: {analysis.recommended_strategy.value}")
    print(f"Frame Issues: {analysis.has_frame_issues}")
    print(f"Needs Normalization: {analysis.needs_normalization}")
    print(f"Complexity Score: {analysis.complexity_score:.2f}")
    print(f"Confidence: {analysis.confidence:.2f}")
    print(f"Reasoning: {analysis.reasoning}")
    print(f"Cost: ${analysis.estimated_cost:.4f}")
    print(f"Time: {analysis.estimated_time:.1f}s")
    
    # Test with API key if available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print(f"\n🧠 Testing AI Analysis (API key found)")
        
        ai_agent = HaikuSubagent(
            anthropic_api_key=api_key,
            cost_limits=CostLimits(daily_limit=5.0),
            fallback_enabled=True
        )
        
        try:
            ai_analysis = await ai_agent.analyze_video_files(video_files)
            
            print(f"\n📊 === AI ANALYSIS RESULTS ===")
            print(f"Strategy: {ai_analysis.recommended_strategy.value}")
            print(f"Frame Issues: {ai_analysis.has_frame_issues}")
            print(f"Needs Normalization: {ai_analysis.needs_normalization}")
            print(f"Complexity Score: {ai_analysis.complexity_score:.2f}")
            print(f"Confidence: {ai_analysis.confidence:.2f}")
            print(f"Reasoning: {ai_analysis.reasoning}")
            print(f"Cost: ${ai_analysis.estimated_cost:.4f}")
            print(f"Time: {ai_analysis.estimated_time:.1f}s")
            
            # Compare results
            print(f"\n🔍 === COMPARISON ===")
            print(f"Fallback Strategy: {analysis.recommended_strategy.value}")
            print(f"AI Strategy: {ai_analysis.recommended_strategy.value}")
            print(f"Strategy Match: {analysis.recommended_strategy == ai_analysis.recommended_strategy}")
            print(f"Confidence Improvement: {ai_analysis.confidence - analysis.confidence:+.2f}")
            
            # Show final costs
            cost_status = ai_agent.get_cost_status()
            print(f"\n💰 === FINAL COST STATUS ===")
            print(f"Daily Spend: ${cost_status['daily_spend']:.4f}")
            print(f"Analysis Count: {cost_status['analysis_count']}")
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            print("🔄 Falling back to heuristic analysis")
    else:
        print(f"\n💡 No ANTHROPIC_API_KEY found - AI analysis skipped")
        print("Set ANTHROPIC_API_KEY environment variable to test AI functionality")
    
    return True

async def test_ffmpeg_integration():
    """Test basic FFMPEG integration without complex dependencies"""
    print("\n🎞️ Testing Basic FFMPEG Integration")
    print("=" * 50)
    
    # Check if FFMPEG is available
    import shutil
    ffmpeg_path = shutil.which("ffmpeg")
    
    if not ffmpeg_path:
        print("❌ FFMPEG not found in PATH")
        return False
        
    print(f"✅ FFMPEG found at: {ffmpeg_path}")
    
    # Test basic FFMPEG command
    import subprocess
    try:
        result = subprocess.run([ffmpeg_path, "-version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Extract version info
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFMPEG Version: {version_line}")
            return True
        else:
            print(f"❌ FFMPEG version check failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ FFMPEG test failed: {e}")
        return False

async def simulate_processing_strategies():
    """Simulate different processing strategies without actual processing"""
    print("\n🎯 Simulating Processing Strategy Decisions")
    print("=" * 50)
    
    # Find real videos
    video_dir = Path(__file__).parent / "tests" / "files"
    video_files = list(video_dir.glob("*.mp4"))
    
    if not video_files:
        print("❌ No video files available for strategy simulation")
        return
    
    haiku_agent = HaikuSubagent(fallback_enabled=True)
    
    # Test different combinations
    test_cases = [
        {
            "name": "Single Video Processing",
            "files": video_files[:1],
            "description": "Process one video file"
        },
        {
            "name": "Two Video Concatenation", 
            "files": video_files[:2],
            "description": "Concatenate two videos"
        }
    ]
    
    if len(video_files) >= 3:
        test_cases.append({
            "name": "Multi-Video Concatenation",
            "files": video_files[:3], 
            "description": "Concatenate multiple videos"
        })
    
    for case in test_cases:
        print(f"\n📋 {case['name']}")
        print(f"   {case['description']}")
        
        analysis = await haiku_agent.analyze_video_files(case['files'])
        
        print(f"   Files: {len(case['files'])}")
        print(f"   Strategy: {analysis.recommended_strategy.value}")
        print(f"   Confidence: {analysis.confidence:.2f}")
        print(f"   Reasoning: {analysis.reasoning}")
        
        # Explain what this strategy would do
        strategy_explanations = {
            "direct_process": "Process single file without concatenation",
            "standard_concat": "Simple concatenation with stream copy",
            "crossfade_concat": "Concatenation with crossfade transitions",
            "keyframe_align": "Force keyframe alignment for smooth playback", 
            "normalize_first": "Normalize formats before concatenation"
        }
        
        explanation = strategy_explanations.get(analysis.recommended_strategy.value, 
                                               "Unknown strategy")
        print(f"   Action: {explanation}")

async def main():
    """Run real video tests"""
    print("🚀 YOLO-FFMPEG Haiku Integration Test with Real Videos")
    print("=" * 60)
    
    try:
        success1 = await test_with_real_videos()
        success2 = await test_ffmpeg_integration()
        await simulate_processing_strategies()
        
        print("\n🎉 === REAL VIDEO TESTS COMPLETE ===")
        
        if success1 and success2:
            print("✅ Real video analysis working")
            print("✅ FFMPEG integration available")
            print("✅ Processing strategies simulated")
            print("\n🚀 Ready for actual video processing workflows!")
        else:
            print("⚠️ Some components not fully operational")
            if not success1:
                print("   - Video analysis had issues")
            if not success2:
                print("   - FFMPEG not available or not working")
                
    except Exception as e:
        logger.error(f"Tests failed: {e}")
        print(f"\n❌ Tests failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)