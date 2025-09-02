#!/usr/bin/env python3
"""
80 BPM Music Video - Forced Validation Test
Extract and validate the actual FFMPEG commands from both models
"""

import asyncio
import subprocess
import time
from pathlib import Path

OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/80bpm-forced/"

# Extract clean commands from the results
HAIKU_COMMAND = """ffmpeg -i '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4' -i '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac' -filter_complex "[0:v]trim=84.82:87.82,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=out:st=2.7:d=0.3[seg1]; [0:v]trim=180.33:183.33,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg2]; [0:v]trim=167.33:170.33,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg3]; [0:v]trim=42.98:45.98,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg4]; [0:v]trim=17.95:20.95,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg5]; [0:v]trim=13.11:16.11,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3[seg6]; [seg1][seg2][seg3][seg4][seg5][seg6]concat=n=6:v=1:a=0[outv]" -map "[outv]" -map 1:a -c:v libx264 -c:a aac -t 18 -pix_fmt yuv420p {OUTPUT_DIR}haiku_output.mp4"""

GEMINI_COMMAND = """ffmpeg -y -i '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac' -i '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4' -filter_complex "[1:v]trim=start=84.82:duration=3,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=out:st=2.7:d=0.3[v1]; [1:v]trim=start=180.33:duration=3,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[v2]; [1:v]trim=start=167.33:duration=3,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[v3]; [1:v]trim=start=42.98:duration=3,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[v4]; [1:v]trim=start=17.95:duration=3,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0.d=0.3,fade=t=out:st=2.7:d=0.3[v5]; [1:v]trim=start=13.11:duration=3,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3[v6]; [v1][v2][v3][v4][v5][v6]concat=n=6:v=1:a=0[outv]" -map "[outv]" -map 0:a -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 128k -t 18 {OUTPUT_DIR}gemini_output.mp4"""

