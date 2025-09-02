#!/usr/bin/env python3
"""
120 BPM Music Video Creation & LLM Command Comparison Test

REQUIREMENTS:
- 120 BPM tempo (4 beats = 2 seconds per segment)  
- 6 random segments from JJVtt947FfI_136.mp4
- Subnautic Measures.flac as audio
- 1 second white fade transitions between segments
- Leica style filter on all video tracks
- Total length: ~17 seconds (12s video + 5s transitions)

PURPOSE: 
- Test Python FFMPEG MCP implementation
- Document exact parameters for Sonnet/Haiku/Gemini comparison
- Analyze prompt optimization opportunities
"""

import asyncio
import json
import random
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# File paths
VIDEO_SOURCE = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4"
AUDIO_SOURCE = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac"
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/120bpm-music-videos/"
VIDEO_DURATION = 223.88  # seconds

# Music video parameters
BPM = 120
BEATS_PER_SEGMENT = 4
SEGMENT_DURATION = (BEATS_PER_SEGMENT / BPM) * 60  # 2.0 seconds
FADE_DURATION = 1.0  # seconds
NUM_SEGMENTS = 6
TOTAL_VIDEO_LENGTH = (NUM_SEGMENTS * SEGMENT_DURATION) + ((NUM_SEGMENTS - 1) * FADE_DURATION)

