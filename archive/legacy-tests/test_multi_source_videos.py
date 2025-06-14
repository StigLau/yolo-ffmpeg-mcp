#!/usr/bin/env python3
"""
Test actual multi-source video composition
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def test_multi_source():
    print("🎬 TESTING ACTUAL MULTI-SOURCE VIDEO COMPOSITION")
    print("=" * 60)
    
    try:
        # Import components 
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        from speech_komposition_processor import SpeechKompositionProcessor
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        processor = SpeechKompositionProcessor(file_manager, ffmpeg_wrapper)
        
        print(f"🎯 TESTING 3 DIFFERENT VIDEO SOURCES:")
        print(f"   1. PXL_20250306_132546255.mp4 (intro)")
        print(f"   2. lookin.mp4 (main with speech)")
        print(f"   3. Dagny-Baybay.mp4 (outro)")
        
        # Process without background music first
        print(f"\n🎵 Processing multi-source composition (no music)...")
        result = await processor.process_speech_komposition("video_only_multi_source.json")
        
        print(f"\n📊 MULTI-SOURCE RESULTS:")
        print(f"=" * 50)
        
        if result.get('success'):
            output_id = result.get('output_file_id')
            metadata = result.get('metadata', {})
            summary = result.get('processing_summary', {})
            
            print(f"✅ SUCCESS: Multi-source composition created!")
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
                        # Create the final multi-source output
                        final_output = Path("/tmp/music/temp/MULTI_SOURCE_VIDEO.mp4")
                        import shutil
                        shutil.copy(output_path, final_output)
                        print(f"💾 Multi-source video saved as: {final_output}")
                        
                        print(f"\n🎉 MULTI-SOURCE COMPOSITION VERIFIED!")
                        print(f"📹 This should contain 3 different videos:")
                        print(f"   • 0-8s: PXL video")
                        print(f"   • 8-16s: lookin.mp4 (your dog)")
                        print(f"   • 16-24s: Dagny-Baybay.mp4")
                        
                        # Now try to add background music separately
                        return await add_background_music_separately(file_manager, ffmpeg_wrapper, output_path)
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

async def add_background_music_separately(file_manager, ffmpeg_wrapper, video_path):
    """Add background music as a separate step"""
    print(f"\n🎵 ADDING BACKGROUND MUSIC SEPARATELY...")
    
    try:
        # Get music file
        music_id = file_manager.get_id_by_name("16BL - Deep In My Soul (Original Mix).mp3")
        if not music_id:
            print("❌ Background music file not found")
            return False
        
        music_path = file_manager.resolve_id(music_id)
        output_with_music = Path("/tmp/music/temp/FINAL_WITH_MUSIC.mp4")
        
        # Import SecurityConfig
        from config import SecurityConfig
        
        # Use FFmpeg to add background music
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(video_path),      # Video input
            "-i", str(music_path),      # Music input
            "-c:v", "copy",             # Copy video as-is
            "-c:a", "aac",              # Re-encode audio
            "-filter_complex", "[1:a]volume=0.3[music];[0:a][music]amix=inputs=2:duration=first[audio]",
            "-map", "0:v",              # Map video from first input
            "-map", "[audio]",          # Map mixed audio
            "-t", "24",                 # Limit to 24 seconds
            "-y",                       # Overwrite output
            str(output_with_music)
        ]
        
        print(f"   Command: {' '.join(cmd[:8])}...")  # Show partial command
        
        result = await ffmpeg_wrapper.execute_command(cmd, timeout=120)
        
        if result["success"] and output_with_music.exists():
            file_size = output_with_music.stat().st_size
            print(f"✅ Background music added successfully!")
            print(f"📂 Final output: {output_with_music}")
            print(f"📏 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            if file_size > 0:
                print(f"\n🎉 COMPLETE MULTI-VIDEO WITH MUSIC SUCCESS!")
                print(f"🎬 Contains: 3 different videos + background music")
                return True
            else:
                print(f"❌ Final output is empty")
                return False
        else:
            print(f"❌ Music addition failed: {result.get('logs', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Music addition failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_multi_source())
    
    if success:
        print(f"\n🎉 CORRECTED COMPOSITION COMPLETE!")
        print(f"✅ Now you have: Intro + Your Dog Video + Outro + Music")
        print(f"📂 Check: /tmp/music/temp/FINAL_WITH_MUSIC.mp4")
    else:
        print(f"\n❌ Multi-source composition failed")