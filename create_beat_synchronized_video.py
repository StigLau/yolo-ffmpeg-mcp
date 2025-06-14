#!/usr/bin/env python3
"""
Create beat-synchronized video with proper audio handling:
- Video segments stretched to exact beat timing (no gaps)
- Speech audio time-stretched separately before mixing with pristine music
- Background music remains untouched throughout process
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_beat_synchronized_video():
    print("🎬 CREATING BEAT-SYNCHRONIZED VIDEO WITH PROPER AUDIO HANDLING")
    print("=" * 70)
    
    try:
        # Import components 
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        
        print(f"🎯 BEAT-SYNCHRONIZED COMPOSITION PLAN:")
        print(f"   1. PXL video (0-8s exactly) - MUSIC ONLY")
        print(f"   2. lookin video (8-16s exactly) - TIME-STRETCHED SPEECH + PRISTINE MUSIC")
        print(f"   3. panning video (16-24s exactly) - MUSIC ONLY")
        print(f"   🎵 Background music: pristine, never time-stretched")
        
        # Verify all source files exist
        print(f"\n📂 VERIFYING SOURCE FILES:")
        video_files = {
            "PXL": "PXL_20250306_132546255.mp4",
            "lookin": "lookin.mp4", 
            "panning": "panning back and forth.mp4",
            "music": "16BL - Deep In My Soul (Original Mix).mp3"
        }
        
        file_ids = {}
        for name, filename in video_files.items():
            file_id = file_manager.get_id_by_name(filename)
            if file_id:
                file_ids[name] = file_id
                print(f"   ✅ {name}: {filename}")
            else:
                print(f"   ❌ {name}: {filename} - NOT FOUND")
                return False
        
        if len(file_ids) != 4:
            print("❌ Not all source files found")
            return False
        
        # Step 1: Create video segments with exact 8-second timing
        print(f"\n🎬 STEP 1: CREATING VIDEO SEGMENTS (EXACT 8-SECOND TIMING)")
        video_segments = []
        
        # Get file paths
        pxl_path = file_manager.resolve_id(file_ids["PXL"])
        lookin_path = file_manager.resolve_id(file_ids["lookin"])
        panning_path = file_manager.resolve_id(file_ids["panning"])
        music_path = file_manager.resolve_id(file_ids["music"])
        
        # Segment 1: PXL video stretched to exactly 8 seconds (3.567133s → 8s)
        print(f"\n📹 Creating Segment 1: PXL (3.567s → 8s exactly)")
        segment1_video = Path("/tmp/music/temp/segment1_pxl_8s.mp4")
        
        cmd1 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(pxl_path),
            "-vf", "setpts=PTS*2.243",    # Stretch video to 8s (8/3.567133 = 2.243)
            "-af", "atempo=0.5,atempo=0.892",  # Chain atempo filters (0.5 * 0.892 = 0.446)
            "-t", "8",                    # Ensure exactly 8 seconds
            "-c:v", "libx264",
            "-c:a", "aac",
            "-y",
            str(segment1_video)
        ]
        
        result1 = await ffmpeg_wrapper.execute_command(cmd1, timeout=120)
        if result1["success"] and segment1_video.exists():
            print(f"   ✅ PXL video segment: {segment1_video.stat().st_size:,} bytes")
            video_segments.append(segment1_video)
        else:
            print(f"   ❌ PXL segment failed")
            return False
        
        # Segment 2: lookin video stretched to exactly 8 seconds (5.800567s → 8s)
        print(f"\n📹 Creating Segment 2: lookin (5.801s → 8s exactly)")
        segment2_video = Path("/tmp/music/temp/segment2_lookin_8s.mp4")
        
        cmd2 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(lookin_path),
            "-vf", "setpts=PTS*1.379",    # Stretch video to 8s (8/5.800567 = 1.379)
            "-af", "atempo=0.725",        # Slow down audio to match (5.800567/8 = 0.725)
            "-t", "8",                    # Ensure exactly 8 seconds
            "-c:v", "libx264", 
            "-c:a", "aac",
            "-y",
            str(segment2_video)
        ]
        
        result2 = await ffmpeg_wrapper.execute_command(cmd2, timeout=120)
        if result2["success"] and segment2_video.exists():
            print(f"   ✅ lookin video segment: {segment2_video.stat().st_size:,} bytes")
            video_segments.append(segment2_video)
        else:
            print(f"   ❌ lookin segment failed")
            return False
        
        # Segment 3: panning video stretched to exactly 8 seconds (12.262044s → 8s)
        print(f"\n📹 Creating Segment 3: panning (12.262s → 8s exactly)")
        segment3_video = Path("/tmp/music/temp/segment3_panning_8s.mp4")
        
        cmd3 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(panning_path),
            "-vf", "setpts=PTS*0.652",    # Stretch video to 8s (8/12.262044 = 0.652)
            "-af", "atempo=1.533",        # Speed up audio to match (12.262044/8 = 1.533)
            "-t", "8",                    # Ensure exactly 8 seconds
            "-c:v", "libx264",
            "-c:a", "aac", 
            "-y",
            str(segment3_video)
        ]
        
        result3 = await ffmpeg_wrapper.execute_command(cmd3, timeout=120)
        if result3["success"] and segment3_video.exists():
            print(f"   ✅ panning video segment: {segment3_video.stat().st_size:,} bytes")
            video_segments.append(segment3_video)
        else:
            print(f"   ❌ panning segment failed")
            return False
        
        # Step 2: Extract and time-stretch speech audio separately
        print(f"\n🎤 STEP 2: EXTRACTING TIME-STRETCHED SPEECH AUDIO")
        
        # Extract speech from original lookin video (before time-stretching)
        original_speech = Path("/tmp/music/temp/original_speech.wav")
        cmd_extract = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(lookin_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-y",
            str(original_speech)
        ]
        
        result_extract = await ffmpeg_wrapper.execute_command(cmd_extract, timeout=60)
        if not (result_extract["success"] and original_speech.exists()):
            print(f"   ❌ Speech extraction failed")
            return False
        
        # Time-stretch speech to exactly 8 seconds (5.801s → 8s)
        stretched_speech = Path("/tmp/music/temp/stretched_speech_8s.wav")
        cmd_stretch = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(original_speech),
            "-af", "atempo=0.725",  # Adjust speech timing (5.800567s -> 8s)
            "-t", "8",              # Exactly 8 seconds
            "-y",
            str(stretched_speech)
        ]
        
        result_stretch = await ffmpeg_wrapper.execute_command(cmd_stretch, timeout=60)
        if result_stretch["success"] and stretched_speech.exists():
            print(f"   ✅ Time-stretched speech: {stretched_speech.stat().st_size:,} bytes")
        else:
            print(f"   ❌ Speech time-stretching failed")
            return False
        
        # Step 3: Create final compositions with proper audio
        print(f"\n🎵 STEP 3: CREATING FINAL SEGMENTS WITH PROPER AUDIO")
        final_segments = []
        
        # Final Segment 1: PXL video + pristine music
        print(f"\n🎬 Final Segment 1: PXL + pristine music")
        final1 = Path("/tmp/music/temp/final_segment1.mp4")
        
        cmd_final1 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(segment1_video),  # Time-stretched PXL video (silent)
            "-i", str(music_path),      # Pristine music
            "-ss", "0", "-t", "8",      # 8 seconds of music
            "-map", "0:v",              # Video from segment
            "-map", "1:a",              # Audio from music
            "-c:v", "copy",             # Don't re-encode video
            "-c:a", "aac",
            "-filter:a", "volume=0.5",  # Music volume
            "-y",
            str(final1)
        ]
        
        result_final1 = await ffmpeg_wrapper.execute_command(cmd_final1, timeout=120)
        if result_final1["success"] and final1.exists():
            print(f"   ✅ Final segment 1: {final1.stat().st_size:,} bytes")
            final_segments.append(final1)
        else:
            print(f"   ❌ Final segment 1 failed")
            return False
        
        # Final Segment 2: lookin video + time-stretched speech + pristine music
        print(f"\n🎬 Final Segment 2: lookin + stretched speech + pristine music")
        final2 = Path("/tmp/music/temp/final_segment2.mp4")
        
        cmd_final2 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(segment2_video),    # Time-stretched lookin video (silent)
            "-i", str(stretched_speech),  # Time-stretched speech audio
            "-i", str(music_path),        # Pristine music
            "-ss", "0", "-t", "8",        # 8 seconds
            "-filter_complex", "[2:a]volume=0.2[bg];[1:a][bg]amix=inputs=2:duration=first[out]",
            "-map", "0:v",                # Video from segment
            "-map", "[out]",              # Mixed audio (speech + music)
            "-c:v", "copy",               # Don't re-encode video
            "-c:a", "aac",
            "-y",
            str(final2)
        ]
        
        result_final2 = await ffmpeg_wrapper.execute_command(cmd_final2, timeout=120)
        if result_final2["success"] and final2.exists():
            print(f"   ✅ Final segment 2: {final2.stat().st_size:,} bytes")
            final_segments.append(final2)
        else:
            print(f"   ❌ Final segment 2 failed")
            return False
        
        # Final Segment 3: panning video + pristine music
        print(f"\n🎬 Final Segment 3: panning + pristine music")
        final3 = Path("/tmp/music/temp/final_segment3.mp4")
        
        cmd_final3 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(segment3_video),  # Time-stretched panning video (silent)
            "-i", str(music_path),      # Pristine music
            "-ss", "8", "-t", "8",      # 8 seconds of music starting from 8s offset
            "-map", "0:v",              # Video from segment
            "-map", "1:a",              # Audio from music
            "-c:v", "copy",             # Don't re-encode video
            "-c:a", "aac",
            "-filter:a", "volume=0.5",  # Music volume
            "-y",
            str(final3)
        ]
        
        result_final3 = await ffmpeg_wrapper.execute_command(cmd_final3, timeout=120)
        if result_final3["success"] and final3.exists():
            print(f"   ✅ Final segment 3: {final3.stat().st_size:,} bytes")
            final_segments.append(final3)
        else:
            print(f"   ❌ Final segment 3 failed")
            return False
        
        # Step 4: Concatenate all final segments
        print(f"\n🔗 STEP 4: CONCATENATING BEAT-SYNCHRONIZED SEGMENTS")
        
        if len(final_segments) != 3:
            print(f"❌ Expected 3 final segments, got {len(final_segments)}")
            return False
        
        # Create concat list
        concat_list = Path("/tmp/music/temp/beat_sync_concat_list.txt")
        with open(concat_list, 'w') as f:
            for segment in final_segments:
                f.write(f"file '{segment}'\n")
        
        final_output = Path("/tmp/music/temp/BEAT_SYNCHRONIZED_VIDEO.mp4")
        
        cmd_concat = [
            SecurityConfig.FFMPEG_PATH,
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",  # Copy streams (should work with consistent format)
            "-y",
            str(final_output)
        ]
        
        print(f"   🔗 Concatenating 3 beat-synchronized segments...")
        
        result_concat = await ffmpeg_wrapper.execute_command(cmd_concat, timeout=180)
        
        if result_concat["success"] and final_output.exists():
            file_size = final_output.stat().st_size
            print(f"   ✅ Beat synchronization successful: {file_size:,} bytes")
            
            print(f"\n🎉 BEAT-SYNCHRONIZED VIDEO COMPLETE!")
            print(f"📂 Output: {final_output}")
            print(f"📏 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            print(f"\n🎵 BEAT SYNCHRONIZATION FIXES:")
            print(f"   ✅ NO GAPS: Each segment exactly 8 seconds")
            print(f"   ✅ PRISTINE MUSIC: Background music never time-stretched")
            print(f"   ✅ SEPARATE PROCESSING: Speech time-stretched independently")
            print(f"   ✅ PROPER MIXING: Speech + music mixed after individual processing")
            
            print(f"\n📊 TECHNICAL APPROACH:")
            print(f"   • Video segments: Time-stretched to exact 8s using setpts filter")
            print(f"   • Speech audio: Extracted and time-stretched separately using atempo")
            print(f"   • Music audio: Pristine, never modified, only volume adjusted")
            print(f"   • Final mix: Time-stretched speech + pristine music")
            
            return True
        else:
            print(f"   ❌ Final concatenation failed")
            return False
        
    except Exception as e:
        print(f"❌ Beat synchronization failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 CREATING BEAT-SYNCHRONIZED VIDEO WITH PROPER AUDIO HANDLING")
    print("=" * 70)
    
    success = asyncio.run(create_beat_synchronized_video())
    
    if success:
        print(f"\n🎉 BEAT SYNCHRONIZATION SUCCESSFUL!")
        print(f"✅ Fixed timing gaps: Each segment exactly 8 seconds")
        print(f"✅ Fixed audio quality: Speech processed separately, music pristine")
        print(f"📂 Check: /tmp/music/temp/BEAT_SYNCHRONIZED_VIDEO.mp4")
    else:
        print(f"\n❌ Beat synchronization failed")