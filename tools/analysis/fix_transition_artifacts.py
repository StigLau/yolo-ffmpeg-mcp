#!/usr/bin/env python3
"""
Fix video transition artifacts by implementing frame-accurate concatenation.
"""
import subprocess
import json
from pathlib import Path

def run_ffmpeg(cmd, description="FFmpeg operation"):
    """Run FFmpeg command and return result"""
    print(f"🎬 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    else:
        print(f"✅ Success")
        return True

def fix_concatenation_artifacts():
    """Fix concatenation artifacts by rebuilding with proper frame alignment"""
    print("🔧 FIXING CONCATENATION ARTIFACTS")
    print("=" * 60)
    
    # Define paths
    temp_dir = Path("/tmp/music/temp")
    segments = [
        temp_dir / "final_segment1.mp4",
        temp_dir / "final_segment2.mp4", 
        temp_dir / "final_segment3.mp4"
    ]
    
    # Check if segments exist
    for segment in segments:
        if not segment.exists():
            print(f"❌ Segment not found: {segment}")
            return False
    
    print("📁 Found all segments:")
    for i, segment in enumerate(segments, 1):
        print(f"   Segment {i}: {segment.name}")
    
    # Solution 1: Re-encode all segments to consistent format first
    print("\n🎯 SOLUTION 1: Normalize segments to consistent format")
    
    normalized_segments = []
    for i, segment in enumerate(segments, 1):
        output_file = temp_dir / f"normalized_segment{i}.mp4"
        normalized_segments.append(output_file)
        
        # Re-encode with consistent parameters: 30fps, keyframes every 1 second
        cmd = [
            "ffmpeg", "-y", "-i", str(segment),
            "-c:v", "libx264",
            "-r", "30",                    # Force 30 fps
            "-g", "30",                    # GOP size = 30 frames (1 second at 30fps)
            "-keyint_min", "30",           # Minimum keyframe interval
            "-sc_threshold", "0",          # Disable scene change detection
            "-force_key_frames", "expr:gte(t,n_forced*1)",  # Keyframe every 1 second
            "-preset", "medium",
            "-crf", "18",                  # High quality
            "-pix_fmt", "yuv420p",         # Consistent pixel format
            str(output_file)
        ]
        
        if not run_ffmpeg(cmd, f"Normalizing segment {i}"):
            return False
    
    # Solution 2: Create new concat list with normalized segments
    print("\n📝 Creating concat list with normalized segments")
    concat_file = temp_dir / "normalized_concat_list.txt"
    with open(concat_file, 'w') as f:
        for segment in normalized_segments:
            f.write(f"file '{segment}'\n")
    
    # Solution 3: Concatenate with stream copy (no re-encoding)
    print("\n🔗 Concatenating normalized segments")
    output_file = temp_dir / "FIXED_SILENT_VIDEO_COMPOSITION.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",                      # Stream copy - no re-encoding
        str(output_file)
    ]
    
    if not run_ffmpeg(cmd, "Concatenating normalized segments"):
        return False
    
    # Solution 4: Add music with copy to avoid re-encoding
    print("\n🎵 Adding music with stream copy")
    music_file = Path("/tmp/music/source/16BL - Deep In My Soul (Original Mix).mp3")
    final_output = temp_dir / "FIXED_FINAL_FROM_AUDIO_MANIFEST.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(output_file),
        "-i", str(music_file),
        "-c:v", "copy",                    # Copy video stream
        "-c:a", "aac",                     # Re-encode audio
        "-filter:a", "volume=0.5",         # Volume adjustment
        "-shortest",
        str(final_output)
    ]
    
    if not run_ffmpeg(cmd, "Adding music to fixed video"):
        return False
    
    print(f"\n✅ FIXED VIDEO CREATED: {final_output}")
    return True

def analyze_fixed_video():
    """Analyze the fixed video to verify improvements"""
    print("\n🔍 ANALYZING FIXED VIDEO")
    print("=" * 60)
    
    fixed_video = Path("/tmp/music/temp/FIXED_FINAL_FROM_AUDIO_MANIFEST.mp4")
    if not fixed_video.exists():
        print("❌ Fixed video not found")
        return
    
    # Check framerate
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', str(fixed_video)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
    
    print(f"📊 Fixed Video Properties:")
    print(f"   Duration: {video_stream['duration']}s")
    print(f"   Framerate: {video_stream['r_frame_rate']}")
    print(f"   Avg framerate: {video_stream['avg_frame_rate']}")
    
    # Parse framerate
    r_frame_rate = video_stream['r_frame_rate']
    if '/' in r_frame_rate:
        num, den = map(int, r_frame_rate.split('/'))
        fps = num / den if den != 0 else 0
    else:
        fps = float(r_frame_rate)
    
    print(f"   Calculated FPS: {fps}")
    
    if fps == 30.0:
        print("   ✅ Perfect! Now using standard 30 fps")
    else:
        print(f"   ⚠️  Still non-standard framerate: {fps}")
    
    print(f"\n📁 File sizes:")
    original = Path("/tmp/music/temp/FINAL_FROM_AUDIO_MANIFEST.mp4")
    if original.exists():
        original_size = original.stat().st_size / (1024*1024)
        fixed_size = fixed_video.stat().st_size / (1024*1024)
        print(f"   Original: {original_size:.1f} MB")
        print(f"   Fixed:    {fixed_size:.1f} MB")
    
    return True

def main():
    """Main function to fix transition artifacts"""
    print("🎯 FIXING VIDEO TRANSITION ARTIFACTS")
    print("Target: Remove flicker at 8-second transition point")
    print("Method: Frame-accurate concatenation with consistent encoding")
    print()
    
    # Fix the concatenation
    if fix_concatenation_artifacts():
        analyze_fixed_video()
        
        print("\n🎉 ARTIFACT FIX COMPLETE!")
        print("\nRecommendations:")
        print("1. Test the FIXED_FINAL_FROM_AUDIO_MANIFEST.mp4 file")
        print("2. Check the 8-second transition point for improvements")
        print("3. If artifacts persist, the issue may be in source video encoding")
        print("4. Consider implementing this fix in the MCP server for future builds")
    else:
        print("❌ Failed to fix artifacts")

if __name__ == "__main__":
    main()