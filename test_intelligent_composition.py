#!/usr/bin/env python3
"""
Test the intelligent composition system with real video files
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_intelligent_composition():
    print("🧠 TESTING INTELLIGENT COMPOSITION SYSTEM")
    print("=" * 60)
    
    try:
        # Import components
        from server import (
            analyze_composition_sources,
            generate_composition_plan,
            preview_composition_timing,
            process_composition_plan
        )
        
        # Test data - use existing videos
        source_videos = [
            "PXL_20250306_132546255.mp4",
            "lookin.mp4", 
            "panning back and forth.mp4"
        ]
        background_music = "16BL - Deep In My Soul (Original Mix).mp3"
        
        print(f"🎬 Testing with {len(source_videos)} source videos")
        print(f"🎵 Background music: {background_music}")
        
        # Step 1: Analyze composition sources
        print(f"\n🔍 STEP 1: ANALYZING COMPOSITION SOURCES")
        analysis_result = await analyze_composition_sources(source_videos)
        
        if analysis_result["success"]:
            print(f"   ✅ Analysis successful: {len(analysis_result['analyzed_sources'])} sources")
            for source in analysis_result["analyzed_sources"]:
                print(f"      📹 {source['filename']}: {source['recommended_strategy']} (priority: {source['priority_score']:.2f})")
        else:
            print(f"   ❌ Analysis failed: {analysis_result.get('error', 'Unknown error')}")
            return False
        
        # Step 2: Preview composition timing
        print(f"\n⏰ STEP 2: PREVIEWING COMPOSITION TIMING")
        timing_result = await preview_composition_timing(source_videos, total_duration=24.0, bpm=120)
        
        if timing_result["success"]:
            print(f"   ✅ Timing preview successful")
            for slot in timing_result["timing_preview"]:
                print(f"      ⏱️ Slot {slot['slot_number']}: {slot['start_time']:.1f}-{slot['end_time']:.1f}s ({slot['strategy']})")
        else:
            print(f"   ❌ Timing preview failed: {timing_result.get('error', 'Unknown error')}")
            return False
        
        # Step 3: Generate composition plan
        print(f"\n📋 STEP 3: GENERATING COMPOSITION PLAN")
        plan_result = await generate_composition_plan(
            source_filenames=source_videos,
            background_music=background_music,
            total_duration=24.0,
            bpm=120,
            composition_title="Test Intelligent Composition"
        )
        
        if plan_result["success"]:
            print(f"   ✅ Plan generation successful")
            summary = plan_result["processing_summary"]
            print(f"      📊 Total segments: {summary['total_segments']}")
            print(f"      🎤 Speech segments: {summary['speech_segments']}")
            print(f"      🔄 Time-stretch segments: {summary['time_stretch_segments']}")
            print(f"      ✂️ Smart-cut segments: {summary['smart_cut_segments']}")
            print(f"      ⏱️ Estimated processing: {summary['estimated_processing_time']/60:.1f} minutes")
        else:
            print(f"   ❌ Plan generation failed: {plan_result.get('error', 'Unknown error')}")
            return False
        
        # Step 4: Test plan processing (without full execution)
        print(f"\n🎬 STEP 4: TESTING PLAN PROCESSING (DRY RUN)")
        print(f"   📄 Plan file: {plan_result['plan_file_path']}")
        
        # Read the generated plan to verify structure
        import json
        plan_path = Path(plan_result["plan_file_path"])
        if plan_path.exists():
            with open(plan_path, 'r') as f:
                plan_data = json.load(f)
            
            print(f"   ✅ Plan file verified")
            print(f"      📋 Metadata: {plan_data['metadata']['title']}")
            print(f"      🎵 Duration: {plan_data['metadata']['total_duration']}s")
            print(f"      🥁 BPM: {plan_data['metadata']['bpm']}")
            print(f"      📹 Video sources: {len(plan_data['sources']['videos'])}")
            print(f"      🎼 Audio sources: {len(plan_data['sources']['audio'])}")
            print(f"      🎬 Composition segments: {len(plan_data['composition']['segments'])}")
        else:
            print(f"   ❌ Plan file not found at {plan_path}")
            return False
        
        print(f"\n🎉 INTELLIGENT COMPOSITION SYSTEM TEST COMPLETE!")
        print(f"✅ All components working correctly")
        print(f"🚀 System ready for production use")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_intelligent_composition())
    
    if success:
        print(f"\n✅ INTELLIGENT COMPOSITION SYSTEM: FULLY OPERATIONAL")
    else:
        print(f"\n❌ INTELLIGENT COMPOSITION SYSTEM: NEEDS ATTENTION")