def ensure_output_dir():
    """Ensure output directory exists"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def generate_random_segments(video_duration: float, num_segments: int, segment_length: float) -> List[Dict]:
    """Generate random start times for video segments"""
    segments = []
    used_ranges = []  # To avoid overlapping segments
    
    for i in range(num_segments):
        # Find a start time that doesn't overlap with existing segments
        max_attempts = 50
        for attempt in range(max_attempts):
            start_time = random.uniform(0, video_duration - segment_length)
            end_time = start_time + segment_length
            
            # Check for overlap with existing segments
            overlap = any(
                not (end_time <= existing['start'] or start_time >= existing['end'])
                for existing in used_ranges
            )
            
            if not overlap:
                segments.append({
                    'segment_id': i + 1,
                    'start_time': round(start_time, 2),
                    'duration': segment_length,
                    'end_time': round(end_time, 2)
                })
                used_ranges.append({'start': start_time, 'end': end_time})
                break
        else:
            # Fallback if no non-overlapping segment found
            start_time = (video_duration / num_segments) * i
            segments.append({
                'segment_id': i + 1,
                'start_time': round(start_time, 2),
                'duration': segment_length,
                'end_time': round(start_time + segment_length, 2)
            })
    
    return segments

def create_leica_filter_command() -> str:
    """Create FFMPEG filter string for Leica look"""
    # Leica look: slightly desaturated, warm tones, slight vignette
    leica_filter = (
        "colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,"  # Warm color balance
        "eq=contrast=1.1:brightness=0.02:saturation=0.9,"  # Slight contrast/desat
        "vignette=angle=PI/4"  # Subtle vignette
    )
    return leica_filter

async def create_music_video_python_mcp(segments: List[Dict]) -> Dict[str, Any]:
    """Create music video using Python FFMPEG MCP"""
    print("🎬 Creating 120 BPM music video with Python FFMPEG MCP...")
    
    # Import MCP tools
    import sys
    sys.path.insert(0, 'src')
    
    try:
        # Test direct komposition approach first
        from komposition_processor_mcp import KompositionProcessorMCP
        from models import VideoProcessingRequest, VideoProcessingResult
        
        processor = KompositionProcessorMCP()
        
        # Create komposition structure for the music video
        komposition = {
            "timeline": [],
            "metadata": {
                "bpm": BPM,
                "total_duration": TOTAL_VIDEO_LENGTH,
                "segments": len(segments),
                "style": "leica_120bpm"
            },
            "audio": {
                "source": AUDIO_SOURCE,
                "duration": TOTAL_VIDEO_LENGTH
            }
        }
        
        # Add video segments with transitions
        timeline_position = 0
        leica_filter = create_leica_filter_command()
        
        for i, segment in enumerate(segments):
            # Video segment
            komposition["timeline"].append({
                "type": "video",
                "source": VIDEO_SOURCE,
                "start_time": segment['start_time'],
                "duration": segment['duration'],
                "timeline_position": timeline_position,
                "filters": [leica_filter],
                "segment_id": segment['segment_id']
            })
            
            timeline_position += segment['duration']
            
            # Add white fade transition (except after last segment)
            if i < len(segments) - 1:
                komposition["timeline"].append({
                    "type": "transition",
                    "effect": "fade_through_white",
                    "duration": FADE_DURATION,
                    "timeline_position": timeline_position,
                    "transition_id": i + 1
                })
                timeline_position += FADE_DURATION
        
        # Save komposition for analysis
        komposition_file = Path(OUTPUT_DIR) / "120bpm_music_video_komposition.json"
        with open(komposition_file, 'w') as f:
            json.dump(komposition, f, indent=2)
        
        # Process via MCP
        output_file = Path(OUTPUT_DIR) / "120bpm_subnautic_python_mcp.mp4"
        
        start_time = time.time()
        
        # Create video processing request
        request = VideoProcessingRequest(
            input_file=str(komposition_file),
            output_file=str(output_file),
            operation="create_music_video_from_komposition",
            parameters={
                "style": "leica_120bpm",
                "bpm": BPM,
                "segments": segments,
                "transitions": "white_fade",
                "audio_source": AUDIO_SOURCE
            }
        )
        
        result = await processor.process_video_request(request)
        processing_time = time.time() - start_time
        
        return {
            "success": result.success if result else False,
            "output_file": str(output_file),
            "komposition_file": str(komposition_file),
            "processing_time": processing_time,
            "segments_used": segments,
            "komposition": komposition,
            "mcp_result": result.__dict__ if result else None
        }
        
    except Exception as e:
        print(f"❌ MCP processing failed: {e}")
        
        # Fallback to direct FFMPEG command construction
        return await create_music_video_direct_ffmpeg(segments)

async def create_music_video_direct_ffmpeg(segments: List[Dict]) -> Dict[str, Any]:
    """Fallback: Create music video with direct FFMPEG commands"""
    print("🔧 Fallback: Creating music video with direct FFMPEG...")
    
    output_file = Path(OUTPUT_DIR) / "120bpm_subnautic_direct_ffmpeg.mp4"
    leica_filter = create_leica_filter_command()
    
    # Build complex FFMPEG command for the music video
    # This demonstrates what we want LLMs to generate
    
    # Input sources
    inputs = [f'-i "{VIDEO_SOURCE}"', f'-i "{AUDIO_SOURCE}"']
    
    # Build filter graph for segments and transitions
    filter_parts = []
    segment_labels = []
    
    # Extract and filter each segment
    for i, segment in enumerate(segments):
        segment_label = f"seg{i}"
        filter_parts.append(
            f"[0:v]trim=start={segment['start_time']}:duration={SEGMENT_DURATION},"
            f"setpts=PTS-STARTPTS,{leica_filter}[{segment_label}]"
        )
        segment_labels.append(f"[{segment_label}]")
    
    # Create white fade transitions
    transition_labels = []
    for i in range(len(segments) - 1):
        trans_label = f"trans{i}"
        filter_parts.append(
            f"color=white:size=1280x720:duration={FADE_DURATION}[{trans_label}]"
        )
        transition_labels.append(f"[{trans_label}]")
    
    # Concatenate all segments and transitions
    concat_inputs = []
    for i in range(len(segments)):
        concat_inputs.append(segment_labels[i])
        if i < len(transition_labels):
            concat_inputs.append(transition_labels[i])
    
    concat_filter = f"{''.join(concat_inputs)}concat=n={len(concat_inputs)}:v=1:a=0[finalvideo]"
    filter_parts.append(concat_filter)
    
    # Complete filter graph
    filter_complex = ';'.join(filter_parts)
    
    # Audio processing (trim to match video length)
    audio_filter = f"[1:a]atrim=duration={TOTAL_VIDEO_LENGTH}[finalaudio]"
    
    # Complete FFMPEG command
    cmd = [
        'ffmpeg', '-y'
    ] + inputs[0].split()[1:] + inputs[1].split()[1:] + [
        '-filter_complex', f"{filter_complex};{audio_filter}",
        '-map', '[finalvideo]',
        '-map', '[finalaudio]', 
        '-c:v', 'libx264', '-preset', 'medium',
        '-c:a', 'aac', '-b:a', '128k',
        '-pix_fmt', 'yuv420p',
        str(output_file)
    ]
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        processing_time = time.time() - start_time
        
        success = result.returncode == 0 and output_file.exists()
        
        return {
            "success": success,
            "output_file": str(output_file),
            "processing_time": processing_time,
            "segments_used": segments,
            "ffmpeg_command": ' '.join(cmd),
            "ffmpeg_output": result.stderr if not success else "Success",
            "method": "direct_ffmpeg"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "FFMPEG timeout (120s)",
            "method": "direct_ffmpeg"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "direct_ffmpeg"
        }

def create_llm_comparison_prompt() -> str:
    """Create standardized prompt for LLM comparison testing"""
    return f"""Create a 120 BPM music video with the following exact specifications:

