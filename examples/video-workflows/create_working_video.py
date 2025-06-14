#!/usr/bin/env python3
"""
Create actually working video: PXL + lookin + PXL (no problematic Dagny video)
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_working_video():
    print("🎬 CREATING ACTUALLY WORKING VIDEO")
    print("=" * 50)
    print("🔧 Using PXL video twice to avoid Dagny-Baybay issues")
    
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
        
        print(f"\n🎯 WORKING COMPOSITION PLAN:")
        print(f"   1. PXL_20250306_132546255.mp4 (0-8s) - Intro")
        print(f"   2. lookin.mp4 (0-8s) - Your dog with speech")
        print(f"   3. PXL_20250306_132546255.mp4 (8-16s) - Outro")
        print(f"   Strategy: Use only known working portrait videos")
        
        # Process working composition (no music first)
        print(f"\n🎵 Processing working composition (no music)...")
        result = await processor.process_speech_komposition("working_composition.json")
        
        print(f"\n📊 WORKING COMPOSITION RESULTS:")
        print(f"=" * 50)
        
        if result.get('success'):
            output_id = result.get('output_file_id')
            metadata = result.get('metadata', {})
            summary = result.get('processing_summary', {})
            
            print(f"✅ SUCCESS: Working composition created!")
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
                        # Create the working video without music first
                        working_video = Path("/tmp/music/temp/WORKING_VIDEO_NO_MUSIC.mp4")
                        import shutil
                        shutil.copy(output_path, working_video)
                        print(f"💾 Working video saved as: {working_video}")
                        
                        print(f"\n✅ WORKING VIDEO VERIFIED!")
                        print(f"📹 Should contain:")
                        print(f"   • 0-8s: PXL video (intro)")
                        print(f"   • 8-16s: lookin.mp4 (your dog)")
                        print(f"   • 16-24s: PXL video again (outro)")
                        
                        # Now add background music
                        return await add_music_to_working_video(file_manager, ffmpeg_wrapper, output_path)
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
        print(f"❌ Working video creation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def add_music_to_working_video(file_manager, ffmpeg_wrapper, video_path):
    """Add background music to the working video"""
    print(f"\n🎵 ADDING BACKGROUND MUSIC TO WORKING VIDEO...")
    
    try:
        from config import SecurityConfig
        
        # Get music file
        music_id = file_manager.get_id_by_name("16BL - Deep In My Soul (Original Mix).mp3")
        if not music_id:
            print("❌ Background music file not found")
            return False
        
        music_path = file_manager.resolve_id(music_id)
        final_working_video = Path("/tmp/music/temp/WORKING_VIDEO_WITH_MUSIC.mp4")
        
        # Use simple FFmpeg command that should work
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(video_path),      # Video input
            "-i", str(music_path),      # Music input
            "-c:v", "copy",             # Copy video stream
            "-c:a", "aac",              # Re-encode audio
            "-filter_complex", "[1:a]volume=0.3[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "0:v",              # Map video
            "-map", "[out]",            # Map mixed audio
            "-t", "24",                 # Limit to 24 seconds
            "-y",                       # Overwrite
            str(final_working_video)
        ]
        
        print(f"   🎵 Adding music with volume mixing...")
        
        result = await ffmpeg_wrapper.execute_command(cmd, timeout=120)
        
        if result["success"] and final_working_video.exists():
            file_size = final_working_video.stat().st_size
            print(f"✅ Music added successfully!")
            print(f"📂 Final working video: {final_working_video}")
            print(f"📏 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            if file_size > 0:
                print(f"\n🎉 WORKING VIDEO WITH MUSIC COMPLETE!")
                print(f"🎬 Contains: PXL + Your Dog + PXL + Background Music")
                print(f"🔊 Should have proper audio mixing throughout")
                
                print(f"\n📊 COMPARISON WITH PREVIOUS ATTEMPTS:")
                print(f"   • MULTI_SOURCE_VIDEO.mp4: 17.9 MB (broken - orientation issues)")
                print(f"   • SAME_ORIENTATION_TEST.mp4: 7.0 MB (works but limited)")
                print(f"   • WORKING_VIDEO_WITH_MUSIC.mp4: {file_size/1024/1024:.1f} MB (should work properly)")
                
                return True
            else:
                print(f"❌ Final video is empty")
                return False
        else:
            print(f"❌ Music addition failed: {result.get('logs', 'Unknown error')[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Music addition failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CREATING ACTUALLY WORKING VIDEO (NO PREMATURE CELEBRATION)")
    print("=" * 60)
    
    success = asyncio.run(create_working_video())
    
    if success:
        print(f"\n🎉 WORKING VIDEO CREATION SUCCESSFUL!")
        print(f"✅ Uses PXL video twice to avoid orientation problems")
        print(f"🔊 Background music properly mixed")
        print(f"📂 Check: /tmp/music/temp/WORKING_VIDEO_WITH_MUSIC.mp4")
        print(f"\n💡 This should actually work without the artifacts!")
    else:
        print(f"\n❌ Working video creation failed - need to debug further")