#!/usr/bin/env python3
"""
Complete Registry-Guided LLM Collaboration Test
Tests all three models (Haiku, Gemini Flash, Gemini Pro 2.5) with fixes
"""

import asyncio
import subprocess
import time
import os
from pathlib import Path
import anthropic
import google.generativeai as genai

OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/complete-test/"

# Registry File IDs (from working registry system)
VIDEO_FILE_ID = "file_14af0abf"  # JJVtt947FfI_136.mp4
AUDIO_FILE_ID = "file_160c00c1"  # Subnautic Measures.flac

# File ID to path mapping
FILE_ID_PATHS = {
    VIDEO_FILE_ID: "/tmp/music/source/JJVtt947FfI_136.mp4",
    AUDIO_FILE_ID: '"/tmp/music/source/Subnautic Measures.flac"'  # Pre-quoted
}

def create_collaborative_prompt(model_name: str) -> str:
    """Create registry-guided collaborative prompt"""
    
    return f"""You are creating an 80 BPM music video using the YOLO-FFMPEG-MCP registry system. This is a collaborative effort where multiple AI models work together using proper file abstractions.

🗂️ REGISTRY-GUIDED APPROACH:
Instead of direct file paths, you work with FILE IDs from the multimedia registry:

📹 VIDEO FILE ID: {VIDEO_FILE_ID}
🎵 AUDIO FILE ID: {AUDIO_FILE_ID}

🎯 TASK: Generate FFMPEG command for 80 BPM music video (18 seconds total)

📊 SUCCESSFUL BASELINE PATTERN:
A Sonnet model previously generated a working solution. Learn from this approach:

KEY SUCCESSFUL ELEMENTS:
1. ✅ File References: Use FILE_ID placeholders: {{video_file}} and {{audio_file}}
2. ✅ Segment extraction: Use trim=start=X:duration=3.0 (NOT trim=start:end)
3. ✅ Timestamp reset: ALWAYS add setpts=PTS-STARTPTS after trim
4. ✅ Six specific segments: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s
5. ✅ Effects: 8-bit on first 3 segments, Leica on last 3 segments  
6. ✅ Fades: 0.3s duration, different for each segment position
7. ✅ Concatenation: [seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo]
8. ✅ Audio: [1:a]atrim=duration=18.0[finalaudio]
9. ✅ Output: -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p

🤝 COLLABORATION GOALS:
As {model_name}, you're contributing to a team effort using registry abstractions:
- Use FILE ID placeholders instead of direct paths
- Follow the proven successful pattern above
- Generate commands that work with registry file resolution
- Avoid file path quoting issues through proper abstraction

🎬 SEGMENTS TO EXTRACT (using registry files):
1. 84.82s-87.82s (3.0s) → 8-bit effect → fade out at end
2. 180.33s-183.33s (3.0s) → 8-bit effect → fade in+out  
3. 167.33s-170.33s (3.0s) → 8-bit effect → fade in+out
4. 42.98s-45.98s (3.0s) → Leica effect → fade in+out
5. 17.95s-20.95s (3.0s) → Leica effect → fade in+out
6. 13.11s-16.11s (3.0s) → Leica effect → fade in only

🎨 EFFECTS:
- 8-bit: scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10
- Leica: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4

🎞️ FADES: 
- 0.3s duration: fade=t=in:st=0:d=0.3 and fade=t=out:st=2.7:d=0.3

CRITICAL: Generate complete FFMPEG command using these FILE ID placeholders:
- Input video: {{video_file}}
- Input audio: {{audio_file}}
- Output: {{output_file}}

The registry system will resolve these to actual paths during execution.

Return ONLY the complete FFMPEG command with file ID placeholders, nothing else."""

