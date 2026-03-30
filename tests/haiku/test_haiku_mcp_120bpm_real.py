#!/usr/bin/env python3
"""
Real Haiku MCP 120 BPM Music Video Test
Test the actual TypeScript Haiku MCP server with the 120 BPM music video task
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path

OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/haiku-mcp-real-test/"
SEGMENTS = [
    {"segment_id": 1, "start_time": 84.82, "duration": 2.0},
    {"segment_id": 2, "start_time": 180.33, "duration": 2.0},
    {"segment_id": 3, "start_time": 167.33, "duration": 2.0},
    {"segment_id": 4, "start_time": 42.98, "duration": 2.0},
    {"segment_id": 5, "start_time": 17.95, "duration": 2.0},
    {"segment_id": 6, "start_time": 13.11, "duration": 2.0}
]

def create_haiku_optimized_prompt() -> str:
    """Create a Haiku-optimized prompt based on our analysis"""
    return f"""Create a 120 BPM music video. I need a simple approach that works reliably:

INPUTS:
- Video: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4  
- Audio: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac

REQUIREMENTS:
1. Extract 6 video segments (2 seconds each) at these times: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s
2. Apply warm cinematic color grading to each segment
3. Add 1-second white fades between segments
4. Combine with audio (17 seconds total)
5. Output as MP4 with H.264 video, AAC audio

Generate a working FFMPEG command. Keep it simple and reliable."""

def create_step_by_step_prompt() -> str:
    """Create a step-by-step prompt that might work better for Haiku"""
    return f"""Create a music video in steps. Generate FFMPEG commands for:

STEP 1: Extract the first video segment
- Extract 2 seconds starting at 84.82 seconds from the video
- Apply basic color correction for cinematic look
- Use: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4

STEP 2: Create white transition
- Generate 1 second of white video at 1280x720

Generate these two FFMPEG commands first, then I'll ask for the rest."""

async def test_haiku_mcp_with_prompt(prompt: str, test_name: str) -> dict:
    """Test Haiku MCP with a specific prompt"""
    
    print(f"🧠 Testing Haiku MCP: {test_name}")
    print(f"📝 Prompt length: {len(prompt)} characters")
    
    # Create test script for TypeScript client
    test_script = f'''
const {{ HaikuMCPClient }} = require('./haiku-mcp-ts/client.js');

async function testHaikuPrompt() {{
    const client = new HaikuMCPClient();
    
    try {{
        await client.connect();
        console.log("✅ Connected to Haiku MCP");
        
        // Test with music video prompt
        const result = await client.callTool('process_video_file', {{
            input_file: '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4',
            output_file: '{OUTPUT_DIR}haiku_{test_name}.mp4',
            operation: 'create_120bpm_music_video',
            parameters: {{
                audio_file: '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac',
                segments: {json.dumps(SEGMENTS)},
                prompt: {json.dumps(prompt)},
                bpm: 120,
                duration: 17.0
            }}
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

testHaikuPrompt().catch(console.error);
'''
    
    # Write and execute test script
    script_file = Path(OUTPUT_DIR) / f"test_{test_name}.js"
    script_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(script_file, 'w') as f:
        f.write(test_script)
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            'node', str(script_file)
        ], capture_output=True, text=True, timeout=120)
        
        processing_time = time.time() - start_time
        
        # Parse the result
        output = result.stdout + result.stderr
        
        # Extract Haiku result
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

