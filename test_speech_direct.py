#!/usr/bin/env python3
"""
Direct speech detection test for lookin.mp4
This script tests speech detection capabilities on the host system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_speech_detection_direct():
    print("🎤 Testing Speech Detection on lookin.mp4 (Direct)")
    print("=" * 55)
    
    try:
        # Import speech detector directly
        from speech_detector import SpeechDetector, SPEECH_DEPS_AVAILABLE
        
        print(f"📦 Speech dependencies available: {SPEECH_DEPS_AVAILABLE}")
        
        if not SPEECH_DEPS_AVAILABLE:
            print("❌ Speech dependencies not available on host system")
            print("   This is expected on macOS where PyTorch installation can be challenging")
            print("   Normally this would work in Docker, but we're encountering repository issues")
            print("")
            print("🔧 What would happen with dependencies:")
            print("   1. Load Silero VAD model via torch.hub")
            print("   2. Extract audio from lookin.mp4 to temporary WAV file")
            print("   3. Analyze audio for speech segments using VAD")
            print("   4. Return timestamps and confidence scores")
            print("   5. Generate insights and editing suggestions")
            print("")
            print("💡 Alternative testing approach:")
            print("   • Install PyTorch locally: pip install torch torchaudio")
            print("   • Or fix Docker repository signing issues")
            print("   • Or test on Linux system with working package manager")
            return
        
        # Test file path
        test_file = Path("/tmp/music/source/lookin.mp4")
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return
        
        print(f"📁 Target file: {test_file}")
        print(f"📏 File size: {test_file.stat().st_size:,} bytes ({test_file.stat().st_size/1024/1024:.1f} MB)")
        
        # Initialize speech detector
        print("\n🔧 Initializing speech detection engine...")
        detector = SpeechDetector(primary_engine="silero", fallback_engines=["webrtc"])
        
        # Run speech detection
        print("🔍 Running speech detection analysis...")
        print("   • Using optimized parameters for speech detection")
        print("   • Threshold: 0.4 (moderate sensitivity)")
        print("   • Min speech duration: 200ms")
        print("   • Min silence duration: 100ms")
        
        result = await detector.detect_speech_segments(
            test_file,
            force_reanalysis=True,
            threshold=0.4,
            min_speech_duration=200,
            min_silence_duration=100
        )
        
        print(f"\n📊 SPEECH DETECTION RESULTS:")
        print(f"{'='*50}")
        
        if result.get('success'):
            has_speech = result.get('has_speech', False)
            segments = result.get('speech_segments', [])
            total_duration = result.get('total_speech_duration', 0)
            engine_used = result.get('analysis_metadata', {}).get('engine_used', 'unknown')
            
            print(f"✅ Success: True")
            print(f"🎤 Contains Speech: {has_speech}")
            print(f"📈 Total Segments: {len(segments)}")
            print(f"⏱️  Total Speech Duration: {total_duration:.2f} seconds")
            print(f"🔧 Detection Engine: {engine_used}")
            
            if segments:
                print(f"\n🎯 DETECTED SPEECH SEGMENTS:")
                print(f"{'No.':<3} {'Start':<8} {'End':<8} {'Duration':<8} {'Quality':<8}")
                print("-" * 45)
                
                for i, segment in enumerate(segments[:10]):  # Show first 10
                    start = segment.get('start_time', 0)
                    end = segment.get('end_time', 0)
                    duration = segment.get('duration', 0)
                    quality = segment.get('audio_quality', 'unknown')
                    
                    print(f"{i+1:2d}. {start:6.2f}s  {end:6.2f}s  {duration:6.2f}s  {quality}")
                
                if len(segments) > 10:
                    print(f"     ... and {len(segments) - 10} more segments")
                
                # Generate insights
                print(f"\n🧠 GENERATING INSIGHTS...")
                insights = detector.get_speech_insights(test_file)
                
                if insights.get('success'):
                    summary = insights.get('summary', {})
                    print(f"📈 STATISTICAL SUMMARY:")
                    print(f"  • Average segment duration: {summary.get('average_segment_duration', 0):.2f}s")
                    print(f"  • Longest segment: {summary.get('longest_segment', 0):.2f}s")
                    print(f"  • Shortest segment: {summary.get('shortest_segment', 0):.2f}s")
                    
                    timing = insights.get('timing_analysis', {})
                    if timing:
                        print(f"\n⏰ TIMING ANALYSIS:")
                        print(f"  • Speech density: {timing.get('speech_density', 0):.2%}")
                        print(f"  • Average gap: {timing.get('average_gap', 0):.2f}s")
            else:
                print("ℹ️  No speech segments detected")
                print("   Possible reasons:")
                print("   • Audio contains only music/instrumental content")
                print("   • Detection threshold too high for this audio quality")
                print("   • Speech too quiet or unclear for detection")
        
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ Speech detection failed: {error}")
        
        print(f"\n{'='*55}")
        print("🎉 Speech detection test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   This suggests missing dependencies or path issues")
    except Exception as e:
        print(f"❌ Test failed with exception: {type(e).__name__}: {e}")
        import traceback
        print("\n📋 Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_speech_detection_direct())