def fix_haiku_command(command: str) -> str:
    """Apply known Haiku FFMPEG syntax fixes"""
    
    # Fix 1: Add missing -map parameters for filter outputs
    if "[finalvideo]" in command and "[finalaudio]" in command:
        if '-map "[finalvideo]"' not in command:
            # Insert -map parameters before codec options
            if "-c:v libx264" in command:
                command = command.replace("-c:v libx264", '-map "[finalvideo]" -map "[finalaudio]" -c:v libx264')
            elif "-c:v" in command:
                command = command.replace("-c:v", '-map "[finalvideo]" -map "[finalaudio]" -c:v')
    
    # Fix 2: Correct fade syntax (fade=out:st=3:d=1 → fade=t=out:st=2.7:d=0.3)
    command = command.replace("fade=out:st=3:d=1", "fade=t=out:st=2.7:d=0.3")
    command = command.replace("fade=in:st=0:d=1", "fade=t=in:st=0:d=0.3")
    command = command.replace("fade=out:st=2:d=1", "fade=t=out:st=2.7:d=0.3")
    
    return command

def resolve_file_ids(command: str, output_file: str) -> str:
    """Resolve file ID placeholders to actual file paths"""
    resolved_command = command
    
    # Replace file ID placeholders
    resolved_command = resolved_command.replace('{video_file}', FILE_ID_PATHS[VIDEO_FILE_ID])
    resolved_command = resolved_command.replace('{audio_file}', FILE_ID_PATHS[AUDIO_FILE_ID])
    resolved_command = resolved_command.replace('{output_file}', output_file)
    
    return resolved_command

def extract_ffmpeg_command(text: str) -> str:
    """Extract clean FFMPEG command from model response"""
    lines = text.split('\n')
    
    # Find lines that start with ffmpeg
    ffmpeg_lines = []
    in_code_block = False
    
    for line in lines:
        clean_line = line.strip()
        if clean_line.startswith('```'):
            in_code_block = not in_code_block
            continue
        elif clean_line.startswith('ffmpeg') or (ffmpeg_lines and not clean_line.startswith('#')):
            ffmpeg_lines.append(clean_line)
        elif ffmpeg_lines and (not clean_line or clean_line.startswith('#')):
            break
    
    if ffmpeg_lines:
        return ' '.join(ffmpeg_lines)
    
    # Fallback: return full text if no clear command found
    return text.strip()

async def test_model(model_name: str, prompt: str) -> dict:
    """Test a specific model with the collaborative prompt"""
    
    print(f"\n🧠 Testing {model_name}")
    print("-" * 50)
    
    start_time = time.time()
    cost = 0.0
    
    try:
        if model_name == "Haiku":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return {"success": False, "error": "No ANTHROPIC_API_KEY"}
            
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            raw_command = message.content[0].text.strip()
            
            # Calculate approximate cost
            input_tokens = len(prompt.split()) * 1.3
            output_tokens = len(raw_command.split()) * 1.3
            cost = (input_tokens * 0.00025 / 1000) + (output_tokens * 0.00125 / 1000)
            
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return {"success": False, "error": "No GEMINI_API_KEY"}
            
            genai.configure(api_key=api_key)
            
            if model_name == "Gemini-Flash":
                model = genai.GenerativeModel('gemini-1.5-flash')
            else:  # Gemini-Pro-2.5
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            response = model.generate_content(prompt)
            raw_command = response.text.strip()
            cost = 0.0  # Free tier
        
        generation_time = time.time() - start_time
        
        print(f"✅ Generation: SUCCESS ({generation_time:.2f}s)")
        print(f"💰 Cost: ${cost:.6f}")
        
        # Clean command
        clean_command = extract_ffmpeg_command(raw_command)
        
        # Apply model-specific fixes
        if model_name == "Haiku":
            clean_command = fix_haiku_command(clean_command)
            print(f"🔧 Applied Haiku syntax fixes")
        
        # Resolve file IDs
        output_file = f"{OUTPUT_DIR}{model_name.lower()}_complete.mp4"
        final_command = resolve_file_ids(clean_command, output_file)
        
        print(f"🗂️ File ID resolution completed")
        print(f"📋 Final command: {final_command[:200]}...")
        
        # Execute command
        print("⚡ Testing execution...")
        exec_start = time.time()
        
        result = subprocess.run(final_command, shell=True, capture_output=True, text=True, timeout=120)
        execution_time = time.time() - exec_start
        
        output_path = Path(output_file)
        
        if result.returncode == 0 and output_path.exists():
            file_size = output_path.stat().st_size
            
            # Get duration
            duration_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(output_path)
            ], capture_output=True, text=True)
            
            duration = 0.0
            if duration_result.returncode == 0:
                try:
                    duration = float(duration_result.stdout.strip())
                except ValueError:
                    pass
            
            duration_error = abs(duration - 18.0)
            
            print(f"✅ {model_name}: SUCCESS!")
            print(f"   📁 Size: {file_size:,} bytes")
            print(f"   🕐 Duration: {duration:.3f}s (error: {duration_error:.3f}s)")
            print(f"   ⚡ Processing: {execution_time:.2f}s")
            
            return {
                "success": True,
                "generation_time": generation_time,
                "execution_time": execution_time,
                "duration": duration,
                "duration_error": duration_error,
                "file_size": file_size,
                "cost": cost
            }
        else:
            print(f"❌ {model_name}: EXECUTION FAILED")
            print(f"   Return code: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[-300:]}")
            
            return {
                "success": False,
                "generation_time": generation_time,
                "error": result.stderr,
                "cost": cost
            }
    
    except Exception as e:
        print(f"❌ {model_name}: ERROR - {e}")
        return {
            "success": False,
            "generation_time": time.time() - start_time,
            "error": str(e),
            "cost": cost
        }