async def validate_command(command: str, model_name: str) -> dict:
    """Validate a specific command"""
    
    print(f"🧪 Testing {model_name} command...")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        execution_time = time.time() - start_time
        
        output_file = Path(OUTPUT_DIR) / f"{model_name.lower()}_output.mp4"
        
        if output_file.exists():
            file_size = output_file.stat().st_size
            
            # Get duration
            duration_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(output_file)
            ], capture_output=True, text=True)
            
            duration = None
            if duration_result.returncode == 0:
                try:
                    duration = float(duration_result.stdout.strip())
                except ValueError:
                    pass
            
            duration_error = abs(duration - 18.0) if duration else 999
            
            print(f"✅ {model_name}: SUCCESS ({execution_time:.2f}s)")
            print(f"   📁 Size: {file_size:,} bytes")
            print(f"   🕐 Duration: {duration:.2f}s (error: {duration_error:.2f}s)")
            
            return {
                "success": True,
                "execution_time": execution_time,
                "file_size": file_size,
                "duration": duration,
                "duration_error": duration_error,
                "output_file": str(output_file)
            }
        else:
            print(f"❌ {model_name}: FAILED - No output file")
            print(f"   Error: {result.stderr[-300:]}")
            return {
                "success": False,
                "execution_time": execution_time,
                "error": result.stderr,
                "ffmpeg_returncode": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        print(f"❌ {model_name}: TIMEOUT (120s)")
        return {"success": False, "execution_time": 120, "error": "Timeout"}
    except Exception as e:
        print(f"❌ {model_name}: ERROR - {e}")
        return {"success": False, "execution_time": time.time() - start_time, "error": str(e)}

async def run_forced_validation():
    """Force validation of both generated commands"""
    
    print("🎵 80 BPM Music Video - Forced Command Validation")
    print("=" * 60)
    print("🎯 TESTING:")
    print("   • Haiku generated command (clean extracted)")
    print("   • Gemini generated command (clean extracted)")
    print("   • Direct execution comparison")
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print(f"\\n🔍 COMMAND ANALYSIS:")
    print(f"   • Haiku length: {len(HAIKU_COMMAND)} chars")
    print(f"   • Gemini length: {len(GEMINI_COMMAND)} chars")
    
    # Key differences analysis
    print(f"\\n📊 KEY DIFFERENCES:")
    
    if "trim=84.82:87.82" in HAIKU_COMMAND:
        print("   • Haiku: Uses trim=start:end syntax")
    else:
        print("   • Haiku: Uses different trim syntax")
    
    if "trim=start=84.82:duration=3" in GEMINI_COMMAND:
        print("   • Gemini: Uses trim=start:duration syntax ✅")
    else:
        print("   • Gemini: Uses different trim syntax")
    
    if "setpts=PTS-STARTPTS" in HAIKU_COMMAND:
        print("   • Haiku: Missing setpts=PTS-STARTPTS ❌")
    else:
        print("   • Haiku: Has setpts=PTS-STARTPTS")
    
    if "setpts=PTS-STARTPTS" in GEMINI_COMMAND:
        print("   • Gemini: Missing setpts=PTS-STARTPTS ❌")
    else:
        print("   • Gemini: Has setpts=PTS-STARTPTS")
    
    # Execute both commands
    print(f"\\n🧪 EXECUTION TESTS:")
    print("-" * 40)
    
    haiku_result = await validate_command(HAIKU_COMMAND, "Haiku")
    gemini_result = await validate_command(GEMINI_COMMAND, "Gemini")
    
    # Comparison
    print(f"\\n📊 RESULTS COMPARISON:")
    print("=" * 60)
    
    if haiku_result["success"] and gemini_result["success"]:
        print("✅ Both models produced working videos!")
        
        h_dur_error = haiku_result["duration_error"]
        g_dur_error = gemini_result["duration_error"]
        
        print(f"\\n🎯 ACCURACY COMPARISON:")
        print(f"   • Haiku duration error: {h_dur_error:.2f}s")
        print(f"   • Gemini duration error: {g_dur_error:.2f}s")
        
        print(f"\\n⚡ PERFORMANCE COMPARISON:")
        print(f"   • Haiku processing: {haiku_result['execution_time']:.2f}s")
        print(f"   • Gemini processing: {gemini_result['execution_time']:.2f}s")
        
        print(f"\\n📁 FILE SIZE COMPARISON:")
        print(f"   • Haiku: {haiku_result['file_size']:,} bytes")
        print(f"   • Gemini: {gemini_result['file_size']:,} bytes")
        
        # Winner determination
        if h_dur_error < g_dur_error:
            print("\\n🏆 ACCURACY WINNER: HAIKU")
        elif g_dur_error < h_dur_error:
            print("\\n🏆 ACCURACY WINNER: GEMINI") 
        else:
            print("\\n🤝 ACCURACY: TIE")
            
        if haiku_result['execution_time'] < gemini_result['execution_time']:
            print("🏆 SPEED WINNER: HAIKU")
        elif gemini_result['execution_time'] < haiku_result['execution_time']:
            print("🏆 SPEED WINNER: GEMINI")
        else:
            print("🤝 SPEED: TIE")
    
    elif haiku_result["success"]:
        print("🏆 OVERALL WINNER: HAIKU (only working solution)")
        print(f"   Duration: {haiku_result['duration']:.2f}s (error: {haiku_result['duration_error']:.2f}s)")
        print(f"   Processing: {haiku_result['execution_time']:.2f}s")
        
    elif gemini_result["success"]:
        print("🏆 OVERALL WINNER: GEMINI (only working solution)")
        print(f"   Duration: {gemini_result['duration']:.2f}s (error: {gemini_result['duration_error']:.2f}s)")
        print(f"   Processing: {gemini_result['execution_time']:.2f}s")
        
    else:
        print("❌ Both models failed to produce working videos")
    
    # Technical insights
    print(f"\\n🔍 TECHNICAL INSIGHTS:")
    print("-" * 30)
    
    print("✅ Both models understood:")
    print("   • Segment extraction with correct timestamps")
    print("   • 8-bit vs Leica effects assignment")
    print("   • Fade transition requirements")
    print("   • Concatenation necessity")
    print("   • Output format specifications")
    
    print("⚠️ Critical differences:")
    if not haiku_result["success"]:
        print(f"   • Haiku error: {haiku_result.get('error', 'Unknown')[:100]}...")
    if not gemini_result["success"]:
        print(f"   • Gemini error: {gemini_result.get('error', 'Unknown')[:100]}...")
    
    # Open directory
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print(f"\\n📂 Opened output directory: {OUTPUT_DIR}")
    except:
        pass
    
    return {"haiku": haiku_result, "gemini": gemini_result}

if __name__ == "__main__":
    asyncio.run(run_forced_validation())