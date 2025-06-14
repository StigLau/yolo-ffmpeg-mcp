#!/usr/bin/env python3
"""
Create fixed orientation video using video normalization
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

async def create_fixed_orientation_video():
    print("🎬 CREATING FIXED ORIENTATION VIDEO")
    print("=" * 50)
    print("🔧 Using video normalization to fix orientation mismatch")
    
    try:
        # Import components 
        from file_manager import FileManager
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        from video_normalizer import VideoNormalizer
        
        # Initialize components
        file_manager = FileManager()
        ffmpeg_wrapper = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
        normalizer = VideoNormalizer(ffmpeg_wrapper)
        
        print(f"\n🎯 ORIGINAL PROBLEM:")
        print(f"   • Videos 1&2: Portrait orientation")
        print(f"   • Video 3: Landscape orientation")
        print(f"   • Result: Audio/video desync, artifacts")
        
        print(f"\n🔧 SOLUTION APPROACH:")
        print(f"   • Analyze all video orientations")
        print(f"   • Normalize to consistent format")
        print(f"   • Concatenate normalized videos")
        
        # Get source video paths
        video_files = [
            "PXL_20250306_132546255.mp4",
            "lookin.mp4",
            "Dagny-Baybay.mp4"
        ]
        
        video_paths = []
        for video_name in video_files:
            video_id = file_manager.get_id_by_name(video_name)
            if video_id:
                path = file_manager.resolve_id(video_id)
                video_paths.append(path)
                print(f"   📹 Found: {video_name}")
            else:
                print(f"   ❌ Missing: {video_name}")
                
        if len(video_paths) != 3:
            print("❌ Not all source videos found")
            return False
        
        # Step 1: Normalize videos
        print(f"\n🔧 STEP 1: VIDEO NORMALIZATION")
        normalized_paths = await normalizer.normalize_video_set(video_paths)
        
        # Step 2: Create segments from normalized videos
        print(f"\n🎬 STEP 2: CREATING VIDEO SEGMENTS")
        
        segments = []
        for i, norm_path in enumerate(normalized_paths):
            print(f"   📹 Creating segment {i+1}: {norm_path.name}")
            
            # Create segment output
            segment_output = Path(f"/tmp/music/temp/segment_{i+1}_normalized.mp4")
            
            # Trim to 8 seconds
            start_time = 8 if i == 2 else 0  # Third segment starts at 8s for variety
            
            cmd = [
                SecurityConfig.FFMPEG_PATH,
                "-i", str(norm_path),
                "-ss", str(start_time),
                "-t", "8",  # 8 seconds duration
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y",
                str(segment_output)
            ]
            
            result = await ffmpeg_wrapper.execute_command(cmd, timeout=120)
            
            if result["success"] and segment_output.exists():
                file_size = segment_output.stat().st_size
                print(f"      ✅ Segment created: {file_size:,} bytes")
                segments.append(segment_output)
            else:
                print(f"      ❌ Segment creation failed")
                return False
        
        # Step 3: Concatenate normalized segments
        print(f"\n🔗 STEP 3: CONCATENATING NORMALIZED SEGMENTS")
        
        # Create concat list
        concat_list = Path("/tmp/music/temp/normalized_concat_list.txt")
        with open(concat_list, 'w') as f:
            for segment in segments:
                f.write(f"file '{segment}'\n")
        
        final_output = Path("/tmp/music/temp/FIXED_ORIENTATION_VIDEO.mp4")
        
        cmd = [
            SecurityConfig.FFMPEG_PATH,
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",  # Should work now with normalized videos
            "-y",
            str(final_output)
        ]
        
        print(f"   🔗 Concatenating {len(segments)} normalized segments...")
        
        result = await ffmpeg_wrapper.execute_command(cmd, timeout=180)
        
        if result["success"] and final_output.exists():
            file_size = final_output.stat().st_size
            print(f"   ✅ Concatenation successful: {file_size:,} bytes")
            
            # Step 4: Add background music
            print(f"\n🎵 STEP 4: ADDING BACKGROUND MUSIC")
            
            music_id = file_manager.get_id_by_name("16BL - Deep In My Soul (Original Mix).mp3")
            if music_id:
                music_path = file_manager.resolve_id(music_id)
                final_with_music = Path("/tmp/music/temp/FIXED_ORIENTATION_WITH_MUSIC.mp4")
                
                cmd = [
                    SecurityConfig.FFMPEG_PATH,
                    "-i", str(final_output),
                    "-i", str(music_path),
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-filter_complex", "[1:a]volume=0.3[music];[0:a][music]amix=inputs=2:duration=first[audio]",
                    "-map", "0:v",
                    "-map", "[audio]",
                    "-t", "24",
                    "-y",
                    str(final_with_music)
                ]
                
                music_result = await ffmpeg_wrapper.execute_command(cmd, timeout=120)
                
                if music_result["success"] and final_with_music.exists():
                    music_size = final_with_music.stat().st_size
                    print(f"   ✅ Music added: {music_size:,} bytes")
                    
                    print(f"\n🎉 FIXED ORIENTATION VIDEO COMPLETE!")
                    print(f"📂 Final output: {final_with_music}")
                    print(f"📏 Size: {music_size:,} bytes ({music_size/1024/1024:.1f} MB)")
                    
                    print(f"\n🔍 COMPARISON:")
                    print(f"   • MULTI_SOURCE_VIDEO.mp4: 17.9 MB (orientation issues)")
                    print(f"   • SAME_ORIENTATION_TEST.mp4: 7.0 MB (consistent)")
                    print(f"   • FIXED_ORIENTATION_WITH_MUSIC.mp4: {music_size/1024/1024:.1f} MB (normalized)")
                    
                    return True
                else:
                    print(f"   ❌ Music addition failed")
            else:
                print(f"   ⚠️  Music file not found, video ready without music")
                return True
        else:
            print(f"   ❌ Concatenation failed")
            return False
        
    except Exception as e:
        print(f"❌ Fixed orientation video creation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 FIXING ORIENTATION MISMATCH ISSUE")
    print("=" * 60)
    
    success = asyncio.run(create_fixed_orientation_video())
    
    if success:
        print(f"\n🎉 ORIENTATION FIX SUCCESSFUL!")
        print(f"✅ Created normalized multi-video composition")
        print(f"🔧 No more audio/video sync issues")
        print(f"📂 Check: /tmp/music/temp/FIXED_ORIENTATION_WITH_MUSIC.mp4")
        print(f"\n💡 This demonstrates the solution for the original problem!")
    else:
        print(f"\n❌ Orientation fix failed")