#!/usr/bin/env python3
"""
Debug Haiku FFMPEG Command Generation
Focus on the specific command syntax issue
"""

import asyncio
import subprocess
import time
import os
from pathlib import Path
import anthropic

# Test files (properly quoted)
VIDEO_FILE = "/tmp/music/source/JJVtt947FfI_136.mp4"  
AUDIO_FILE = '"/tmp/music/source/Subnautic Measures.flac"'  # Pre-quoted
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/debug/"

def create_haiku_prompt():
    """Create focused prompt to debug Haiku command generation"""
    
    return f"""You are creating an 80 BPM music video using FFMPEG. Generate a command that creates 18 seconds of video from 6 segments.

🎯 TASK: Generate FFMPEG command for 18-second music video

FILES:
- Video: {VIDEO_FILE}
- Audio: {AUDIO_FILE}
- Output: {OUTPUT_DIR}haiku_debug.mp4

SEGMENTS (3 seconds each):
1. 84.82s-87.82s → 8-bit effect → fade out at end
2. 180.33s-183.33s → 8-bit effect → fade in+out  
3. 167.33s-170.33s → 8-bit effect → fade in+out
4. 42.98s-45.98s → Leica effect → fade in+out
5. 17.95s-20.95s → Leica effect → fade in+out
6. 13.11s-16.11s → Leica effect → fade in only

EFFECTS:
- 8-bit: scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10
- Leica: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4

CRITICAL REQUIREMENTS:
- Use trim=start=X:duration=3.0 syntax
- Add setpts=PTS-STARTPTS after each trim  
- Use [0:v] for video input, [1:a] for audio input
- Concatenate: [seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo]
- Audio: [1:a]atrim=duration=18.0[finalaudio]
- Output: -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p

Return ONLY the complete FFMPEG command, nothing else."""

async def test_haiku_debug():
    print("🐣 HAIKU FFMPEG DEBUG TEST")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found")
        return
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Initialize Haiku client
    client = anthropic.Anthropic(api_key=api_key)
    
    print("🧠 Generating Haiku command...")
    start_time = time.time()
    
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2000,
        messages=[{"role": "user", "content": create_haiku_prompt()}]
    )
    
    generation_time = time.time() - start_time
    raw_command = message.content[0].text.strip()
    
    print(f"✅ Generated in {generation_time:.2f}s")
    print(f"📝 Command length: {len(raw_command)} chars")
    print()
    print("🔍 RAW COMMAND:")
    print("-" * 80)
    print(raw_command)
    print("-" * 80)
    
    # Clean command (remove any markdown formatting)
    clean_command = raw_command
    if clean_command.startswith('```'):
        lines = clean_command.split('\n')
        clean_command = '\n'.join(lines[1:-1]) if len(lines) > 2 else clean_command
    
    clean_command = clean_command.strip()
    
    print()
    print("🧼 CLEANED COMMAND:")
    print("-" * 80)
    print(clean_command)
    print("-" * 80)
    
    # Test execution
    print()
    print("⚡ Testing command execution...")
    exec_start = time.time()
    
    try:
        result = subprocess.run(clean_command, shell=True, capture_output=True, text=True, timeout=120)
        execution_time = time.time() - exec_start
        
        output_file = f"{OUTPUT_DIR}haiku_debug.mp4"
        output_path = Path(output_file)
        
        if result.returncode == 0 and output_path.exists():
            file_size = output_path.stat().st_size
            
            # Get duration
            duration_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(output_path)]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            
            duration = 0.0
            if duration_result.returncode == 0:
                try:
                    duration = float(duration_result.stdout.strip())
                except ValueError:
                    pass
            
            duration_error = abs(duration - 18.0)
            
            print(f"✅ SUCCESS!")
            print(f"   📁 File size: {file_size:,} bytes")
            print(f"   🕐 Duration: {duration:.3f}s (error: {duration_error:.3f}s)")
            print(f"   ⚡ Processing: {execution_time:.2f}s")
            
            return True
            
        else:
            print(f"❌ EXECUTION FAILED (return code: {result.returncode})")
            print()
            print("📋 COMMAND USED:")
            print(clean_command[:300] + "..." if len(clean_command) > 300 else clean_command)
            print()
            print("🚨 STDERR:")
            print("-" * 50)
            print(result.stderr[-1000:] if result.stderr else "No error output")
            print("-" * 50)
            print()
            print("📤 STDOUT:")
            print("-" * 50)
            print(result.stdout[-500:] if result.stdout else "No output")
            print("-" * 50)
            
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT (120s)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

async def analyze_haiku_problem():
    """Analyze what went wrong with Haiku file selection"""
    
    print("""
🔍 HAIKU PROBLEM ANALYSIS
========================

❌ WHAT WENT WRONG:
- User requested: "Create montage using 3 different video clips"
- Expected files: JJVtt947FfI_136.mp4, PXL_20250306_132546255.mp4, _wZ5Hof5tXY_136.mp4
- Haiku actually used: test_video.mp4 (WRONG!)
- Result: 31.5s, 320x240, no audio instead of 21.57s, 1280x720, with audio

🧠 PROMPT PROBLEMS:
1. File selection logic is unclear
2. No explicit instruction to avoid test files
3. No validation of file usage
4. No size/quality requirements specified

💡 PROPOSED FIXES:
1. Explicit file filtering: "Do NOT use any files with 'test' in the name"
2. File validation: "Verify file sizes are > 1MB before using"
3. Quality requirements: "Target output should be HD resolution (1280x720 or higher)"
4. Explicit file mapping: "Use exactly these files: [list]"

🎯 IMPROVED PROMPT STRUCTURE:
- Clear file inclusion/exclusion rules
- Quality validation steps
- Explicit file-to-role mapping
- Success criteria definition
""")

if __name__ == "__main__":
    asyncio.run(test_haiku_debug())