async def analyze_haiku_capabilities():
    """Test Haiku MCP with different prompt strategies"""
    
    print("🎵 Real Haiku MCP 120 BPM Music Video Test")
    print("=" * 60)
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Test different prompts
    test_prompts = {
        "simplified": create_haiku_optimized_prompt(),
        "step_by_step": create_step_by_step_prompt()
    }
    
    results = {}
    
    for test_name, prompt in test_prompts.items():
        print(f"\n🧪 Running test: {test_name}")
        print("-" * 40)
        
        result = await test_haiku_mcp_with_prompt(prompt, test_name)
        results[test_name] = result
        
        # Display immediate results
        if result["success"]:
            print(f"✅ {test_name}: SUCCESS ({result['processing_time']:.2f}s)")
            
            if result["haiku_result"]:
                haiku_data = result["haiku_result"]
                if "content" in haiku_data and haiku_data["content"]:
                    try:
                        content = json.loads(haiku_data["content"][0]["text"])
                        if "command_used" in content:
                            cmd_length = len(content["command_used"])
                            print(f"   📏 Generated command: {cmd_length} characters")
                            print(f"   🧠 LLM tokens: {content.get('llm_tokens_used', 'N/A')}")
                            print(f"   💰 Cost: ${content.get('llm_cost', 'N/A')}")
                        
                        if "success" in content:
                            print(f"   🎬 Video creation: {'✅ Success' if content['success'] else '❌ Failed'}")
                            
                    except Exception as e:
                        print(f"   ⚠️ Response parsing error: {e}")
        else:
            print(f"❌ {test_name}: FAILED ({result['processing_time']:.2f}s)")
            if result.get("haiku_error"):
                print(f"   ❌ Error: {result['haiku_error']}")
    
    # Save comprehensive results
    results_file = Path(OUTPUT_DIR) / "haiku_mcp_test_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "test_purpose": "Real Haiku MCP 120 BPM Music Video Generation",
            "tests": results
        }, f, indent=2)
    
    # Analysis and recommendations
    print(f"\n📊 HAIKU MCP ANALYSIS:")
    print("=" * 60)
    
    successful_tests = [k for k, v in results.items() if v["success"]]
    failed_tests = [k for k, v in results.items() if not v["success"]]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n🎯 BEST PERFORMING APPROACH:")
        best_test = min(successful_tests, key=lambda k: results[k]["processing_time"])
        best_result = results[best_test]
        print(f"   🏆 {best_test}: {best_result['processing_time']:.2f}s")
        
        # Extract command if available
        if best_result["haiku_result"]:
            try:
                haiku_data = best_result["haiku_result"]
                content = json.loads(haiku_data["content"][0]["text"])
                if "command_used" in content:
                    cmd_file = Path(OUTPUT_DIR) / f"best_haiku_command_{best_test}.txt"
                    with open(cmd_file, 'w') as f:
                        f.write(f"# Best Haiku MCP Generated Command ({best_test})\n")
                        f.write(f"# Processing time: {best_result['processing_time']:.2f}s\n")
                        f.write(f"# Tokens used: {content.get('llm_tokens_used', 'N/A')}\n")
                        f.write(f"# Cost: ${content.get('llm_cost', 'N/A')}\n\n")
                        f.write(content["command_used"])
                    
                    print(f"   📄 Command saved: {cmd_file}")
            except:
                pass
    
    # Recommendations for prompt optimization
    print(f"\n💡 HAIKU OPTIMIZATION FINDINGS:")
    print("=" * 60)
    
    if failed_tests:
        print("❌ ISSUES IDENTIFIED:")
        for test_name in failed_tests:
            error = results[test_name].get("haiku_error", results[test_name].get("error", "Unknown"))
            print(f"   • {test_name}: {error}")
    
    print("\n🔧 RECOMMENDATIONS:")
    if len(successful_tests) > 0:
        print("✅ Haiku MCP can handle music video generation")
        print("   • Use simplified, direct prompts")
        print("   • Provide exact parameters and examples")
        print("   • Break complex tasks into steps if needed")
    else:
        print("⚠️ Haiku MCP struggling with complex video tasks")
        print("   • Consider using Python MCP for complex workflows") 
        print("   • Test with simpler prompts first")
        print("   • Verify MCP server configuration")
    
    print(f"\n📂 Results saved to: {OUTPUT_DIR}")
    
    # Open output directory
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print(f"📂 Opened output directory")
    except:
        pass
    
    return results

if __name__ == "__main__":
    asyncio.run(analyze_haiku_capabilities())