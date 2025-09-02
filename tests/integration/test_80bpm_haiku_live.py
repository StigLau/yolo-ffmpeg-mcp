#!/usr/bin/env python3
"""
80 BPM Music Video - Live Haiku & Gemini API Test
Direct API testing with real FFMPEG command generation and validation
"""

import asyncio
import json
import subprocess
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

# API clients
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Test parameters
SEGMENTS = [
    {"segment_id": 1, "start_time": 84.82, "duration": 3.0},
    {"segment_id": 2, "start_time": 180.33, "duration": 3.0},
    {"segment_id": 3, "start_time": 167.33, "duration": 3.0},
    {"segment_id": 4, "start_time": 42.98, "duration": 3.0},
    {"segment_id": 5, "start_time": 17.95, "duration": 3.0},
    {"segment_id": 6, "start_time": 13.11, "duration": 3.0}
]

VIDEO_SOURCE = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4"
AUDIO_SOURCE = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac"
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/80bpm-live/"

def create_optimized_prompt() -> str:
    """Optimized prompt for FFMPEG command generation"""
    return f"""Generate a complete FFMPEG command for this 80 BPM music video task:

INPUTS:
- Video: {VIDEO_SOURCE}
- Audio: {AUDIO_SOURCE}

TASK: Create 18-second music video with 6 segments (3 seconds each)

SEGMENTS TO EXTRACT:
1. 84.82s-87.82s (3.0s) → 8-bit effect → fade out at end
2. 180.33s-183.33s (3.0s) → 8-bit effect → fade in+out  
3. 167.33s-170.33s (3.0s) → 8-bit effect → fade in+out
4. 42.98s-45.98s (3.0s) → Leica effect → fade in+out
5. 17.95s-20.95s (3.0s) → Leica effect → fade in+out
6. 13.11s-16.11s (3.0s) → Leica effect → fade in only

EFFECTS:
- 8-bit: scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10
- Leica: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4

FADES: 
- 0.3s duration: fade=t=in:st=0:d=0.3 and fade=t=out:st=2.7:d=0.3

OUTPUT:
- File: {OUTPUT_DIR}output.mp4
- Format: H.264, AAC, yuv420p
- Duration: 18.0s exactly

Return only the complete FFMPEG command."""