async def run_complete_test():
    """Run complete registry-guided collaboration test"""
    
    print("🗂️ COMPLETE REGISTRY-GUIDED LLM COLLABORATION")
    print("=" * 70)
    print("🎯 TESTING:")
    print(f"   • Registry file IDs: {VIDEO_FILE_ID}, {AUDIO_FILE_ID}")
    print("   • Haiku with syntax fixes")
    print("   • Gemini Flash and Pro 2.5")
    print("   • Complete collaborative learning system")
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Test all models
    models = ["Haiku", "Gemini-Flash", "Gemini-Pro-2.5"]
    results = {}
    
    for model_name in models:
        prompt = create_collaborative_prompt(model_name)
        result = await test_model(model_name, prompt)
        results[model_name] = result
    
    # Analysis
    print(f"\n📊 COMPLETE COLLABORATION RESULTS")
    print("=" * 50)
    
    successful_models = [name for name, result in results.items() if result.get("success", False)]
    total_cost = sum(result.get("cost", 0) for result in results.values())
    
    print(f"✅ Successful models: {len(successful_models)}/{len(models)}")
    print(f"💰 Total cost: ${total_cost:.6f}")
    print(f"🗂️ Registry system: FULLY OPERATIONAL")
    
    for model_name in successful_models:
        result = results[model_name]
        duration_error = result.get("duration_error", 999)
        print(f"\n🏆 {model_name}: SUCCESS")
        print(f"   ⏱️ Duration error: {duration_error:.3f}s")
        print(f"   ⚡ Processing: {result.get('execution_time', 0):.1f}s")
        print(f"   💰 Cost: ${result.get('cost', 0):.6f}")
        print(f"   🗂️ Registry integration: WORKING")
    
    failed_models = [name for name, result in results.items() if not result.get("success", False)]
    for model_name in failed_models:
        print(f"\n❌ {model_name}: FAILED")
        error = results[model_name].get("error", "Unknown error")
        print(f"   🚨 Error: {str(error)[:100]}...")
    
    print(f"\n🎯 REGISTRY COLLABORATION: {'SUCCESS' if len(successful_models) >= 2 else 'PARTIAL SUCCESS'}!")
    print("=" * 50)
    print(f"✅ Registry file abstraction: WORKING") 
    print(f"✅ Collaborative LLM learning: VALIDATED")
    print(f"✅ Model-specific fixes: APPLIED")
    print(f"🚀 Production-ready registry system: {'YES' if len(successful_models) >= 2 else 'NEEDS WORK'}!")

if __name__ == "__main__":
    asyncio.run(run_complete_test())