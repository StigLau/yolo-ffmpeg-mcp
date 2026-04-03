#!/usr/bin/env python3
"""
Direct test of Haiku MCP bridge integration by calling server tools
"""
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.server import (
        yolo_smart_video_concat,
        analyze_video_processing_strategy, 
        get_haiku_cost_status,
        reset_haiku_daily_costs
    )
    MCP_SERVER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ MCP server tools not available: {e}")
    MCP_SERVER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_haiku_mcp_tools():
    """Test the Haiku MCP bridge through server tools"""
    
    if not MCP_SERVER_AVAILABLE:
        print("❌ Cannot test - MCP server tools not available")
        return False
    
    print("🎬 Testing Haiku MCP Bridge: Direct Server Tool Integration")
    print("="*70)
    
    # Test data: our three video shorts
    video_file_ids = ["Oa8iS1W3OCM.mp4", "3xEMCU1fyl8.mp4", "PLnPZVqiyjA.mp4"]
    
    # Performance tracking
    start_time = time.time()
    test_results = {
        "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "video_files": video_file_ids,
        "tests": {},
        "performance": {}
    }
    
    # Test 1: Get Haiku cost status
    print(f"\n📊 Test 1: Haiku Cost Status")
    stage_start = time.time()
    
    try:
        cost_status = await get_haiku_cost_status()
        stage_time = time.time() - stage_start
        test_results["performance"]["cost_status"] = stage_time
        test_results["tests"]["cost_status"] = {
            "success": True,
            "result": cost_status,
            "time_seconds": stage_time
        }
        
        print(f"✅ Cost status retrieved in {stage_time:.3f}s")
        print(f"💰 Status: {json.dumps(cost_status, indent=2)}")
        
    except Exception as e:
        stage_time = time.time() - stage_start
        test_results["performance"]["cost_status"] = stage_time
        test_results["tests"]["cost_status"] = {
            "success": False,
            "error": str(e),
            "time_seconds": stage_time
        }
        print(f"❌ Cost status failed in {stage_time:.3f}s: {e}")
    
    # Test 2: Analyze video processing strategy
    print(f"\n🧠 Test 2: Video Processing Strategy Analysis")
    stage_start = time.time()
    
    try:
        strategy_analysis = await analyze_video_processing_strategy(video_file_ids)
        stage_time = time.time() - stage_start
        test_results["performance"]["strategy_analysis"] = stage_time
        test_results["tests"]["strategy_analysis"] = {
            "success": True,
            "result": strategy_analysis,
            "time_seconds": stage_time
        }
        
        print(f"✅ Strategy analysis completed in {stage_time:.3f}s")
        print(f"🎯 Analysis preview:")
        
        # Print key findings
        if isinstance(strategy_analysis, dict):
            for key, value in strategy_analysis.items():
                if key in ["recommended_strategy", "confidence", "has_frame_issues", "reasoning"]:
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        stage_time = time.time() - stage_start
        test_results["performance"]["strategy_analysis"] = stage_time
        test_results["tests"]["strategy_analysis"] = {
            "success": False,
            "error": str(e),
            "time_seconds": stage_time
        }
        print(f"❌ Strategy analysis failed in {stage_time:.3f}s: {e}")
    
    # Test 3: Smart video concatenation (without actually processing)
    print(f"\n🎬 Test 3: Smart Video Concatenation Analysis")
    stage_start = time.time()
    
    try:
        # This will analyze and recommend but may not process due to file availability
        concat_result = await yolo_smart_video_concat(video_file_ids)
        stage_time = time.time() - stage_start
        test_results["performance"]["smart_concat"] = stage_time
        test_results["tests"]["smart_concat"] = {
            "success": True,
            "result": concat_result,
            "time_seconds": stage_time
        }
        
        print(f"✅ Smart concatenation analysis in {stage_time:.3f}s")
        print(f"🎥 Result summary:")
        
        # Print key results
        if isinstance(concat_result, dict):
            for key, value in concat_result.items():
                if key in ["strategy_used", "success", "analysis", "recommendation"]:
                    print(f"  {key.replace('_', ' ').title()}: {value}")
        
    except Exception as e:
        stage_time = time.time() - stage_start
        test_results["performance"]["smart_concat"] = stage_time
        test_results["tests"]["smart_concat"] = {
            "success": False,
            "error": str(e),
            "time_seconds": stage_time
        }
        print(f"❌ Smart concatenation failed in {stage_time:.3f}s: {e}")
    
    # Final performance analysis
    total_time = time.time() - start_time
    test_results["performance"]["total_time"] = total_time
    
    print(f"\n⏱️ Performance Summary:")
    print(f"  Total time: {total_time:.3f}s")
    for test_name, duration in test_results["performance"].items():
        if test_name != "total_time":
            status = "✅" if test_results["tests"].get(test_name, {}).get("success", False) else "❌"
            print(f"  {test_name.replace('_', ' ').title()}: {duration:.3f}s {status}")
    
    # Save results
    with open("haiku_mcp_bridge_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n📄 Results saved: haiku_mcp_bridge_test_results.json")
    
    # Generate improvement analysis
    improvements = analyze_haiku_mcp_performance(test_results)
    
    return test_results