async def test_haiku_generation(prompt: str) -> Dict[str, Any]:
    """Test Haiku FFMPEG command generation"""
    
    if not anthropic:
        return {"success": False, "error": "Anthropic client not available"}
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return {"success": False, "error": "No ANTHROPIC_API_KEY found"}
    
    print("🧠 Testing Haiku FFMPEG generation...")
    
    client = anthropic.Anthropic(api_key=api_key)
    start_time = time.time()
    
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
        )
        
        processing_time = time.time() - start_time
        generated_command = response.content[0].text.strip()
        
        # Clean up command (remove any markdown)
        if "```" in generated_command:
            parts = generated_command.split("```")
            for part in parts:
                if "ffmpeg" in part and not part.startswith("bash"):
                    generated_command = part.strip()
                    break
        
        # Calculate cost
        input_tokens = response.usage.input_tokens if hasattr(response, 'usage') else 0
        output_tokens = response.usage.output_tokens if hasattr(response, 'usage') else 0
        cost = (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000
        
        return {
            "success": True,
            "processing_time": processing_time,
            "generated_command": generated_command,
            "command_length": len(generated_command),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        }
        
    except Exception as e:
        return {
            "success": False,
            "processing_time": time.time() - start_time,
            "error": str(e)
        }

async def test_gemini_generation(prompt: str) -> Dict[str, Any]:
    """Test Gemini FFMPEG command generation"""
    
    if not genai:
        return {"success": False, "error": "Google GenerativeAI client not available"}
    
    api_key = os.getenv('GEMINI_API_KEY') 
    if not api_key:
        return {"success": False, "error": "No GEMINI_API_KEY found"}
    
    print("🤖 Testing Gemini FFMPEG generation...")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    start_time = time.time()
    
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        
        processing_time = time.time() - start_time
        generated_command = response.text.strip()
        
        # Clean up command
        if "```" in generated_command:
            parts = generated_command.split("```")
            for part in parts:
                if "ffmpeg" in part and not part.startswith("bash"):
                    generated_command = part.strip()
                    break
        
        return {
            "success": True,
            "processing_time": processing_time,
            "generated_command": generated_command,
            "command_length": len(generated_command),
            "cost": 0.0  # Gemini Flash is free tier
        }
        
    except Exception as e:
        return {
            "success": False,
            "processing_time": time.time() - start_time,
            "error": str(e)
        }

def analyze_command_completeness(command: str) -> Dict[str, Any]:
    """Quick analysis of command completeness"""
    
    checks = {
        "has_ffmpeg": command.strip().startswith("ffmpeg"),
        "has_inputs": "-i" in command and "JJVtt947FfI_136.mp4" in command,
        "has_audio": "Subnautic Measures.flac" in command or "Subnautic" in command,
        "has_segments": sum(1 for ts in ["84.82", "180.33", "167.33", "42.98", "17.95", "13.11"] if ts in command),
        "has_effects": "scale=" in command or "colorbalance=" in command,
        "has_fades": "fade=" in command,
        "has_concat": "concat=" in command,
        "has_output": "-c:v" in command or "libx264" in command
    }
    
    segment_score = checks["has_segments"] / 6  # 6 segments expected
    
    completeness_score = (
        checks["has_ffmpeg"] * 0.15 +
        checks["has_inputs"] * 0.15 +
        checks["has_audio"] * 0.10 +
        segment_score * 0.25 +
        checks["has_effects"] * 0.15 +
        checks["has_fades"] * 0.10 +
        checks["has_concat"] * 0.15 +
        checks["has_output"] * 0.10
    )
    
    return {
        "completeness_score": completeness_score,
        "checks": checks,
        "segments_found": checks["has_segments"],
        "likely_executable": checks["has_ffmpeg"] and checks["has_inputs"] and segment_score > 0.5
    }

async def validate_command_quick(command: str, test_name: str) -> Dict[str, Any]:
    """Quick validation of generated command"""
    
    # Prepare command
    clean_command = command.strip()
    if not clean_command.startswith("ffmpeg"):
        return {"success": False, "error": "Not an FFMPEG command"}
    
    # Replace output path
    test_output = Path(OUTPUT_DIR) / f"{test_name}_test.mp4"
    if "output.mp4" in clean_command:
        clean_command = clean_command.replace("output.mp4", str(test_output))
    else:
        clean_command += f" {test_output}"
    
    print(f"   🧪 Executing {test_name} command...")
    start_time = time.time()
    
    try:
        # Use shell=True to handle complex FFMPEG syntax properly
        result = subprocess.run(clean_command, shell=True, capture_output=True, text=True, timeout=120)
        execution_time = time.time() - start_time
        
        if test_output.exists():
            file_size = test_output.stat().st_size
            
            # Quick duration check
            duration_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(test_output)
            ], capture_output=True, text=True)
            
            duration = None
            if duration_result.returncode == 0:
                try:
                    duration = float(duration_result.stdout.strip())
                except ValueError:
                    pass
            
            duration_ok = abs(duration - 18.0) < 1.0 if duration else False
            
            return {
                "success": True,
                "execution_time": execution_time,
                "output_file": str(test_output),
                "file_size": file_size,
                "duration": duration,
                "duration_ok": duration_ok,
                "ffmpeg_success": result.returncode == 0
            }
        else:
            return {
                "success": False,
                "execution_time": execution_time,
                "error": f"No output. Error: {result.stderr[-200:]}",
                "ffmpeg_returncode": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "execution_time": 120, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "execution_time": time.time() - start_time, "error": str(e)}

