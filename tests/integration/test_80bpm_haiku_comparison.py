#!/usr/bin/env python3
"""
80 BPM Music Video - Haiku MCP Comparison Test
Based on successful baseline: 80bpm_subnautic_3sec_segments.mp4
Test Haiku command generation against proven working solution
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path

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
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/80bpm-comparison/"

# Reference working command (1761 characters)
REFERENCE_COMMAND = """ffmpeg -y -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4 -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac -filter_complex [0:v]trim=start=84.82:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=out:st=2.7:d=0.3[seg0];[0:v]trim=start=180.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg1];[0:v]trim=start=167.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg2];[0:v]trim=start=42.98:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg3];[0:v]trim=start=17.95:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg4];[0:v]trim=start=13.11:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3[seg5];[seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo];[1:a]atrim=duration=18.0[finalaudio] -map [finalvideo] -map [finalaudio] -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p"""

def create_haiku_optimized_prompt() -> str:
    """Haiku-optimized prompt based on successful 80 BPM solution"""
    return f"""Create an 80 BPM music video using FFMPEG with these exact specifications:

REQUIREMENTS:
- Input video: {VIDEO_SOURCE}
- Input audio: {AUDIO_SOURCE}
- Tempo: 80 BPM (4 beats = 3.0 seconds per segment)
- Total duration: exactly 18.0 seconds
- Output: {OUTPUT_DIR}haiku_80bpm.mp4

VIDEO SEGMENTS (use these exact timestamps):
1. Segment 1: 84.82s - 87.82s (3.0s duration)
2. Segment 2: 180.33s - 183.33s (3.0s duration) 
3. Segment 3: 167.33s - 170.33s (3.0s duration)
4. Segment 4: 42.98s - 45.98s (3.0s duration)
5. Segment 5: 17.95s - 20.95s (3.0s duration)
6. Segment 6: 13.11s - 16.11s (3.0s duration)

TRANSITIONS:
- 0.3 second fade in/out transitions between segments
- NO harsh cuts or white flashes

VIDEO EFFECTS:
- Segments 1-3: 8-bit retro effect (scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10)
- Segments 4-6: Leica cinematic look (colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4)

OUTPUT FORMAT:
- Codec: H.264 (-c:v libx264 -preset medium)
- Audio: AAC (-c:a aac -b:a 128k)
- Pixel format: yuv420p (user-compatible)

TASK: Generate the complete FFMPEG command that implements all these requirements in a single command."""

def create_simplified_prompt() -> str:
    """Simplified prompt for smaller models"""
    return f"""Create a music video using FFMPEG with these requirements:

- Extract 6 segments (3 seconds each) from video at specific timestamps
- Apply visual effects: 8-bit effect on first 3 segments, cinematic look on last 3 segments  
- Add smooth fade transitions (0.3 second) between segments
- Combine with audio track, trim to 18 seconds total
- Output as H.264 MP4 with YUV420P format

Input files:
- Video: {VIDEO_SOURCE}
- Audio: {AUDIO_SOURCE}

Segment times: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s (3s each)

