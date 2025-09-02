#!/usr/bin/env python3
"""
80 BPM Music Video - Direct Haiku API Test
Uses existing HaikuSubagent to directly test command generation
Bypasses MCP connection issues and tests raw Haiku capability
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from src.haiku_subagent import HaikuSubagent

# Successful baseline parameters
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
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/80bpm-direct/"

# Reference working command (1761 characters)
REFERENCE_COMMAND = """ffmpeg -y -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4 -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac -filter_complex [0:v]trim=start=84.82:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=out:st=2.7:d=0.3[seg0];[0:v]trim=start=180.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg1];[0:v]trim=start=167.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg2];[0:v]trim=start=42.98:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg3];[0:v]trim=start=17.95:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg4];[0:v]trim=start=13.11:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3[seg5];[seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo];[1:a]atrim=duration=18.0[finalaudio] -map [finalvideo] -map [finalaudio] -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p"""

def create_haiku_ffmpeg_generation_prompt() -> str:
    """Create focused prompt for FFMPEG command generation"""
    return f"""You are a video processing expert. Generate a complete FFMPEG command for this 80 BPM music video task:

TASK: Create 80 BPM music video (18 seconds total)

INPUT FILES:
- Video: {VIDEO_SOURCE}
- Audio: {AUDIO_SOURCE}

SEGMENTS (extract these exact 6 segments, 3.0s each):
1. 84.82s-87.82s (3.0s) - apply 8-bit effect + fade out end
2. 180.33s-183.33s (3.0s) - apply 8-bit effect + fade in/out
3. 167.33s-170.33s (3.0s) - apply 8-bit effect + fade in/out
4. 42.98s-45.98s (3.0s) - apply Leica effect + fade in/out
5. 17.95s-20.95s (3.0s) - apply Leica effect + fade in/out
6. 13.11s-16.11s (3.0s) - apply Leica effect + fade in start

EFFECTS:
- 8-bit effect: scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10
- Leica effect: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4
- Transitions: 0.3s fade in/out between segments

OUTPUT:
- Format: H.264 MP4, AAC audio, yuv420p
- Duration: 18.0s exactly
- File: {OUTPUT_DIR}haiku_generated.mp4

