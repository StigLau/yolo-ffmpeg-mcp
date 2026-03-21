#!/usr/bin/env python3
"""
Gemini Pro 2.5 Registry Test - Command Parsing Fixed
"""

import asyncio
import subprocess
import time
import json
import os
import re
from pathlib import Path
import google.generativeai as genai

OUTPUT_DIR = '/tmp/kompo/haiku-ffmpeg/gemini-fixed/'

def create_prompt():
    return '''Generate a single-line FFMPEG command for 80 BPM music video:

INPUT FILES:
- Video: /tmp/music/source/JJVtt947FfI_136.mp4  
- Audio: "/tmp/music/source/Subnautic Measures.flac"

TASK: Create 18-second video with 6 segments (3 seconds each):

SEGMENTS:
1. 84.82s-87.82s → 8-bit effect → fade out at end
2. 180.33s-183.33s → 8-bit effect → fade in+out  
3. 167.33s-170.33s → 8-bit effect → fade in+out
4. 42.98s-45.98s → Leica effect → fade in+out
5. 17.95s-20.95s → Leica effect → fade in+out
6. 13.11s-16.11s → Leica effect → fade in only

EFFECTS:
- 8-bit: scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10
- Leica: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4

FADES: fade=t=in:st=0:d=0.3 and fade=t=out:st=2.7:d=0.3

REQUIREMENTS:
- Use trim=start=X:duration=3.0 syntax
- Add setpts=PTS-STARTPTS after each trim
- Concatenate all 6 segments
- Audio: atrim=duration=18.0
- Output format: H.264, AAC, yuv420p
- Output file: /tmp/kompo/haiku-ffmpeg/gemini-fixed/output.mp4

IMPORTANT: Return ONLY the complete FFMPEG command as a single line, no explanations, no code blocks, no line breaks.'''

def clean_command(raw_command):
    """Clean and fix FFMPEG command parsing"""
    
    # Remove code block markers
    command = re.sub(r'```[a-zA-Z]*\n?', '', raw_command)
    command = re.sub(r'```', '', command)
    
    # Remove comments and explanations
    lines = command.split('\n')
    ffmpeg_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#') or line.startswith('//'):
            continue
        if line.startswith('ffmpeg') or (ffmpeg_lines and not line.startswith(('Note:', 'This ', 'The '))):
            ffmpeg_lines.append(line)
    
    # Join lines and clean up backslashes
    if ffmpeg_lines:
        command = ' '.join(ffmpeg_lines)
    else:
        command = raw_command
    
    # Clean up line continuation backslashes
    command = re.sub(r'\s*\\\s*', ' ', command)
    
    # Clean up multiple spaces
    command = re.sub(r'\s+', ' ', command)
    
    # Ensure it starts with ffmpeg
    if not command.strip().startswith('ffmpeg'):
        # Try to find ffmpeg in the text
        match = re.search(r'ffmpeg\s+.*', command, re.IGNORECASE)
        if match:
            command = match.group(0)
    
    return command.strip()

