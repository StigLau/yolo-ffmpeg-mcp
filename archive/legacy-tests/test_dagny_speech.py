#!/usr/bin/env python3
"""
Test speech detection on the Dagny singing video
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

from server import list_files, detect_speech_segments, get_speech_insights

async def test_dagny_speech_detection():
    print("🎤 Testing Speech Detection on Dagny Singing Video")
    print("=" * 60)
    
    try:
        # Get file list
        print("📁 Getting available files...")
        files_result = await list_files()
        
        if not files_result:
            print("❌ Failed to get file list")
            return
        
        # Find Dagny video
        dagny_file = None
        print(f"📋 Found {len(files_result.get('files', []))} files:")
        
        for file_info in files_result.get('files', []):
            file_name = file_info.name if hasattr(file_info, 'name') else str(file_info)
            file_id = file_info.id if hasattr(file_info, 'id') else None
            
            print(f"  - {file_name}")
            
            if 'Dagny' in file_name or 'dagny' in file_name.lower():
                dagny_file = {'name': file_name, 'id': file_id}
                print(f"    🎯 Target file found! ID: {file_id}")
        
        if not dagny_file:
            print("❌ Dagny video not found in available files")
            return
        
        print(f"\n🎵 Testing speech detection on: {dagny_file['name']}")
        print("-" * 40)
        
        # Test speech detection
        print("🔍 Running speech detection...")
        speech_result = await detect_speech_segments(
            dagny_file['id'],
            threshold=0.3,  # Lower threshold for singing
            min_speech_duration=100,  # Shorter minimum for music
            min_silence_duration=50
        )
        
        print("\n📊 Speech Detection Results:")
        print(f"✅ Success: {speech_result.get('success', False)}")
        
        if speech_result.get('success'):
            print(f"🎤 Has speech: {speech_result.get('has_speech', False)}")
            print(f"📈 Segments found: {len(speech_result.get('speech_segments', []))}")
            print(f"⏱️  Total speech duration: {speech_result.get('total_speech_duration', 0):.2f}s")
            
            metadata = speech_result.get('analysis_metadata', {})
            print(f"🔧 Engine used: {metadata.get('engine_used', 'unknown')}")
            
            # Show segment details
            segments = speech_result.get('speech_segments', [])
            if segments:
                print(f"\n🎯 Speech Segments Details:")
                for i, segment in enumerate(segments[:5]):  # Show first 5
                    start = segment.get('start_time', 0)
                    end = segment.get('end_time', 0)
                    duration = segment.get('duration', 0)
                    quality = segment.get('audio_quality', 'unknown')
                    print(f"  {i+1}. {start:.2f}s - {end:.2f}s ({duration:.2f}s) [{quality}]")
                
                if len(segments) > 5:
                    print(f"  ... and {len(segments) - 5} more segments")
            
            # Test insights
            print(f"\n🧠 Getting speech insights...")
            insights_result = await get_speech_insights(dagny_file['id'])
            
            if insights_result.get('success'):
                summary = insights_result.get('summary', {})
                print(f"📊 Insights Summary:")
                print(f"  • Average segment: {summary.get('average_segment_duration', 0):.2f}s")
                print(f"  • Longest segment: {summary.get('longest_segment', 0):.2f}s")
                print(f"  • Shortest segment: {summary.get('shortest_segment', 0):.2f}s")
                
                quality_dist = insights_result.get('quality_distribution', {})
                print(f"  • Quality distribution: {dict(quality_dist)}")
                
                suggestions = insights_result.get('editing_suggestions', [])
                if suggestions:
                    print(f"💡 Editing Suggestions:")
                    for suggestion in suggestions[:3]:  # Show first 3
                        msg = suggestion.get('message', '')
                        priority = suggestion.get('priority', 'medium')
                        print(f"  • [{priority}] {msg}")
            else:
                print(f"❌ Insights failed: {insights_result.get('error', 'Unknown error')}")
                
        else:
            error_msg = speech_result.get('error', 'Unknown error')
            print(f"❌ Speech detection failed: {error_msg}")
            
            if 'dependencies not available' in error_msg:
                print("\n💡 Note: This is expected without PyTorch/Silero VAD installed.")
                print("   In Docker environment, all dependencies would be available.")
            
        print("\n" + "=" * 60)
        print("🎉 Speech detection test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dagny_speech_detection())