Generate the complete FFMPEG command only. No explanation needed."""

async def test_haiku_ffmpeg_generation(haiku: HaikuSubagent, prompt: str) -> dict:
    """Test direct Haiku FFMPEG command generation"""
    
    print("🧠 Testing Haiku direct API for FFMPEG generation...")
    print(f"📝 Prompt: {len(prompt)} characters")
    
    start_time = time.time()
    
    try:
        # Use Haiku to generate FFMPEG command
        response = await haiku.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        processing_time = time.time() - start_time
        generated_command = response.content[0].text.strip()
        
        print(f"✅ Haiku response received ({processing_time:.2f}s)")
        print(f"📏 Generated command: {len(generated_command)} characters")
        
        # Analyze the command
        command_analysis = analyze_ffmpeg_command(generated_command)
        
        return {
            "success": True,
            "processing_time": processing_time,
            "generated_command": generated_command,
            "command_length": len(generated_command),
            "analysis": command_analysis,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens if hasattr(response, 'usage') else None,
            "cost_estimate": calculate_haiku_cost(response) if hasattr(response, 'usage') else None
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "success": False,
            "processing_time": processing_time,
            "error": str(e),
            "error_type": type(e).__name__
        }

def analyze_ffmpeg_command(command: str) -> dict:
    """Analyze generated FFMPEG command for correctness"""
    
    required_components = {
        "input_files": ["-i", VIDEO_SOURCE.split("/")[-1], AUDIO_SOURCE.split("/")[-1]],
        "segments": ["trim=start=84.82", "trim=start=180.33", "trim=start=167.33", 
                     "trim=start=42.98", "trim=start=17.95", "trim=start=13.11"],
        "durations": ["duration=3.0"] * 6,
        "8bit_effects": ["scale=320:240", "scale=1280:720:flags=neighbor"],
        "leica_effects": ["colorbalance=rs=0.1", "vignette=angle=PI/4"],
        "fade_transitions": ["fade=t=in", "fade=t=out", "d=0.3"],
        "concatenation": ["concat=n=6", "[finalvideo]"],
        "audio_processing": ["atrim=duration=18.0", "[finalaudio]"],
        "output_settings": ["-c:v libx264", "-c:a aac", "yuv420p"]
    }
    
    analysis = {}
    total_score = 0
    
    for component, patterns in required_components.items():
        found = sum(1 for pattern in patterns if pattern in command)
        expected = len(patterns)
        score = found / expected if expected > 0 else 0
        
        analysis[component] = {
            "found": found,
            "expected": expected, 
            "score": score
        }
        
        total_score += score
    
    overall_score = total_score / len(required_components)
    
    return {
        "overall_score": overall_score,
        "component_analysis": analysis,
        "command_valid": overall_score > 0.8,
        "critical_missing": [comp for comp, data in analysis.items() if data["score"] < 0.5]
    }

def calculate_haiku_cost(response) -> float:
    """Calculate estimated cost for Haiku usage"""
    if not hasattr(response, 'usage'):
        return 0.0
    
    # Haiku pricing (as of 2024): $0.25/1M input tokens, $1.25/1M output tokens
    input_cost = (response.usage.input_tokens / 1_000_000) * 0.25
    output_cost = (response.usage.output_tokens / 1_000_000) * 1.25
    
    return input_cost + output_cost

async def validate_generated_command(command: str) -> dict:
    """Execute generated command and validate output"""
    
    print("🧪 Validating generated FFMPEG command...")
    
    # Clean up command (remove any markdown formatting)
    clean_command = command.replace("```bash", "").replace("```", "").strip()
    if clean_command.startswith("ffmpeg"):
        # Modify output path
        test_output = str(Path(OUTPUT_DIR) / "haiku_validation.mp4")
        # Simple replacement of output file
        if OUTPUT_DIR in clean_command:
            clean_command = clean_command.replace(f"{OUTPUT_DIR}haiku_generated.mp4", test_output)
        else:
            # Append output if not found
            clean_command += f" {test_output}"
    else:
        return {"validation_success": False, "error": "Generated text is not an FFMPEG command"}
    
    start_time = time.time()
    
    try:
        # Execute command
        result = subprocess.run(clean_command.split(), capture_output=True, text=True, timeout=60)
        processing_time = time.time() - start_time
        
        # Check output
        output_file = Path(test_output)
        if output_file.exists():
            file_size = output_file.stat().st_size
            
            # Get duration
            duration_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(output_file)
            ], capture_output=True, text=True)
            
            duration = None
            duration_accurate = False
            
            if duration_result.returncode == 0:
                try:
                    duration = float(duration_result.stdout.strip())
                    duration_accurate = abs(duration - 18.0) < 0.2  # Allow 0.2s tolerance
                except ValueError:
                    pass
            
            return {
                "validation_success": True,
                "processing_time": processing_time,
                "output_file": str(output_file),
                "file_size": file_size,
                "duration": duration,
                "duration_accurate": duration_accurate,
                "ffmpeg_success": result.returncode == 0
            }
        else:
            return {
                "validation_success": False,
                "processing_time": processing_time,
                "error": f"No output file created. FFmpeg error: {result.stderr[-500:]}",
                "ffmpeg_returncode": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        return {
            "validation_success": False,
            "processing_time": 60,
            "error": "Command execution timeout"
        }
    except Exception as e:
        return {
            "validation_success": False,
            "processing_time": time.time() - start_time,
            "error": str(e)
        }

async def run_haiku_direct_test():
    """Execute direct Haiku FFMPEG generation test"""
    
    print("🎵 80 BPM Music Video - Direct Haiku API Test")
    print("=" * 60)
    print("📋 TESTING APPROACH:")
    print("   • Direct Anthropic Haiku API (bypasses MCP)")
    print("   • FFMPEG command generation task")
    print("   • Command analysis and validation")
    print("   • Cost and performance tracking")
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Initialize Haiku subagent
    try:
        haiku = HaikuSubagent()
        if not haiku.client:
            print("❌ No Anthropic API key found - testing with mock mode")
            # Could implement mock testing here
            return {"error": "No API key available"}
        
        print("✅ Haiku client initialized")
        
    except Exception as e:
        print(f"❌ Haiku initialization failed: {e}")
        return {"error": f"Initialization failed: {e}"}
    
    # Test command generation
    prompt = create_haiku_ffmpeg_generation_prompt()
    
    print(f"\\n🧠 GENERATING FFMPEG COMMAND...")
    print("-" * 50)
    
    generation_result = await test_haiku_ffmpeg_generation(haiku, prompt)
    
    if generation_result["success"]:
        print(f"✅ Command generation: SUCCESS")
        print(f"⏱️ Processing time: {generation_result['processing_time']:.2f}s")
        print(f"📏 Command length: {generation_result['command_length']} chars (ref: 1761)")
        print(f"🎯 Analysis score: {generation_result['analysis']['overall_score']:.2%}")
        
        if generation_result.get('cost_estimate'):
            print(f"💰 Estimated cost: ${generation_result['cost_estimate']:.6f}")
        
        if generation_result.get('tokens_used'):
            print(f"🪙 Tokens used: {generation_result['tokens_used']}")
        
        # Show analysis details
        analysis = generation_result['analysis']
        if analysis['critical_missing']:
            print(f"⚠️ Critical missing: {', '.join(analysis['critical_missing'])}")
        
        # Validate command if it looks promising
        if analysis['command_valid']:
            print(f"\\n🧪 VALIDATING COMMAND...")
            print("-" * 30)
            
            validation = await validate_generated_command(generation_result['generated_command'])
            
            if validation['validation_success']:
                print(f"✅ Validation: SUCCESS")
                print(f"📁 Output: {validation['file_size']:,} bytes")
                print(f"🕐 Duration: {validation.get('duration', 'N/A'):.2f}s")
                print(f"✅ Duration accurate: {validation.get('duration_accurate', False)}")
                
                generation_result['validation'] = validation
            else:
                print(f"❌ Validation: FAILED")
                print(f"💥 Error: {validation.get('error', 'Unknown')}")
                generation_result['validation'] = validation
        else:
            print(f"⚠️ Command quality too low ({analysis['overall_score']:.2%}) - skipping validation")
            
    else:
        print(f"❌ Command generation: FAILED")
        print(f"💥 Error: {generation_result.get('error', 'Unknown')}")
    
    # Save results
    results = {
        "timestamp": time.time(),
        "test_purpose": "Direct Haiku API FFMPEG Command Generation Test",
        "baseline": {
            "reference_command": REFERENCE_COMMAND,
            "command_length": len(REFERENCE_COMMAND),
            "expected_duration": 18.0,
            "expected_size": 1710700
        },
        "test_result": generation_result
    }
    
    results_file = Path(OUTPUT_DIR) / "haiku_direct_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print(f"\\n📊 HAIKU DIRECT TEST SUMMARY:")
    print("=" * 60)
    
    if generation_result["success"]:
        analysis = generation_result["analysis"]
        print(f"✅ Generation: SUCCESS ({generation_result['processing_time']:.2f}s)")
        print(f"🎯 Command quality: {analysis['overall_score']:.2%}")
        
        if generation_result.get("validation"):
            validation = generation_result["validation"]
            if validation["validation_success"]:
                print(f"✅ Execution: SUCCESS")
                print(f"📊 Duration accuracy: {validation.get('duration_accurate', False)}")
                print(f"📁 File size: {validation['file_size']:,} bytes")
            else:
                print(f"❌ Execution: FAILED")
                print(f"   Error: {validation.get('error', 'Unknown')[:100]}...")
        
        # Show generated command snippet
        cmd_preview = generation_result["generated_command"][:200] + "..."
        print(f"\\n📋 Generated command preview:")
        print(f"   {cmd_preview}")
        
    else:
        print(f"❌ Generation: FAILED")
        print(f"   Error: {generation_result.get('error', 'Unknown')}")
    
    print(f"\\n📂 Results saved: {results_file}")
    
    # Open directory
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print(f"📂 Opened output directory")
    except:
        pass
    
    return results

if __name__ == "__main__":
    asyncio.run(run_haiku_direct_test())