REQUIREMENTS:
- Input video: {VIDEO_SOURCE}
- Input audio: {AUDIO_SOURCE}
- Tempo: {BPM} BPM (4 beats = {SEGMENT_DURATION} seconds per segment)
- Structure: {NUM_SEGMENTS} video segments with {FADE_DURATION}s white fade transitions
- Total length: approximately {TOTAL_VIDEO_LENGTH:.1f} seconds
- Video filter: Leica look (warm color balance, slight desaturation, vignette)
- Output format: MP4, H.264, AAC audio, YUV420P pixel format

SEGMENT SELECTION:
Select 6 random segments from the source video, each {SEGMENT_DURATION} seconds long.
Avoid overlapping segments where possible.

TECHNICAL REQUIREMENTS:
1. Extract random video segments with Leica-style color grading
2. Create white fade transitions (1 second each) between segments  
3. Synchronize with Subnautic Measures audio track
4. Ensure smooth playback and consistent quality
5. Output user-compatible format (YUV420P)

Generate the complete FFMPEG command(s) needed to create this music video."""

def document_test_parameters() -> Dict[str, Any]:
    """Document all parameters for reproducible LLM testing"""
    return {
        "test_configuration": {
            "bpm": BPM,
            "beats_per_segment": BEATS_PER_SEGMENT,
            "segment_duration_seconds": SEGMENT_DURATION,
            "num_segments": NUM_SEGMENTS,
            "fade_duration_seconds": FADE_DURATION,
            "total_video_length_seconds": TOTAL_VIDEO_LENGTH,
            "video_source": VIDEO_SOURCE,
            "audio_source": AUDIO_SOURCE,
            "video_duration_seconds": VIDEO_DURATION
        },
        "filters": {
            "leica_filter": create_leica_filter_command(),
            "transition_effect": "white fade",
            "output_format": "MP4, H.264, AAC, YUV420P"
        },
        "llm_comparison_prompt": create_llm_comparison_prompt(),
        "success_criteria": [
            "Video exactly {:.1f} seconds long".format(TOTAL_VIDEO_LENGTH),
            "6 distinct video segments visible",
            "5 white fade transitions between segments",
            "Leica-style color grading applied",
            "Synchronized with Subnautic audio",
            "Playable in standard video players"
        ]
    }

async def main():
    """Main function to create music video and prepare LLM comparison test"""
    ensure_output_dir()
    
    print("🎵 120 BPM Music Video Creation & LLM Comparison Test")
    print("=" * 60)
    
    # Generate random segments
    print(f"🎲 Generating {NUM_SEGMENTS} random segments from {VIDEO_DURATION:.1f}s video...")
    segments = generate_random_segments(VIDEO_DURATION, NUM_SEGMENTS, SEGMENT_DURATION)
    
    print("📋 Selected segments:")
    for segment in segments:
        print(f"  Segment {segment['segment_id']}: {segment['start_time']:.2f}s - {segment['end_time']:.2f}s")
    
    # Create music video with Python FFMPEG MCP
    print(f"\n🎬 Creating music video (total length: {TOTAL_VIDEO_LENGTH:.1f}s)...")
    result = await create_music_video_python_mcp(segments)
    
    # Document parameters for LLM testing
    test_doc = document_test_parameters()
    test_doc["execution_result"] = result
    test_doc["segments_used"] = segments
    
    # Save documentation
    doc_file = Path(OUTPUT_DIR) / "llm_comparison_test_documentation.json"
    with open(doc_file, 'w') as f:
        json.dump(test_doc, f, indent=2)
    
    # Results summary
    print("\n📊 RESULTS SUMMARY:")
    print("=" * 60)
    
    if result.get('success'):
        print("✅ Music video created successfully!")
        print(f"📁 Output file: {result['output_file']}")
        print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
        
        # Verify output file
        output_path = Path(result['output_file'])
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"📊 File size: {file_size:,} bytes")
            
            # Get actual duration
            try:
                duration_result = subprocess.run([
                    'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                    '-of', 'csv=p=0', str(output_path)
                ], capture_output=True, text=True)
                
                if duration_result.returncode == 0:
                    actual_duration = float(duration_result.stdout.strip())
                    print(f"🕐 Actual duration: {actual_duration:.2f}s (target: {TOTAL_VIDEO_LENGTH:.1f}s)")
                    
                    duration_diff = abs(actual_duration - TOTAL_VIDEO_LENGTH)
                    if duration_diff < 1.0:
                        print("✅ Duration within acceptable range")
                    else:
                        print(f"⚠️ Duration difference: {duration_diff:.2f}s")
                        
            except Exception as e:
                print(f"⚠️ Could not verify duration: {e}")
        
    else:
        print("❌ Music video creation failed!")
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n📄 LLM comparison documentation: {doc_file}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    
    # Open output directory
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print("📂 Opened output directory")
    except Exception as e:
        print(f"⚠️ Could not open directory: {e}")
    
    # Analysis and recommendations
    print("\n🔍 ANALYSIS & LLM OPTIMIZATION RECOMMENDATIONS:")
    print("=" * 60)
    
    if result.get('success'):
        print("✅ Python FFMPEG MCP: Working correctly")
        
        if 'ffmpeg_command' in result:
            cmd_length = len(result['ffmpeg_command'])
            print(f"📏 Generated command length: {cmd_length} characters")
            
            if cmd_length > 1000:
                print("⚠️ RECOMMENDATION: Command is complex - consider breaking into steps for Haiku/Gemini")
            
            # Analyze command complexity
            cmd = result['ffmpeg_command']
            complex_elements = [
                ('filter_complex', 'Complex video filtering'),
                ('concat=', 'Video concatenation'),
                ('color=white', 'Transition effects'), 
                ('trim=', 'Segment extraction'),
                ('colorbalance', 'Color grading')
            ]
            
            print("\n🧩 Command complexity analysis:")
            for element, description in complex_elements:
                if element in cmd:
                    print(f"  ✅ {description}: Present")
                else:
                    print(f"  ❌ {description}: Missing")
        
        print("\n💡 PROMPT OPTIMIZATION FOR HAIKU/GEMINI:")
        print("1. Break down into clear sequential steps")
        print("2. Provide exact filter syntax examples") 
        print("3. Specify output format requirements explicitly")
        print("4. Include fallback strategies for complex filters")
        print("5. Test with simpler variations first")
        
    else:
        print("❌ Issues found - analyze logs for LLM optimization")
        
        if result.get('method') == 'direct_ffmpeg':
            print("⚠️ Fell back to direct FFMPEG - MCP integration needs work")
            print("💡 Consider simpler MCP tool calls for Haiku/Gemini")
    
    print(f"\n🎯 Next steps:")
    print(f"1. Test with Haiku LLM using prompt from: {doc_file}")
    print(f"2. Test with Gemini LLM using same prompt")
    print(f"3. Compare generated FFMPEG commands")
    print(f"4. Optimize prompts based on results")
    
    return result, test_doc

if __name__ == "__main__":
    asyncio.run(main())