async def run_live_llm_comparison():
    """Execute live Haiku vs Gemini comparison"""
    
    print("🎵 80 BPM Music Video - Live LLM Comparison")
    print("=" * 60)
    print("🎯 TESTING:")
    print("   • Haiku 3 (claude-3-haiku-20240307)")
    print("   • Gemini 1.5 Flash (gemini-1.5-flash)")
    print("   • Direct API calls with FFMPEG validation")
    print("   • Cost and performance comparison")
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    prompt = create_optimized_prompt()
    print(f"\\n📝 Using optimized prompt ({len(prompt)} chars)")
    
    results = {
        "timestamp": time.time(),
        "test_purpose": "Live Haiku vs Gemini FFMPEG Generation",
        "prompt": prompt,
        "tests": {}
    }
    
    # Test Haiku
    print(f"\\n🧠 HAIKU TEST")
    print("-" * 30)
    
    haiku_result = await test_haiku_generation(prompt)
    
    if haiku_result["success"]:
        print(f"✅ Generation: SUCCESS ({haiku_result['processing_time']:.2f}s)")
        print(f"📏 Command: {haiku_result['command_length']} chars")
        print(f"💰 Cost: ${haiku_result['cost']:.6f}")
        print(f"🪙 Tokens: {haiku_result['input_tokens']}→{haiku_result['output_tokens']}")
        
        # Analyze command
        analysis = analyze_command_completeness(haiku_result["generated_command"])
        print(f"🎯 Completeness: {analysis['completeness_score']:.2%}")
        print(f"📊 Segments found: {analysis['segments_found']}/6")
        
        haiku_result["analysis"] = analysis
        
        # Validate if promising
        if analysis["likely_executable"]:
            validation = await validate_command_quick(haiku_result["generated_command"], "haiku")
            haiku_result["validation"] = validation
            
            if validation["success"]:
                print(f"✅ Execution: SUCCESS ({validation['execution_time']:.2f}s)")
                print(f"📁 Output: {validation['file_size']:,} bytes")
                if validation.get("duration"):
                    print(f"🕐 Duration: {validation['duration']:.2f}s (target: 18.0s)")
            else:
                print(f"❌ Execution: FAILED")
                print(f"💥 Error: {validation['error'][:100]}...")
        else:
            print(f"⚠️ Command quality too low - skipping execution")
    else:
        print(f"❌ Generation: FAILED")
        print(f"💥 Error: {haiku_result['error']}")
    
    results["tests"]["haiku"] = haiku_result
    
    # Test Gemini
    print(f"\\n🤖 GEMINI TEST")
    print("-" * 30)
    
    gemini_result = await test_gemini_generation(prompt)
    
    if gemini_result["success"]:
        print(f"✅ Generation: SUCCESS ({gemini_result['processing_time']:.2f}s)")
        print(f"📏 Command: {gemini_result['command_length']} chars")
        print(f"💰 Cost: ${gemini_result['cost']:.6f} (free tier)")
        
        # Analyze command
        analysis = analyze_command_completeness(gemini_result["generated_command"])
        print(f"🎯 Completeness: {analysis['completeness_score']:.2%}")
        print(f"📊 Segments found: {analysis['segments_found']}/6")
        
        gemini_result["analysis"] = analysis
        
        # Validate if promising
        if analysis["likely_executable"]:
            validation = await validate_command_quick(gemini_result["generated_command"], "gemini")
            gemini_result["validation"] = validation
            
            if validation["success"]:
                print(f"✅ Execution: SUCCESS ({validation['execution_time']:.2f}s)")
                print(f"📁 Output: {validation['file_size']:,} bytes")
                if validation.get("duration"):
                    print(f"🕐 Duration: {validation['duration']:.2f}s (target: 18.0s)")
            else:
                print(f"❌ Execution: FAILED")
                print(f"💥 Error: {validation['error'][:100]}...")
        else:
            print(f"⚠️ Command quality too low - skipping execution")
    else:
        print(f"❌ Generation: FAILED")
        print(f"💥 Error: {gemini_result['error']}")
    
    results["tests"]["gemini"] = gemini_result
    
    # Comparison summary
    print(f"\\n📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    haiku_success = haiku_result.get("success", False)
    gemini_success = gemini_result.get("success", False)
    
    if haiku_success and gemini_success:
        print("✅ Both models generated commands")
        
        h_score = haiku_result.get("analysis", {}).get("completeness_score", 0)
        g_score = gemini_result.get("analysis", {}).get("completeness_score", 0)
        
        print(f"🎯 Completeness: Haiku {h_score:.2%} vs Gemini {g_score:.2%}")
        print(f"⏱️ Speed: Haiku {haiku_result['processing_time']:.2f}s vs Gemini {gemini_result['processing_time']:.2f}s")
        print(f"💰 Cost: Haiku ${haiku_result.get('cost', 0):.6f} vs Gemini ${gemini_result.get('cost', 0):.6f}")
        
        # Execution comparison
        h_exec = haiku_result.get("validation", {}).get("success", False)
        g_exec = gemini_result.get("validation", {}).get("success", False)
        
        if h_exec and g_exec:
            print("✅ Both commands executed successfully")
            
            h_dur = haiku_result["validation"].get("duration", 0)
            g_dur = gemini_result["validation"].get("duration", 0)
            
            print(f"🕐 Duration accuracy:")
            print(f"   • Haiku: {h_dur:.2f}s (diff: {abs(h_dur-18.0):.2f}s)")
            print(f"   • Gemini: {g_dur:.2f}s (diff: {abs(g_dur-18.0):.2f}s)")
            
        elif h_exec:
            print("🏆 Winner: HAIKU (only successful execution)")
        elif g_exec:
            print("🏆 Winner: GEMINI (only successful execution)")
        else:
            print("❌ Both commands failed execution")
            
        # Overall winner
        if h_score > g_score and h_exec:
            print("\\n🏆 OVERALL WINNER: HAIKU")
        elif g_score > h_score and g_exec:
            print("\\n🏆 OVERALL WINNER: GEMINI")
        else:
            print("\\n🤝 Result: TIE or inconclusive")
    
    elif haiku_success:
        print("🏆 WINNER: HAIKU (only successful generation)")
    elif gemini_success:
        print("🏆 WINNER: GEMINI (only successful generation)")
    else:
        print("❌ Both models failed to generate commands")
    
    # Save results
    results_file = Path(OUTPUT_DIR) / "live_llm_comparison_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\\n📂 Results saved: {results_file}")
    
    # Open directory
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print(f"📂 Opened output directory")
    except:
        pass
    
    return results

if __name__ == "__main__":
    asyncio.run(run_live_llm_comparison())