def analyze_haiku_mcp_performance(test_results):
    """Analyze Haiku MCP bridge performance and suggest improvements"""
    
    print(f"\n🔍 HAIKU MCP BRIDGE PERFORMANCE ANALYSIS")
    print("="*60)
    
    improvements = []
    performance = test_results["performance"]
    tests = test_results["tests"]
    
    # Speed analysis
    print("⚡ Speed Analysis:")
    for test_name, duration in performance.items():
        if test_name != "total_time":
            if duration > 2.0:
                status = "❌ Slow"
                improvements.append({
                    "test": test_name,
                    "issue": f"Takes {duration:.3f}s (>2.0s threshold)",
                    "solution": "Optimize async operations and caching"
                })
            elif duration > 0.5:
                status = "⚠️ Medium"
            else:
                status = "✅ Fast"
            
            success = "✅" if tests.get(test_name, {}).get("success", False) else "❌"
            print(f"  {test_name.replace('_', ' ').title()}: {duration:.3f}s {status} {success}")
    
    print(f"\n📊 Total Processing: {performance['total_time']:.3f}s")
    
    # Success rate analysis
    successful_tests = sum(1 for test in tests.values() if test.get("success", False))
    total_tests = len(tests)
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n📈 Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate < 100:
        print("❌ Failed Tests:")
        for test_name, test_result in tests.items():
            if not test_result.get("success", False):
                print(f"  - {test_name}: {test_result.get('error', 'Unknown error')}")
                improvements.append({
                    "test": test_name,
                    "issue": f"Test failed: {test_result.get('error', 'Unknown')}",
                    "solution": "Check MCP server integration and error handling"
                })
    
    # Quality analysis based on results
    print(f"\n📝 Quality Analysis:")
    for test_name, test_result in tests.items():
        if test_result.get("success", False):
            result_data = test_result.get("result", {})
            if isinstance(result_data, dict):
                result_size = len(json.dumps(result_data))
                print(f"  {test_name}: {result_size} chars data")
                
                # Check for meaningful content
                if result_size < 100:
                    improvements.append({
                        "test": test_name,
                        "issue": f"Small result size ({result_size} chars)",
                        "solution": "Enhance response detail and information content"
                    })
    
    # Cost effectiveness analysis
    cost_test = tests.get("cost_status", {})
    if cost_test.get("success", False):
        cost_result = cost_test.get("result", {})
        daily_spend = cost_result.get("daily_spend", 0)
        daily_limit = cost_result.get("daily_limit", 5.0)
        
        print(f"\n💰 Cost Analysis:")
        print(f"  Daily spend: ${daily_spend:.4f} / ${daily_limit:.2f}")
        print(f"  Usage: {(daily_spend/daily_limit)*100:.1f}% of budget")
        
        if daily_spend / daily_limit > 0.8:
            improvements.append({
                "test": "cost_management",
                "issue": f"High budget usage ({(daily_spend/daily_limit)*100:.1f}%)",
                "solution": "Implement more aggressive cost controls and caching"
            })
    
    # Improvement recommendations
    if improvements:
        print(f"\n🛠️ Recommended Improvements ({len(improvements)}):")
        for i, improvement in enumerate(improvements, 1):
            print(f"  {i}. {improvement['test'].replace('_', ' ').title()}")
            print(f"     Issue: {improvement['issue']}")
            print(f"     Solution: {improvement['solution']}")
    else:
        print(f"\n✅ Bridge performance is excellent - no improvements needed!")
    
    return improvements

