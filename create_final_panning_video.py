#!/usr/bin/env python3
"""
Create final video with panning video and specific audio requirements:
- Segment 1 (PXL): Music only, no original audio
- Segment 2 (lookin): Speech + background music  
- Segment 3 (panning): Music only, no original audio
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_final_panning_video():
    print("🎬 CREATING FINAL VIDEO WITH PANNING + SPECIFIC AUDIO REQUIREMENTS")
    print("=" * 70)
    
    try:
        # Import components 
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        
        print(f"🎯 FINAL COMPOSITION PLAN:")
        print(f"   1. PXL_20250306_132546255.mp4 (0-8s) - MUSIC ONLY")
        print(f"   2. lookin.mp4 (0-8s) - SPEECH + BACKGROUND MUSIC")
        print(f"   3. panning back and forth.mp4 (0-8s) - MUSIC ONLY")
        print(f"   🎵 Background music plays throughout all segments")
        
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
        
        # Step 1: Create individual segments with specific audio settings
        print(f"\n🎬 STEP 1: CREATING SEGMENTS WITH SPECIFIC AUDIO")
        segments = []
        
        # Segment 1: PXL with music only (no original audio)
        print(f"\n📹 Creating Segment 1: PXL (music only)")
        pxl_path = file_manager.resolve_id(file_ids["PXL"])
        music_path = file_manager.resolve_id(file_ids["music"])
        
        segment1_output = Path("/tmp/music/temp/segment1_pxl_music_only.mp4")
        
        cmd1 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(pxl_path),        # Video input
            "-i", str(music_path),      # Music input
            "-ss", "0", "-t", "8",      # Trim video to 8 seconds
            "-c:v", "libx264",          # Video codec
            "-c:a", "aac",              # Audio codec
            "-map", "0:v",              # Map video from first input
            "-map", "1:a",              # Map audio from music (second input)
            "-filter:a", "volume=0.5",  # Music volume
            "-y",
            str(segment1_output)
        ]
        
        result1 = await ffmpeg_wrapper.execute_command(cmd1, timeout=120)
        if result1["success"] and segment1_output.exists():
            print(f"   ✅ Segment 1 created: {segment1_output.stat().st_size:,} bytes")
            segments.append(segment1_output)
        else:
            print(f"   ❌ Segment 1 failed")
            return False
        
        # Segment 2: lookin with speech + background music
        print(f"\n📹 Creating Segment 2: lookin (speech + background music)")
        lookin_path = file_manager.resolve_id(file_ids["lookin"])
        
        segment2_output = Path("/tmp/music/temp/segment2_lookin_speech_music.mp4")
        
        cmd2 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(lookin_path),     # Video with original audio
            "-i", str(music_path),      # Music input
            "-ss", "0", "-t", "8",      # Trim video to 8 seconds  
            "-c:v", "libx264",          # Video codec
            "-c:a", "aac",              # Audio codec
            "-filter_complex", "[1:a]volume=0.2[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[out]",
            "-map", "0:v",              # Map video
            "-map", "[out]",            # Map mixed audio
            "-y",
            str(segment2_output)
        ]
        
        result2 = await ffmpeg_wrapper.execute_command(cmd2, timeout=120)
        if result2["success"] and segment2_output.exists():
            print(f"   ✅ Segment 2 created: {segment2_output.stat().st_size:,} bytes")
            segments.append(segment2_output)
        else:
            print(f"   ❌ Segment 2 failed")
            return False
        
        # Segment 3: panning with music only (no original audio)
        print(f"\n📹 Creating Segment 3: panning (music only)")
        panning_path = file_manager.resolve_id(file_ids["panning"])
        
        segment3_output = Path("/tmp/music/temp/segment3_panning_music_only.mp4")
        
        cmd3 = [
            SecurityConfig.FFMPEG_PATH,
            "-i", str(panning_path),    # Video input
            "-i", str(music_path),      # Music input  
            "-ss", "0", "-t", "8",      # Trim video to 8 seconds
            "-c:v", "libx264",          # Video codec
            "-c:a", "aac",              # Audio codec
            "-map", "0:v",              # Map video from first input
            "-map", "1:a",              # Map audio from music (second input)
            "-filter:a", "volume=0.5",  # Music volume
            "-y",
            str(segment3_output)
        ]
        
        result3 = await ffmpeg_wrapper.execute_command(cmd3, timeout=120)
        if result3["success"] and segment3_output.exists():
            print(f"   ✅ Segment 3 created: {segment3_output.stat().st_size:,} bytes")
            segments.append(segment3_output)
        else:
            print(f"   ❌ Segment 3 failed")
            return False
        
        # Step 2: Concatenate all segments
        print(f"\n🔗 STEP 2: CONCATENATING SEGMENTS")
        
        if len(segments) != 3:
            print(f"❌ Expected 3 segments, got {len(segments)}")
            return False
        
        # Create concat list
        concat_list = Path("/tmp/music/temp/final_concat_list.txt")
        with open(concat_list, 'w') as f:
            for segment in segments:
                f.write(f"file '{segment}'\n")
        
        final_output = Path("/tmp/music/temp/FINAL_PANNING_VIDEO.mp4")
        
        cmd_concat = [
            SecurityConfig.FFMPEG_PATH,
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",  # Copy streams (should work now with consistent format)
            "-y",
            str(final_output)
        ]
        
        print(f"   🔗 Concatenating 3 segments...")
        
        result_concat = await ffmpeg_wrapper.execute_command(cmd_concat, timeout=180)
        
        if result_concat["success"] and final_output.exists():
            file_size = final_output.stat().st_size
            print(f"   ✅ Final concatenation successful: {file_size:,} bytes")
            
            print(f"\n🎉 FINAL PANNING VIDEO COMPLETE!")
            print(f"📂 Output: {final_output}")
            print(f"📏 Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            print(f"\n🎵 AUDIO CONFIGURATION:")
            print(f"   • 0-8s: PXL video with music only (no original audio)")
            print(f"   • 8-16s: Your dog video with speech + background music")
            print(f"   • 16-24s: Panning video with music only (no original audio)")
            
            print(f"\n📊 EXPECTED RESULTS:")
            print(f"   ✅ Segments 1&3: Only background music audible")
            print(f"   ✅ Segment 2: Your dog's speech + background music")
            print(f"   ✅ Smooth video transitions")
            print(f"   ✅ Consistent audio throughout")
            
            return True
        else:
            print(f"   ❌ Final concatenation failed")
            return False
        
    except Exception as e:
        print(f"❌ Final panning video creation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 CREATING FINAL VIDEO WITH PANNING AND SPECIFIC AUDIO REQUIREMENTS")
    print("=" * 70)
    
    success = asyncio.run(create_final_panning_video())
    
    if success:
        print(f"\n🎉 FINAL PANNING VIDEO CREATION SUCCESSFUL!")
        print(f"✅ Created with exact audio requirements:")
        print(f"   • Segments 1&3: Music only, no original audio")
        print(f"   • Segment 2: Speech preserved + background music")
        print(f"📂 Check: /tmp/music/temp/FINAL_PANNING_VIDEO.mp4")
    else:
        print(f"\n❌ Final panning video creation failed")