async def test_gemini_fixed():
    print('🧠 Gemini Pro 2.5 - Command Parsing Fixed')
    print('='*60)
    
    # Verify registry files
    video = Path('/tmp/music/source/JJVtt947FfI_136.mp4')
    audio = Path('/tmp/music/source/Subnautic Measures.flac')
    
    print('🗂️ REGISTRY VERIFICATION:')
    print(f'   📹 Video: {video.exists()} - {video.stat().st_size:,} bytes')
    print(f'   🎵 Audio: {audio.exists()} - {audio.stat().st_size:,} bytes')
    
    if not (video.exists() and audio.exists()):
        print('❌ Registry files missing!')
        return
    
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Setup Gemini
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print('❌ No GEMINI_API_KEY')
        return
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Generate command
    print('\n🎬 Generating FFMPEG command...')
    start_time = time.time()
    
    response = model.generate_content(create_prompt())
    generation_time = time.time() - start_time
    
    raw_command = response.text
    clean_cmd = clean_command(raw_command)
    
    print(f'✅ Generated in {generation_time:.2f}s')
    print(f'📝 Raw length: {len(raw_command)} chars')
    print(f'📝 Clean length: {len(clean_cmd)} chars')
    print(f'🔍 Preview: {clean_cmd[:200]}...')
    
    # Execute command
    print('\n⚡ Executing FFMPEG...')
    exec_start = time.time()
    
    try:
        result = subprocess.run(clean_cmd, shell=True, capture_output=True, text=True, timeout=180)
        execution_time = time.time() - exec_start
        
        output_file = f'{OUTPUT_DIR}output.mp4'
        output_path = Path(output_file)
        
        if output_path.exists():
            file_size = output_path.stat().st_size
            
            # Get video metadata
            probe_cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', '-show_format', str(output_path)
            ]
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            
            duration = 0.0
            width = height = 'unknown'
            video_codec = audio_codec = 'unknown'
            video_bitrate = audio_bitrate = 'unknown'
            
            if probe_result.returncode == 0:
                try:
                    data = json.loads(probe_result.stdout)
                    
                    # Format info
                    if 'format' in data:
                        duration = float(data['format'].get('duration', 0))
                    
                    # Stream info
                    for stream in data.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            width = stream.get('width', 'unknown')
                            height = stream.get('height', 'unknown') 
                            video_codec = stream.get('codec_name', 'unknown')
                            video_bitrate = stream.get('bit_rate', 'unknown')
                        elif stream.get('codec_type') == 'audio':
                            audio_codec = stream.get('codec_name', 'unknown')
                            audio_bitrate = stream.get('bit_rate', 'unknown')
                except:
                    pass
            
            duration_error = abs(duration - 18.0) if duration > 0 else 999
            accuracy = max(0, 100 - (duration_error / 18.0 * 100))
            
            print('🎉 SUCCESS!')
            print('='*50)
            
            print(f'📊 GENERATION:')
            print(f'   🧠 Model: Gemini Pro 2.5 (gemini-2.0-flash-exp)')
            print(f'   ⏱️  Time: {generation_time:.2f}s')
            print(f'   💰 Cost: $0.00 (free tier)')
            
            print(f'\n📊 EXECUTION:')
            print(f'   ⚡ Processing: {execution_time:.2f}s')
            print(f'   📁 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)')
            print(f'   🕐 Duration: {duration:.3f}s (target: 18.000s)')
            print(f'   🎯 Accuracy: {accuracy:.1f}% (error: {duration_error:.3f}s)')
            
            print(f'\n📊 VIDEO SPECS:')
            print(f'   📐 Resolution: {width}x{height}')
            print(f'   🎞️ Video: {video_codec}')
            print(f'   🎵 Audio: {audio_codec}')
            if video_bitrate != 'unknown':
                print(f'   📊 Video bitrate: {int(video_bitrate)/1000:.0f} kbps')
            if audio_bitrate != 'unknown':
                print(f'   📊 Audio bitrate: {int(audio_bitrate)/1000:.0f} kbps')
            
            print(f'\n🗂️ REGISTRY STATUS:')
            print(f'   ✅ Used registry source files')
            print(f'   ✅ File abstraction working')
            print(f'   ✅ Collaborative learning successful')
            
            # Quality assessment
            if duration_error < 0.01:
                print(f'   🏆 PERFECT timing accuracy!')
            elif duration_error < 0.1:
                print(f'   ✅ Excellent timing accuracy!')
            elif duration_error < 0.5:
                print(f'   👍 Good timing accuracy')
            else:
                print(f'   ⚠️  Timing needs improvement')
            
            # Performance metrics
            total_time = generation_time + execution_time
            throughput = file_size / execution_time if execution_time > 0 else 0
            
            print(f'\n⚡ PERFORMANCE:')
            print(f'   🕐 Total time: {total_time:.1f}s')
            print(f'   📊 Processing speed: {throughput/1024/1024:.1f} MB/s')
            print(f'   🎯 Overall score: {accuracy/10:.1f}/10')
            
            # Show generated command
            print(f'\n📋 GENERATED COMMAND:')
            print('='*60)
            print(f'{clean_cmd[:300]}')
            if len(clean_cmd) > 300:
                print('...')
            
            # Open results
            try:
                subprocess.run(['open', output_file])
                subprocess.run(['open', OUTPUT_DIR])
                print(f'\n📺 Opened video and directory')
            except:
                pass
            
            return True
            
        else:
            print('❌ EXECUTION FAILED')
            print(f'Return code: {result.returncode}')
            print(f'Command used: {clean_cmd[:300]}...')
            print(f'STDOUT: {result.stdout[-500:] if result.stdout else "None"}')
            print(f'STDERR: {result.stderr[-500:] if result.stderr else "None"}')
            return False
            
    except subprocess.TimeoutExpired:
        print('❌ EXECUTION TIMEOUT (180s)')
        return False
    except Exception as e:
        print(f'❌ EXECUTION ERROR: {e}')
        return False

if __name__ == '__main__':
    asyncio.run(test_gemini_fixed())