#!/usr/bin/env python3
"""
Test orientation mismatch issue and create same-orientation comparison
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def analyze_video_properties():
    """Analyze the video properties of each source file"""
    print("🔍 ANALYZING VIDEO PROPERTIES")
    print("=" * 50)
    
    try:
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        
        # Get video files
        videos = [
            "PXL_20250306_132546255.mp4",
            "lookin.mp4", 
            "Dagny-Baybay.mp4"
        ]
        
        for i, video_name in enumerate(videos, 1):
            print(f"\n📹 VIDEO {i}: {video_name}")
            
            video_id = file_manager.get_id_by_name(video_name)
            if not video_id:
                print(f"   ❌ File not found")
                continue
                
            video_path = file_manager.resolve_id(video_id)
            
            # Get video info using ffprobe
            cmd = [
                SecurityConfig.FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(video_path)
            ]
            
            result = await ffmpeg_wrapper.execute_command(cmd, timeout=30)
            
            if result["success"]:
                import json
                try:
                    info = json.loads(result["logs"])
                    
                    # Find video stream
                    video_stream = None
                    for stream in info.get("streams", []):
                        if stream.get("codec_type") == "video":
                            video_stream = stream
                            break
                    
                    if video_stream:
                        width = video_stream.get("width", "unknown")
                        height = video_stream.get("height", "unknown")
                        rotation = video_stream.get("tags", {}).get("rotate", "0")
                        duration = float(video_stream.get("duration", 0))
                        
                        orientation = "Portrait" if height > width else "Landscape"
                        if rotation in ["90", "270"]:
                            orientation = "Landscape" if orientation == "Portrait" else "Portrait"
                        
                        print(f"   📐 Resolution: {width}x{height}")
                        print(f"   🔄 Rotation: {rotation}°")
                        print(f"   📱 Orientation: {orientation}")
                        print(f"   ⏱️  Duration: {duration:.1f}s")
                        
                        if i == 3 and orientation != "Portrait":
                            print(f"   ⚠️  ORIENTATION MISMATCH DETECTED!")
                    else:
                        print(f"   ❌ No video stream found")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Failed to parse video info")
            else:
                print(f"   ❌ Failed to get video info")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

async def test_same_orientation():
    """Test composition with same orientation videos"""
    print(f"\n🎬 TESTING SAME ORIENTATION COMPOSITION")
    print("=" * 50)
    
    try:
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        from speech_komposition_processor import SpeechKompositionProcessor
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        processor = SpeechKompositionProcessor(file_manager, ffmpeg_wrapper)
        
        print(f"🎯 COMPOSITION PLAN (ALL PORTRAIT):")
        print(f"   1. PXL_20250306_132546255.mp4 (0-8s) - Portrait")
        print(f"   2. lookin.mp4 (0-8s) - Portrait")
        print(f"   3. PXL_20250306_132546255.mp4 (8-16s) - Portrait")
        print(f"   Expected: No orientation conflicts")
        
        # Process same-orientation composition
        print(f"\n🎵 Processing same-orientation composition...")
        result = await processor.process_speech_komposition("same_orientation_test.json")
        
        print(f"\n📊 SAME ORIENTATION RESULTS:")
        print(f"=" * 50)
        
        if result.get('success'):
            output_id = result.get('output_file_id')
            metadata = result.get('metadata', {})
            summary = result.get('processing_summary', {})
            
            print(f"✅ SUCCESS: Same orientation composition created!")
            print(f"🎬 Output File ID: {output_id}")
            print(f"⏱️  Duration: {metadata.get('estimatedDuration', 0)}s")
            print(f"📈 Segments processed: {summary.get('segments_processed', 0)}")
            
            # Show output file details
            if output_id:
                output_path = file_manager.resolve_id(output_id)
                if output_path and output_path.exists():
                    file_size = output_path.stat().st_size
                    print(f"📂 Output path: {output_path}")
                    print(f"📏 Output size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
                    
                    if file_size > 0:
                        # Create the same-orientation output
                        final_output = Path("/tmp/music/temp/SAME_ORIENTATION_TEST.mp4")
                        import shutil
                        shutil.copy(output_path, final_output)
                        print(f"💾 Same-orientation video saved as: {final_output}")
                        
                        print(f"\n🎉 SAME ORIENTATION TEST COMPLETE!")
                        print(f"📹 This should show smooth transitions:")
                        print(f"   • 0-8s: PXL video (portrait)")
                        print(f"   • 8-16s: Your dog video (portrait)")
                        print(f"   • 16-24s: PXL video again (portrait)")
                        print(f"🔍 Compare this with MULTI_SOURCE_VIDEO.mp4 to see difference")
                        
                        return True
                    else:
                        print(f"❌ Output file is empty")
                        return False
                else:
                    print(f"❌ Output file not accessible")
                    return False
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ COMPOSITION FAILED: {error}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def compare_results():
    """Compare the orientation results"""
    print(f"\n📊 COMPARING ORIENTATION RESULTS:")
    print("=" * 50)
    
    mixed_file = Path("/tmp/music/temp/MULTI_SOURCE_VIDEO.mp4")
    same_file = Path("/tmp/music/temp/SAME_ORIENTATION_TEST.mp4")
    
    if mixed_file.exists():
        size1 = mixed_file.stat().st_size
        print(f"🔄 MIXED ORIENTATION: {size1:,} bytes")
        print(f"   Issues: Portrait + Portrait + Landscape")
        print(f"   Expected problems: Audio/video desync, artifacts")
    
    if same_file.exists():
        size2 = same_file.stat().st_size
        print(f"✅ SAME ORIENTATION: {size2:,} bytes")
        print(f"   Content: Portrait + Portrait + Portrait")
        print(f"   Expected: Smooth transitions, no artifacts")
        
        return True
    
    return False

async def suggest_orientation_fix():
    """Suggest how to fix the orientation issue"""
    print(f"\n🔧 ORIENTATION FIX RECOMMENDATIONS:")
    print("=" * 50)
    
    print(f"🎯 PROBLEM IDENTIFIED:")
    print(f"   • Videos 1&2: Portrait orientation")
    print(f"   • Video 3: Landscape orientation")
    print(f"   • FFmpeg concatenation fails with mixed orientations")
    
    print(f"\n💡 SOLUTION OPTIONS:")
    print(f"   1. FORCE UNIFORM RESOLUTION:")
    print(f"      - Scale all videos to same resolution (e.g., 1080x1920)")
    print(f"      - Add letterboxing/pillarboxing as needed")
    
    print(f"   2. ROTATE LANDSCAPE VIDEO:")
    print(f"      - Detect orientation mismatch")
    print(f"      - Auto-rotate landscape to portrait")
    
    print(f"   3. STANDARDIZE TO LANDSCAPE:")
    print(f"      - Convert all to landscape format")
    print(f"      - Add black bars for portrait videos")
    
    print(f"\n🛠️  IMPLEMENTATION PLAN:")
    print(f"   • Add video resolution analysis to processor")
    print(f"   • Implement auto-scaling/rotation filters")
    print(f"   • Ensure consistent format before concatenation")

if __name__ == "__main__":
    print("🚀 INVESTIGATING ORIENTATION MISMATCH ISSUE")
    print("=" * 60)
    
    asyncio.run(analyze_video_properties())
    
    success = asyncio.run(test_same_orientation())
    
    if success:
        comparison = asyncio.run(compare_results())
        if comparison:
            print(f"\n🎉 ORIENTATION TEST COMPLETE!")
            print(f"📂 Check both videos:")
            print(f"   • MULTI_SOURCE_VIDEO.mp4 (mixed orientations)")
            print(f"   • SAME_ORIENTATION_TEST.mp4 (all portrait)")
            
            asyncio.run(suggest_orientation_fix())
        else:
            print(f"\n⚠️  Test completed but comparison failed")
    else:
        print(f"\n❌ Orientation test failed")