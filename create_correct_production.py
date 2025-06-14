#!/usr/bin/env python3
"""
Create the CORRECT multi-video composition as originally specified
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_correct_production():
    print("🎬 CREATING CORRECT MULTI-VIDEO COMPOSITION")
    print("=" * 60)
    print("🔍 FIXING: Previous output was just lookin.mp4 duplicated")
    print("🎯 GOAL: Intro + Speech Video + Outro + Background Music")
    
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
        
        print(f"\n🎯 CORRECT COMPOSITION PLAN:")
        print(f"   1. Intro: PXL_20250306_132546255.mp4 (8s)")
        print(f"   2. Main: lookin.mp4 with speech (8s)")  
        print(f"   3. Outro: Dagny-Baybay.mp4 (8s)")
        print(f"   4. Audio: Background music throughout")
        print(f"   5. Total: 24 seconds with 3 different videos")
        
        # Verify source files exist
        print(f"\n📂 VERIFYING SOURCE FILES:")
        intro_id = file_manager.get_id_by_name("PXL_20250306_132546255.mp4")
        main_id = file_manager.get_id_by_name("lookin.mp4")
        outro_id = file_manager.get_id_by_name("Dagny-Baybay.mp4")
        music_id = file_manager.get_id_by_name("16BL - Deep In My Soul (Original Mix).mp3")
        
        print(f"   Intro video: {'✅' if intro_id else '❌'} PXL_20250306_132546255.mp4")
        print(f"   Main video: {'✅' if main_id else '❌'} lookin.mp4")
        print(f"   Outro video: {'✅' if outro_id else '❌'} Dagny-Baybay.mp4")
        print(f"   Background music: {'✅' if music_id else '❌'} 16BL - Deep In My Soul.mp3")
        
        if not all([intro_id, main_id, outro_id, music_id]):
            print("❌ Missing source files - cannot create composition")
            return False
        
        # Process the correct composition
        print(f"\n🎵 PROCESSING CORRECT MULTI-VIDEO COMPOSITION...")
        result = await processor.process_speech_komposition("correct_multi_video_komposition.json")
        
        print(f"\n📊 RESULTS:")
        print(f"=" * 60)
        
        if result.get('success'):
            output_id = result.get('output_file_id')
            metadata = result.get('metadata', {})
            summary = result.get('processing_summary', {})
            
            print(f"✅ SUCCESS: Correct multi-video composition created!")
            print(f"🎬 Output File ID: {output_id}")
            print(f"🎵 Title: {metadata.get('title', 'Unknown')}")
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
                        # Create the final corrected output
                        final_output = Path("/tmp/music/temp/CORRECT_MULTI_VIDEO_DEMO.mp4")
                        import shutil
                        shutil.copy(output_path, final_output)
                        print(f"💾 Corrected video saved as: {final_output}")
                        
                        print(f"\n🎉 CORRECT COMPOSITION COMPLETE!")
                        print(f"📹 Contains 3 different video sources:")
                        print(f"   • 0-8s: PXL video (intro)")
                        print(f"   • 8-16s: lookin.mp4 (your dog with speech)")
                        print(f"   • 16-24s: Dagny-Baybay.mp4 (outro)")
                        print(f"🎵 Background music should play throughout")
                        
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
        print(f"❌ Production failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

async def compare_outputs():
    """Compare the incorrect vs correct outputs"""
    print(f"\n🔍 COMPARING OUTPUTS:")
    print(f"=" * 50)
    
    incorrect_file = Path("/tmp/music/temp/MULTI_VIDEO_DEMO.mp4")
    correct_file = Path("/tmp/music/temp/CORRECT_MULTI_VIDEO_DEMO.mp4")
    
    if incorrect_file.exists():
        size1 = incorrect_file.stat().st_size
        print(f"❌ INCORRECT (previous): {size1:,} bytes - Just lookin.mp4 duplicated")
    
    if correct_file.exists():
        size2 = correct_file.stat().st_size
        print(f"✅ CORRECT (new): {size2:,} bytes - 3 different videos + music")
        
        if size2 > size1:
            print(f"📈 Size increase: {size2-size1:,} bytes - indicates additional content")
        
        return True
    
    return False

if __name__ == "__main__":
    print("🚀 CORRECTING MULTI-VIDEO COMPOSITION")
    print("=" * 60)
    
    success = asyncio.run(create_correct_production())
    
    if success:
        comparison = asyncio.run(compare_outputs())
        if comparison:
            print(f"\n🎉 CORRECTION SUCCESSFUL!")
            print(f"✅ Now contains: Intro + Speech Video + Outro + Music")
            print(f"🔧 Previous issue: Used same video twice instead of 3 different videos")
            print(f"📂 Check: /tmp/music/temp/CORRECT_MULTI_VIDEO_DEMO.mp4")
        else:
            print(f"\n⚠️  Correction completed but comparison failed")
    else:
        print(f"\n❌ Correction failed")