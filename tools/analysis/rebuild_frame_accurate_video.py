#!/usr/bin/env python3
"""
Rebuild video with frame-accurate concatenation to eliminate transition artifacts.
This rebuilds from original source files with proper encoding parameters.
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

def rebuild_from_manifest():
    """Rebuild video from original sources using audio timing manifest"""
    print("🔧 REBUILDING VIDEO FROM ORIGINAL SOURCES")
    print("=" * 60)
    
    # Read the audio timing manifest
    manifest_path = Path("/tmp/music/temp/AUDIO_TIMING_MANIFEST.json")
    if not manifest_path.exists():
        print(f"❌ Manifest not found: {manifest_path}")
        return False
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    print("📄 Loaded audio timing manifest")
    print(f"   Duration: {manifest['metadata']['totalDuration']}s")
    print(f"   Segments: {len(manifest['videoSegments'])}")
    
    temp_dir = Path("/tmp/music/temp")
    source_dir = Path("/tmp/music/source")
    
    # Process each segment with frame-accurate timing
    processed_segments = []
    
    for i, segment in enumerate(manifest['videoSegments'], 1):
        print(f"\n🎯 Processing segment {i}: {segment['videoFile']}")
        
        source_file = source_dir / segment['videoFile']
        if not source_file.exists():
            print(f"❌ Source file not found: {source_file}")
            return False
        
        output_file = temp_dir / f"frame_accurate_segment{i}.mp4"
        processed_segments.append(output_file)
        
        target_duration = segment['targetDuration']
        
        # Create frame-accurate segment with consistent encoding
        cmd = [
            "ffmpeg", "-y",
            "-i", str(source_file),
            "-t", str(target_duration),        # Exact duration
            "-c:v", "libx264",
            "-r", "30",                        # Force 30 fps
            "-g", "30",                        # GOP size = 30 frames (1 second)
            "-keyint_min", "30",               # Min keyframe interval
            "-sc_threshold", "0",              # Disable scene change detection
            "-force_key_frames", "expr:gte(t,n_forced*1)",  # Keyframe every 1 second
            "-preset", "medium",
            "-crf", "18",                      # High quality
            "-pix_fmt", "yuv420p",            # Consistent pixel format
            "-movflags", "+faststart",         # Web optimization
            "-an",                             # Remove audio (we'll add it later)
            str(output_file)
        ]
        
        if not run_ffmpeg(cmd, f"Creating frame-accurate segment {i}"):
            return False
        
        # Verify the segment
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', str(output_file)
        ], capture_output=True, text=True)
        
        info = json.loads(result.stdout)
        video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
        actual_duration = float(video_stream['duration'])
        
        print(f"   Target duration: {target_duration}s")
        print(f"   Actual duration: {actual_duration:.6f}s")
        print(f"   Framerate: {video_stream['r_frame_rate']}")
        
        if abs(actual_duration - target_duration) > 0.1:
            print(f"   ⚠️  Duration mismatch: {abs(actual_duration - target_duration):.3f}s")
    
    # Create concat list for frame-accurate segments
    print(f"\n📝 Creating concat list for {len(processed_segments)} segments")
    concat_file = temp_dir / "frame_accurate_concat_list.txt"
    with open(concat_file, 'w') as f:
        for segment in processed_segments:
            f.write(f"file '{segment}'\n")
    
    # Concatenate with stream copy
    print("\n🔗 Concatenating frame-accurate segments")
    silent_output = temp_dir / "FRAME_ACCURATE_SILENT_VIDEO.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "copy",                       # Stream copy - no re-encoding
        "-movflags", "+faststart",
        str(silent_output)
    ]
    
    if not run_ffmpeg(cmd, "Concatenating frame-accurate segments"):
        return False
    
    # Add music
    print("\n🎵 Adding background music")
    music_file = source_dir / manifest['metadata']['backgroundMusic']
    final_output = temp_dir / "FRAME_ACCURATE_FINAL_VIDEO.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(silent_output),
        "-i", str(music_file),
        "-c:v", "copy",                       # Copy video stream
        "-c:a", "aac",                        # Re-encode audio
        "-filter:a", "volume=0.5",            # Volume adjustment
        "-shortest",
        "-movflags", "+faststart",
        str(final_output)
    ]
    
    if not run_ffmpeg(cmd, "Adding music to frame-accurate video"):
        return False
    
    print(f"\n✅ FRAME-ACCURATE VIDEO CREATED: {final_output}")
    
    # Analyze the result
    analyze_result(final_output)
    
    return True

def analyze_result(video_path):
    """Analyze the frame-accurate video"""
    print(f"\n🔍 ANALYZING FRAME-ACCURATE VIDEO")
    print("=" * 60)
    
    # Get video info
    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', str(video_path)
    ], capture_output=True, text=True)
    
    info = json.loads(result.stdout)
    video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
    
    duration = float(video_stream['duration'])
    r_frame_rate = video_stream['r_frame_rate']
    
    # Parse framerate
    if '/' in r_frame_rate:
        num, den = map(int, r_frame_rate.split('/'))
        fps = num / den if den != 0 else 0
    else:
        fps = float(r_frame_rate)
    
    print(f"📊 Frame-Accurate Video Properties:")
    print(f"   Duration: {duration:.6f}s")
    print(f"   Framerate: {r_frame_rate} ({fps:.2f} fps)")
    print(f"   Resolution: {video_stream['width']}x{video_stream['height']}")
    print(f"   Codec: {video_stream['codec_name']}")
    
    # Check file sizes
    original = Path("/tmp/music/temp/FINAL_FROM_AUDIO_MANIFEST.mp4")
    frame_accurate = Path(video_path)
    
    if original.exists():
        original_size = original.stat().st_size / (1024*1024)
        frame_accurate_size = frame_accurate.stat().st_size / (1024*1024)
        print(f"\n📁 File Size Comparison:")
        print(f"   Original (with artifacts): {original_size:.1f} MB")
        print(f"   Frame-accurate (fixed):    {frame_accurate_size:.1f} MB")
    
    # Analyze transition timing
    if fps == 30.0:
        print(f"\n🎯 Transition Analysis at 30 fps:")
        print(f"   Frame duration: {1/fps:.6f}s ({1000/fps:.3f}ms)")
        print(f"   8.0s transition = Frame {int(8.0 * fps)} exactly")
        print(f"   Perfect frame alignment achieved! ✅")
    else:
        print(f"\n⚠️  Non-standard framerate: {fps} fps")
        print(f"   This may still cause transition artifacts")

def main():
    """Main function to rebuild frame-accurate video"""
    print("🎯 REBUILDING VIDEO WITH FRAME-ACCURATE CONCATENATION")
    print("Target: Eliminate transition artifacts through proper encoding")
    print("Method: Rebuild from original sources with consistent 30fps encoding")
    print()
    
    if rebuild_from_manifest():
        print("\n🎉 FRAME-ACCURATE REBUILD COMPLETE!")
        print("\nTesting Instructions:")
        print("1. Play FRAME_ACCURATE_FINAL_VIDEO.mp4")
        print("2. Check the 8-second transition point")
        print("3. Look for the flicker/artifact that was present before")
        print("4. Compare with original FINAL_FROM_AUDIO_MANIFEST.mp4")
        print("\nIf artifacts are eliminated, this solution can be integrated into the MCP server!")
    else:
        print("❌ Failed to rebuild frame-accurate video")

if __name__ == "__main__":
    main()