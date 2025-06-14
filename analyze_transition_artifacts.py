#!/usr/bin/env python3
"""
Analyze video transition artifacts and framerate issues.
This script diagnoses frame-accurate timing problems at segment boundaries.
"""
import subprocess
import json
from pathlib import Path

def get_video_info(video_path):
    """Get detailed video information using ffprobe"""
    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def calculate_frame_timing(fps, duration):
    """Calculate frame boundaries for given fps and duration"""
    frame_duration = 1.0 / fps
    frames = []
    current_time = 0.0
    frame_number = 0
    
    while current_time < duration:
        frames.append({
            'frame': frame_number,
            'time': current_time,
            'time_ms': current_time * 1000
        })
        current_time += frame_duration
        frame_number += 1
    
    return frames

def analyze_transition_point(video_path, transition_time=8.0):
    """Analyze frame timing around a specific transition point"""
    print(f"🔍 ANALYZING TRANSITION ARTIFACTS")
    print(f"Video: {video_path}")
    print(f"Transition time: {transition_time}s")
    print("=" * 60)
    
    # Get video info
    info = get_video_info(video_path)
    video_stream = next(s for s in info['streams'] if s['codec_type'] == 'video')
    
    # Parse framerate
    r_frame_rate = video_stream['r_frame_rate']
    avg_frame_rate = video_stream['avg_frame_rate']
    duration = float(video_stream['duration'])
    
    print(f"📊 Video Information:")
    print(f"   Duration: {duration:.6f}s")
    print(f"   r_frame_rate: {r_frame_rate}")
    print(f"   avg_frame_rate: {avg_frame_rate}")
    
    # Calculate actual FPS
    if '/' in r_frame_rate:
        num, den = map(int, r_frame_rate.split('/'))
        fps = num / den if den != 0 else 0
    else:
        fps = float(r_frame_rate)
    
    print(f"   Calculated FPS: {fps:.6f}")
    print()
    
    # Calculate frame timing around transition
    frame_duration = 1.0 / fps if fps > 0 else 0
    print(f"🎬 Frame Timing Analysis:")
    print(f"   Frame duration: {frame_duration:.6f}s ({frame_duration*1000:.3f}ms)")
    
    # Find frames around transition point
    window_start = transition_time - 0.5  # 500ms before
    window_end = transition_time + 0.5    # 500ms after
    
    print(f"   Analyzing window: {window_start:.3f}s - {window_end:.3f}s")
    print()
    
    # Calculate frames in window
    frames = calculate_frame_timing(fps, duration)
    transition_frames = [f for f in frames if window_start <= f['time'] <= window_end]
    
    print(f"🎯 Frames Around Transition ({transition_time}s):")
    for frame in transition_frames:
        marker = " ← TRANSITION" if abs(frame['time'] - transition_time) < frame_duration/2 else ""
        print(f"   Frame {frame['frame']:3d}: {frame['time']:8.6f}s ({frame['time_ms']:8.3f}ms){marker}")
    
    # Find closest frame to transition
    closest_frame = min(transition_frames, key=lambda f: abs(f['time'] - transition_time))
    time_diff = closest_frame['time'] - transition_time
    
    print()
    print(f"🎯 Transition Analysis:")
    print(f"   Target time: {transition_time:.6f}s")
    print(f"   Closest frame: {closest_frame['frame']} at {closest_frame['time']:.6f}s")
    print(f"   Time difference: {time_diff:.6f}s ({time_diff*1000:.3f}ms)")
    
    if abs(time_diff) > frame_duration / 4:
        print(f"   ⚠️  WARNING: Large timing mismatch! Frame is {abs(time_diff*1000):.3f}ms off")
        print(f"   This could cause visible transition artifacts.")
    else:
        print(f"   ✅ Timing looks good - within {frame_duration/4*1000:.3f}ms tolerance")
    
    return {
        'fps': fps,
        'frame_duration': frame_duration,
        'transition_time': transition_time,
        'closest_frame': closest_frame,
        'time_difference': time_diff,
        'problematic': abs(time_diff) > frame_duration / 4
    }

def suggest_fixes(analysis):
    """Suggest fixes for transition timing issues"""
    print()
    print("🔧 SUGGESTED FIXES:")
    print("=" * 60)
    
    if analysis['problematic']:
        print("❌ FRAME TIMING ISSUE DETECTED")
        print()
        print("Root causes:")
        print("1. Framerate mismatch between source videos and final composition")
        print("2. Non-standard framerate (26.75 fps instead of 30 fps)")
        print("3. Imprecise segment timing not aligned to frame boundaries")
        print()
        
        print("Solutions:")
        print("1. 🎯 FORCE CONSISTENT FRAMERATE:")
        print("   ffmpeg -i input.mp4 -r 30 -video_track_timescale 30000 output.mp4")
        print()
        
        print("2. 🎯 FRAME-ACCURATE CONCATENATION:")
        print("   Use precise timing that aligns with frame boundaries")
        frame_duration = analysis['frame_duration']
        target_time = analysis['transition_time']
        
        # Find frame-aligned times
        frame_before = int(target_time / frame_duration) * frame_duration
        frame_after = (int(target_time / frame_duration) + 1) * frame_duration
        
        print(f"   Current transition: {target_time:.6f}s")
        print(f"   Frame-aligned options:")
        print(f"     Before: {frame_before:.6f}s (frame {int(frame_before/frame_duration)})")
        print(f"     After:  {frame_after:.6f}s (frame {int(frame_after/frame_duration)})")
        print()
        
        print("3. 🎯 RE-ENCODE WITH CONSISTENT PARAMETERS:")
        print("   ffmpeg -i input.mp4 -c:v libx264 -r 30 -g 30 -keyint_min 30 \\")
        print("          -force_key_frames 'expr:gte(t,n_forced/2)' output.mp4")
        print()
        
        print("4. 🎯 USE FRAME-ACCURATE TRIMMING:")
        print("   ffmpeg -ss 00:00:07.966667 -i input.mp4 -frames:v 1 frame_at_8s.jpg")
        print("   # 7.966667s = frame 239 at 30fps, closest to 8.0s")
        
    else:
        print("✅ Frame timing looks acceptable")
        print("The artifact might be caused by:")
        print("1. Video compression artifacts")
        print("2. Keyframe placement issues") 
        print("3. Color space conversion")

def main():
    video_path = Path("/tmp/music/temp/FINAL_FROM_AUDIO_MANIFEST.mp4")
    
    if not video_path.exists():
        print(f"❌ Video not found: {video_path}")
        return
    
    # Analyze the 8-second transition point
    analysis = analyze_transition_point(video_path, transition_time=8.0)
    
    # Suggest fixes
    suggest_fixes(analysis)
    
    print()
    print("🎯 NEXT STEPS:")
    print("1. Run this analysis on source videos to compare framerates")
    print("2. Implement frame-accurate concatenation in MCP server")
    print("3. Add framerate normalization to komposition processor")

if __name__ == "__main__":
    main()