Generate the FFMPEG command."""

async def test_haiku_mcp_command_generation(prompt: str, test_name: str) -> dict:
    """Test Haiku MCP command generation with CI validation"""
    
    print(f"🧠 Testing Haiku MCP: {test_name}")
    print(f"📝 Prompt length: {len(prompt)} characters")
    
    # Create test script for TypeScript Haiku MCP client
    test_script = f'''
const {{ HaikuMCPClient }} = require('/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/haiku-mcp-ts/client.js');

async function testHaikuCommandGeneration() {{
    const client = new HaikuMCPClient();
    
    try {{
        await client.connect();
        console.log("✅ Connected to Haiku MCP");
        
        // Test command generation
        const result = await client.callTool('generate_ffmpeg_command', {{
            task: 'create_80bpm_music_video',
            input_video: '{VIDEO_SOURCE}',
            input_audio: '{AUDIO_SOURCE}', 
            output_file: '{OUTPUT_DIR}haiku_{test_name}.mp4',
            requirements: {{
                bpm: 80,
                segments: {json.dumps(SEGMENTS)},
                duration: 18.0,
                effects: {{
                    segments_1_3: "8bit_retro",
                    segments_4_6: "leica_cinematic"
                }},
                transitions: "fade_0.3s"
            }},
            prompt: {json.dumps(prompt)}
        }});
        
        console.log("HAIKU_RESULT_START");
        console.log(JSON.stringify(result, null, 2));
        console.log("HAIKU_RESULT_END");
        
        await client.disconnect();
        
    }} catch (error) {{
        console.log("HAIKU_ERROR_START");
        console.log(JSON.stringify({{ error: error.message }}, null, 2));
        console.log("HAIKU_ERROR_END");
    }}
}}

testHaikuCommandGeneration().catch(console.error);
'''
    
    # Execute test
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    script_file = Path(OUTPUT_DIR) / f"test_{test_name}.js"
    
    with open(script_file, 'w') as f:
        f.write(test_script)
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            'node', str(script_file)
        ], capture_output=True, text=True, timeout=120, cwd=OUTPUT_DIR)
        
        processing_time = time.time() - start_time
        output = result.stdout + result.stderr
        
        # Parse Haiku result
        haiku_result = None
        haiku_error = None
        
        if "HAIKU_RESULT_START" in output:
            start_idx = output.find("HAIKU_RESULT_START") + len("HAIKU_RESULT_START")
            end_idx = output.find("HAIKU_RESULT_END")
            if end_idx > start_idx:
                try:
                    result_json = output[start_idx:end_idx].strip()
                    haiku_result = json.loads(result_json)
                except json.JSONDecodeError as e:
                    haiku_error = f"JSON decode error: {e}"
        
        if "HAIKU_ERROR_START" in output:
            start_idx = output.find("HAIKU_ERROR_START") + len("HAIKU_ERROR_START")
            end_idx = output.find("HAIKU_ERROR_END")
            if end_idx > start_idx:
                try:
                    error_json = output[start_idx:end_idx].strip()
                    haiku_error = json.loads(error_json)
                except:
                    haiku_error = output[start_idx:end_idx].strip()
        
        return {
            "test_name": test_name,
            "success": result.returncode == 0 and haiku_result is not None,
            "processing_time": processing_time,
            "haiku_result": haiku_result,
            "haiku_error": haiku_error,
            "raw_output": output,
            "prompt_used": prompt
        }
        
    except subprocess.TimeoutExpired:
        return {
            "test_name": test_name,
            "success": False,
            "processing_time": 120,
            "error": "Timeout (120s)",
            "prompt_used": prompt
        }
    except Exception as e:
        return {
            "test_name": test_name,
            "success": False,
            "processing_time": time.time() - start_time,
            "error": str(e),
            "prompt_used": prompt
        }

def analyze_command_similarity(generated_command: str, reference_command: str) -> dict:
    """Analyze similarity between generated and reference commands"""
    
    # Key components to check
    components = {
        "segment_extraction": ["trim=start=84.82", "trim=start=180.33", "trim=start=167.33", 
                               "trim=start=42.98", "trim=start=17.95", "trim=start=13.11"],
        "fade_transitions": ["fade=t=out:st=2.7:d=0.3", "fade=t=in:st=0:d=0.3"],
        "8bit_effects": ["scale=320:240", "scale=1280:720:flags=neighbor", "eq=contrast=1.3"],
        "leica_effects": ["colorbalance=rs=0.1", "eq=contrast=1.1", "vignette=angle=PI/4"],
        "concatenation": ["concat=n=6:v=1:a=0", "[finalvideo]"],
        "audio_processing": ["atrim=duration=18.0", "[finalaudio]"],
        "output_format": ["-c:v libx264", "-c:a aac", "-pix_fmt yuv420p"]
    }
    
    similarity_scores = {}
    
    for component, patterns in components.items():
        found_patterns = sum(1 for pattern in patterns if pattern in generated_command)
        similarity_scores[component] = found_patterns / len(patterns)
    
    overall_similarity = sum(similarity_scores.values()) / len(similarity_scores)
    
    return {
        "overall_similarity": overall_similarity,
        "component_scores": similarity_scores,
        "command_length_ratio": len(generated_command) / len(reference_command),
        "reference_length": len(reference_command),
        "generated_length": len(generated_command)
    }

async def validate_generated_command(command: str, test_name: str) -> dict:
    """Execute generated command and validate output"""
    
    print(f"🧪 Validating generated command: {test_name}")
    
    # Modify output path in command
    test_output = str(Path(OUTPUT_DIR) / f"haiku_{test_name}_validation.mp4")
    modified_command = command.replace("/tmp/kompo/haiku-ffmpeg/80bpm-comparison/haiku_80bpm.mp4", test_output)
    
    start_time = time.time()
    
    try:
        # Execute command
        result = subprocess.run(modified_command.split(), capture_output=True, text=True, timeout=60)
        processing_time = time.time() - start_time
        
        # Check output file
        output_file = Path(test_output)
        if output_file.exists():
            file_size = output_file.stat().st_size
            
            # Check duration with ffprobe
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
            
            return {
                "validation_success": True,
                "processing_time": processing_time,
                "file_size": file_size,
                "duration": duration,
                "duration_accuracy": abs(duration - 18.0) < 0.1 if duration else False,
                "output_file": str(output_file)
            }
        else:
            return {
                "validation_success": False,
                "processing_time": processing_time,
                "error": result.stderr,
                "ffmpeg_returncode": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        return {
            "validation_success": False,
            "processing_time": 60,
            "error": "Validation timeout"
        }
    except Exception as e:
        return {
            "validation_success": False,
            "processing_time": time.time() - start_time,
            "error": str(e)
        }

async def run_80bpm_haiku_comparison():
    """Execute comprehensive Haiku MCP comparison test"""
    
    print("🎵 80 BPM Music Video - Haiku MCP Comparison Test")
    print("=" * 60)
    print("📋 BASELINE VALIDATION:")
    print(f"   ✅ Reference file: 80bpm_subnautic_3sec_segments.mp4")
    print(f"   ✅ Size: 1,710,700 bytes")
    print(f"   ✅ Duration: 18.00s")
    print(f"   ✅ Command length: 1761 characters")
    
    # Test prompts
    test_prompts = {
        "haiku_optimized": create_haiku_optimized_prompt(),
        "simplified": create_simplified_prompt()
    }
    
    results = {}
    
    for test_name, prompt in test_prompts.items():
        print(f"\\n🧪 Running Haiku test: {test_name}")
        print("-" * 50)
        
        # Test command generation
        gen_result = await test_haiku_mcp_command_generation(prompt, test_name)
        results[test_name] = gen_result
        
        if gen_result["success"] and gen_result["haiku_result"]:
            # Extract generated command
            try:
                haiku_data = gen_result["haiku_result"]
                if "content" in haiku_data and haiku_data["content"]:
                    content = json.loads(haiku_data["content"][0]["text"])
                    generated_command = content.get("command_used", "")
                    
                    if generated_command:
                        # Analyze command similarity
                        similarity = analyze_command_similarity(generated_command, REFERENCE_COMMAND)
                        results[test_name]["similarity_analysis"] = similarity
                        
                        print(f"   📊 Similarity: {similarity['overall_similarity']:.2%}")
                        print(f"   📏 Command length: {similarity['generated_length']} chars (ref: {similarity['reference_length']})")
                        
                        # Validate command execution
                        if similarity['overall_similarity'] > 0.7:  # Only validate promising commands
                            validation = await validate_generated_command(generated_command, test_name)
                            results[test_name]["validation"] = validation
                            
                            if validation.get("validation_success"):
                                print(f"   ✅ Validation: SUCCESS")
                                print(f"   📁 Output: {validation['file_size']:,} bytes")
                                print(f"   🕐 Duration: {validation.get('duration', 'N/A'):.2f}s")
                            else:
                                print(f"   ❌ Validation: FAILED")
                                print(f"   💥 Error: {validation.get('error', 'Unknown')}")
                        else:
                            print(f"   ⚠️ Similarity too low ({similarity['overall_similarity']:.2%}) - skipping validation")
                    
            except Exception as e:
                print(f"   ❌ Command extraction failed: {e}")
        else:
            print(f"   ❌ Command generation: FAILED")
            print(f"   💥 Error: {gen_result.get('haiku_error', 'Unknown')}")
    
    # Save results
    results_file = Path(OUTPUT_DIR) / "haiku_80bpm_comparison_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "test_purpose": "Haiku MCP 80 BPM Music Video Command Generation Test",
            "baseline": {
                "reference_command": REFERENCE_COMMAND,
                "command_length": len(REFERENCE_COMMAND),
                "expected_output": "80bpm_subnautic_3sec_segments.mp4",
                "expected_size": 1710700,
                "expected_duration": 18.0
            },
            "test_results": results
        }, f, indent=2)
    
    # Summary
    print(f"\\n📊 HAIKU COMPARISON SUMMARY:")
    print("=" * 60)
    
    successful_tests = [k for k, v in results.items() if v.get("success", False)]
    validated_tests = [k for k, v in results.items() if v.get("validation", {}).get("validation_success", False)]
    
    print(f"✅ Command generation: {len(successful_tests)}/{len(results)}")
    print(f"✅ Command validation: {len(validated_tests)}/{len(results)}")
    
    if validated_tests:
        print(f"\\n🏆 SUCCESSFUL VALIDATIONS:")
        for test_name in validated_tests:
            result = results[test_name]
            validation = result["validation"]
            similarity = result["similarity_analysis"]
            
            print(f"   🎯 {test_name}:")
            print(f"      • Similarity: {similarity['overall_similarity']:.2%}")
            print(f"      • Duration: {validation.get('duration', 'N/A'):.2f}s")
            print(f"      • File size: {validation['file_size']:,} bytes")
            print(f"      • Processing: {validation['processing_time']:.2f}s")
    
    print(f"\\n📂 Results saved: {results_file}")
    
    # Open directory
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print(f"📂 Opened output directory for review")
    except:
        pass
    
    return results

if __name__ == "__main__":
    asyncio.run(run_80bpm_haiku_comparison())