async def create_music_video_description_via_mcp():
    """Create the music video description using MCP bridge results"""
    
    print(f"\n🎬 GENERATING MUSIC VIDEO DESCRIPTION VIA HAIKU MCP BRIDGE")
    print("="*70)
    
    # Get analysis from MCP bridge
    video_files = ["Oa8iS1W3OCM.mp4", "3xEMCU1fyl8.mp4", "PLnPZVqiyjA.mp4"]
    
    try:
        # Get strategy analysis
        strategy = await analyze_video_processing_strategy(video_files)
        
        # Generate description based on MCP bridge analysis
        description = f"""🎬 SUBNAUTICA DEEP OCEAN MUSIC VIDEO
Generated via Haiku MCP Bridge Analysis

🤖 HAIKU MCP BRIDGE ANALYSIS:
- Recommended Strategy: {strategy.get('recommended_strategy', 'Unknown')}
- Frame Issues Detected: {strategy.get('has_frame_issues', 'Unknown')}  
- Normalization Needed: {strategy.get('needs_normalization', 'Unknown')}
- Complexity Score: {strategy.get('complexity_score', 0):.2f}/1.0
- Confidence Level: {strategy.get('confidence', 0):.2f}/1.0

💡 MCP REASONING: {strategy.get('reasoning', 'Analysis not available')}

🎯 VIDEO CONCEPT: Subnautica Deep Ocean Exploration
⏱️ FORMAT: YouTube Short (1080x1920, 24 seconds)

🎥 THREE-ACT NARRATIVE STRUCTURE:

Act 1 (0-8s): MYSTERIOUS DEPTHS
- Source: Oa8iS1W3OCM.mp4 (Deep ocean scenes)
- Segments: 01-04 (mysterious, atmospheric)
- MCP Strategy: {strategy.get('recommended_strategy', 'standard_concat')}

Act 2 (8-16s): EXPLORATION ADVENTURE
- Source: 3xEMCU1fyl8.mp4 (Ocean exploration)
- Segments: 05-08 (dynamic, exploratory)
- Processing: Frame alignment {'required' if strategy.get('has_frame_issues') else 'standard'}

Act 3 (16-24s): GAMING IMMERSION
- Source: PLnPZVqiyjA.mp4 (Subnautica gameplay)
- Segments: 09-12 (futuristic, immersive)
- Quality: {'High complexity' if strategy.get('complexity_score', 0) > 0.7 else 'Standard'}

🎵 AUDIO SYNCHRONIZATION:
- Source: Subnautic Measures.flac
- BPM: 120 (perfect for 2-second segments)
- Processing: Fade in/out, volume 0.8

🎨 VISUAL EFFECTS (MCP-Optimized):
- Vignette: Deep ocean atmosphere
- Unsharp filter: Enhanced underwater detail
- Scale: 1080x1920 vertical format
- {'Crossfade transitions' if strategy.get('has_frame_issues') else 'Direct cuts'}

⚡ TECHNICAL SPECS:
- Total segments: 12 × 2 seconds = 24s
- Strategy: {strategy.get('recommended_strategy', 'Unknown')}
- Estimated processing: {strategy.get('estimated_time', 0):.1f}s
- Estimated cost: ${strategy.get('estimated_cost', 0):.4f}

📊 HAIKU MCP CONFIDENCE: {strategy.get('confidence', 0)*100:.0f}%
💎 QUALITY TARGET: Professional YouTube Short with AI-optimized processing"""
        
        # Save the description
        with open("haiku_mcp_music_video_description.txt", "w") as f:
            f.write(description)
        
        print("✅ Music video description generated successfully!")
        print(f"📝 Length: {len(description)} characters")
        print(f"📄 Preview:\n{description[:400]}...")
        print(f"\n💾 Saved: haiku_mcp_music_video_description.txt")
        
        return description
        
    except Exception as e:
        print(f"❌ Failed to generate description via MCP bridge: {e}")
        return None

async def main():
    """Main test function"""
    
    try:
        # Test Haiku MCP bridge integration
        bridge_results = await test_haiku_mcp_tools()
        
        if bridge_results:
            # Generate music video description using MCP bridge
            description = await create_music_video_description_via_mcp()
            
            print(f"\n🎯 HAIKU MCP BRIDGE TEST COMPLETE")
            print(f"📄 Bridge results: haiku_mcp_bridge_test_results.json")
            print(f"🎬 Video description: haiku_mcp_music_video_description.txt")
            
            return True
        else:
            print(f"\n❌ Haiku MCP bridge test failed")
            return False
            
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)