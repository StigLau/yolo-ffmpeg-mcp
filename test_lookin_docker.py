#!/usr/bin/env python3
"""
Test speech detection on lookin.mp4 inside Docker container
This script is designed to run inside Docker where all dependencies are available
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append('/app/src')

async def test_lookin_speech_detection():
    print("🎤 Testing Speech Detection on lookin.mp4 in Docker")
    print("=" * 65)
    
    try:
        # Import modules (should work in Docker with dependencies)
        from server import list_files, detect_speech_segments, get_speech_insights
        from speech_detector import SPEECH_DEPS_AVAILABLE
        
        print(f"📦 Speech dependencies available: {SPEECH_DEPS_AVAILABLE}")
        
        if not SPEECH_DEPS_AVAILABLE:
            print("❌ Speech dependencies not available even in Docker!")
            print("This suggests an issue with the Docker build or dependencies.")
            return
        
        # Get file list
        print("\n📁 Getting available files...")
        files_result = await list_files()
        
        if not files_result or not files_result.get('files'):
            print("❌ No files found or failed to get file list")
            return
        
        # Find lookin.mp4
        lookin_file = None
        print(f"📋 Available files ({len(files_result.get('files', []))}):")
        
        for file_info in files_result.get('files', []):
            file_name = file_info.name if hasattr(file_info, 'name') else str(file_info)
            file_id = file_info.id if hasattr(file_info, 'id') else None
            
            print(f"  • {file_name}")
            
            if 'lookin' in file_name.lower():
                lookin_file = {'name': file_name, 'id': file_id}
                print(f"    🎯 TARGET FOUND! ID: {file_id}")
        
        if not lookin_file:
            print("❌ lookin.mp4 not found in available files")
            print("Make sure the file is in /tmp/music/source/ directory")
            return
        
        print(f"\n🎵 Testing speech detection on: {lookin_file['name']}")
        print("=" * 50)
        
        # Test with optimized parameters for speech detection
        print("🔍 Running speech detection with optimized parameters...")
        print("   • Threshold: 0.4 (moderate sensitivity)")
        print("   • Min speech: 200ms")
        print("   • Min silence: 100ms")
        
        speech_result = await detect_speech_segments(
            lookin_file['id'],
            force_reanalysis=True,  # Force fresh analysis
            threshold=0.4,  # Moderate threshold
            min_speech_duration=200,  # 200ms minimum
            min_silence_duration=100   # 100ms silence gaps
        )
        
        print(f"\n📊 SPEECH DETECTION RESULTS:")
        print(f"{'='*50}")
        print(f"✅ Success: {speech_result.get('success', False)}")
        
        if speech_result.get('success'):
            has_speech = speech_result.get('has_speech', False)
            total_segments = len(speech_result.get('speech_segments', []))
            total_duration = speech_result.get('total_speech_duration', 0)
            engine_used = speech_result.get('analysis_metadata', {}).get('engine_used', 'unknown')
            
            print(f"🎤 Contains Speech: {has_speech}")
            print(f"📈 Total Segments: {total_segments}")
            print(f"⏱️  Total Speech Duration: {total_duration:.2f} seconds")
            print(f"🔧 Detection Engine: {engine_used}")
            
            # Show detailed segment information
            segments = speech_result.get('speech_segments', [])
            if segments:
                print(f"\n🎯 SPEECH SEGMENTS DETECTED:")
                print(f"{'No.':<3} {'Start':<8} {'End':<8} {'Duration':<8} {'Quality':<8} {'Conf':<5}")
                print("-" * 50)
                
                for i, segment in enumerate(segments):
                    start = segment.get('start_time', 0)
                    end = segment.get('end_time', 0)
                    duration = segment.get('duration', 0)
                    quality = segment.get('audio_quality', 'unknown')
                    confidence = segment.get('confidence', 0)
                    
                    print(f"{i+1:2d}. {start:6.2f}s  {end:6.2f}s  {duration:6.2f}s  {quality:<8s} {confidence:.2f}")
                    
                    if i >= 19:  # Show first 20 segments
                        remaining = len(segments) - 20
                        if remaining > 0:
                            print(f"     ... and {remaining} more segments")
                        break
                
                # Test insights generation
                print(f"\n🧠 GENERATING SPEECH INSIGHTS...")
                insights_result = await get_speech_insights(lookin_file['id'])
                
                if insights_result.get('success'):
                    print(f"✅ Insights generated successfully")
                    
                    summary = insights_result.get('summary', {})
                    print(f"\n📈 STATISTICAL SUMMARY:")
                    print(f"  • Average segment duration: {summary.get('average_segment_duration', 0):.2f}s")
                    print(f"  • Longest segment: {summary.get('longest_segment', 0):.2f}s") 
                    print(f"  • Shortest segment: {summary.get('shortest_segment', 0):.2f}s")
                    
                    quality_dist = insights_result.get('quality_distribution', {})
                    if quality_dist:
                        print(f"\n🎛️  AUDIO QUALITY DISTRIBUTION:")
                        for quality, count in quality_dist.items():
                            if count > 0:
                                print(f"  • {quality.capitalize()}: {count} segments")
                    
                    timing = insights_result.get('timing_analysis', {})
                    if timing:
                        print(f"\n⏰ TIMING ANALYSIS:")
                        print(f"  • Speech density: {timing.get('speech_density', 0):.2%}")
                        print(f"  • Average gap between segments: {timing.get('average_gap', 0):.2f}s")
                        print(f"  • Longest gap: {timing.get('longest_gap', 0):.2f}s")
                    
                    suggestions = insights_result.get('editing_suggestions', [])
                    if suggestions:
                        print(f"\n💡 INTELLIGENT EDITING SUGGESTIONS:")
                        for i, suggestion in enumerate(suggestions[:5]):  # Show first 5
                            priority = suggestion.get('priority', 'medium').upper()
                            message = suggestion.get('message', '')
                            print(f"  {i+1}. [{priority:6s}] {message}")
                
                else:
                    print(f"❌ Insights generation failed: {insights_result.get('error', 'Unknown error')}")
            
            else:
                print("ℹ️  No speech segments detected in this video")
                print("   This could mean:")
                print("   • The video contains only music/instrumental audio")
                print("   • The speech detection threshold is too high")
                print("   • The audio quality is too low for detection")
                
        else:
            error_msg = speech_result.get('error', 'Unknown error')
            print(f"❌ SPEECH DETECTION FAILED:")
            print(f"   Error: {error_msg}")
            
            if 'dependencies' in error_msg.lower():
                print("\n🔧 Dependency issue detected in Docker environment")
                print("   This suggests the Docker build needs to be fixed")
            
        print(f"\n{'='*65}")
        print("🎉 Speech detection test completed!")
        
        # Show file info for debugging
        print(f"\n📄 FILE INFORMATION:")
        file_path = Path(f"/tmp/music/source/{lookin_file['name']}")
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  • Path: {file_path}")
            print(f"  • Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            print(f"  • Exists: {file_path.exists()}")
        else:
            print(f"  • File not found at expected path: {file_path}")
        
    except Exception as e:
        print(f"❌ TEST FAILED WITH EXCEPTION:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        print(f"\n📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lookin_speech_detection())