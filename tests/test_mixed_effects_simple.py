#!/usr/bin/env python3
"""
Simple Mixed Effects Test - demonstrates old-school + blurry effects
"""

import os
import subprocess
import json
from pathlib import Path

def create_mixed_effects_video():
    """Create video with old-school first half, blurry second half"""
    temp_dir = Path("/tmp/music-video-creator")
    temp_dir.mkdir(parents=True, exist_ok=True)
    (temp_dir / "generated-videos").mkdir(parents=True, exist_ok=True)
    
    print("🎬 Creating Mixed Effects Music Video")
    
    # Create 20-second test source
    source = temp_dir / "source_20s.mp4"
    print("📁 Creating 20-second test source...")
    
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', 'testsrc2=duration=20:size=1280x720:rate=25',
        '-c:v', 'libx264', '-t', '20',
        str(source)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create source: {result.stderr}")
        return False
    
    # First half: old-school effects (0-10 seconds)
    segment1 = temp_dir / "segment1_oldschool.mp4"
    print("🎭 Creating first half with old-school effects...")
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(source),
        '-ss', '0', '-t', '10',
        '-vf', 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=20:allf=t,vignette=PI/6',
        '-c:v', 'libx264',
        str(segment1)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create old-school segment: {result.stderr}")
        return False
    
    # Second half: blurry effects (10-20 seconds)  
    segment2 = temp_dir / "segment2_blurry.mp4"
    print("🌫️ Creating second half with blurry effects...")
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(source),
        '-ss', '10', '-t', '10',
        '-vf', 'gblur=sigma=3:steps=1,boxblur=luma_radius=2:luma_power=1',
        '-c:v', 'libx264',
        str(segment2)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create blurry segment: {result.stderr}")
        return False
    
    # Concatenate segments
    concat_file = temp_dir / "concat_list.txt"
    with open(concat_file, 'w') as f:
        f.write(f"file '{segment1}'\n")
        f.write(f"file '{segment2}'\n")
    
    final_video = temp_dir / "generated-videos" / "mixed_effects_final.mp4"
    print("🔗 Concatenating segments...")
    
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', str(concat_file),
        '-c', 'copy',
        str(final_video)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to concatenate: {result.stderr}")
        return False
    
    # Verify output
    if final_video.exists():
        file_size = final_video.stat().st_size
        print(f"✅ Video created! Size: {file_size} bytes")
        print(f"📁 Location: {final_video}")
        
        # Get video info
        info_cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', str(final_video)]
        result = subprocess.run(info_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            duration = float(info['format']['duration'])
            print(f"📊 Duration: {duration:.1f} seconds")
            print(f"📐 Resolution: {info['streams'][0]['width']}x{info['streams'][0]['height']}")
            
            if 19.0 <= duration <= 21.0:
                print("🎊 SUCCESS: Mixed effects video created!")
                print("   ✅ First 10 seconds: Old-school effects (sepia, grain, vignette)")
                print("   ✅ Second 10 seconds: Blurry effects (gaussian + box blur)")
                return True
    
    return False

def main():
    print("🚀 Mixed Effects Test")
    print("=" * 40)
    
    # Check FFmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg available")
    except:
        print("❌ FFmpeg not found")
        return 1
    
    success = create_mixed_effects_video()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 MIXED EFFECTS TEST PASSED!")
        return 0
    else:
        print("💥 MIXED EFFECTS TEST FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())