#!/usr/bin/env python3
"""
Registry-Guided LLM Collaboration Test
Test the multimedia registry system, then use it to guide collaborative LLM FFMPEG generation.
Tests: Sonnet baseline + Haiku + Gemini Flash + Gemini Pro 2.5
"""

import asyncio
import json
import subprocess
import time
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# API clients
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Try to import the MCP server registry functions
try:
    import sys
    sys.path.insert(0, 'src')
    from server import mcp
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ MCP server not available - will use fallback mode")

OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/registry-guided/"

# Our test files
TEST_VIDEO = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4"
TEST_AUDIO = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac"

# Our working baseline command (Sonnet-generated)
SONNET_BASELINE = """ffmpeg -y -i '{video}' -i '{audio}' -filter_complex "[0:v]trim=start=84.82:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=out:st=2.7:d=0.3[seg0];[0:v]trim=start=180.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg1];[0:v]trim=start=167.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg2];[0:v]trim=start=42.98:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg3];[0:v]trim=start=17.95:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg4];[0:v]trim=start=13.11:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3[seg5];[seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo];[1:a]atrim=duration=18.0[finalaudio]" -map "[finalvideo]" -map "[finalaudio]" -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p {output}"""

async def test_registry_system() -> Dict[str, Any]:
    """Test the multimedia registry system first"""
    
    print("🗂️ Testing Multimedia Registry System...")
    print("-" * 50)
    
    registry_status = {"available": False, "files": [], "errors": []}
    
    if not MCP_AVAILABLE:
        registry_status["errors"].append("MCP server not available")
        print("❌ MCP server not available")
        return registry_status
    
    try:
        # Test list_files function
        print("📋 Testing list_files...")
        files_result = await mcp.call_tool('list_files', {})
        print(f"   Found: {len(files_result.get('files', []))} files")
        
        registry_status["files"] = files_result.get('files', [])
        registry_status["available"] = True
        
        # Look for our test files
        test_files = [f for f in registry_status["files"] if any(name in f.get('filename', '') for name in ['JJVtt947FfI', 'Subnautic'])]
        
        print(f"   Test files found: {len(test_files)}")
        for file in test_files:
            print(f"      • {file.get('filename', 'Unknown')} (ID: {file.get('id', 'N/A')})")
        
        if not test_files:
            print("⚠️ Test files not in registry - they may need to be added")
            registry_status["errors"].append("Test files not found in registry")
        
    except Exception as e:
        print(f"❌ Registry test failed: {e}")
        registry_status["errors"].append(str(e))
        registry_status["available"] = False
    
    return registry_status

def create_registry_guided_prompt(registry_info: Dict[str, Any], model_name: str) -> str:
    """Create a registry-guided prompt that instructs the model to use proper file references"""
    
    # Extract file info if available
    test_files_info = ""
    if registry_info.get("available") and registry_info.get("files"):
        for file in registry_info["files"]:
            if any(name in file.get('filename', '') for name in ['JJVtt947FfI', 'Subnautic']):
                test_files_info += f"- File ID: {file.get('id', 'N/A')} | Name: {file.get('filename', 'Unknown')} | Type: {file.get('content_type', 'Unknown')}\n"
    
    registry_guidance = ""
    if registry_info.get("available"):
        registry_guidance = f"""
🗂️ REGISTRY SYSTEM GUIDANCE:
This FFMPEG MCP server uses a multimedia registry system. The files you need are:

{test_files_info}

IMPORTANT: Use file IDs, not direct paths. The registry manages all file access.
However, for this FFMPEG command generation test, you can use the actual paths provided below.
"""
    else:
        registry_guidance = """
🗂️ REGISTRY SYSTEM NOTE:
The MCP registry is not available. Use direct file paths as provided.
"""
    
    # Collaborative prompt that encourages learning from Sonnet's approach
    prompt = f"""You are helping create an 80 BPM music video using FFMPEG. This is a collaborative effort where multiple AI models work together.

{registry_guidance}

🎯 TASK: Generate FFMPEG command for 80 BPM music video (18 seconds total)

📁 INPUT FILES:
- Video: {TEST_VIDEO}
- Audio: {TEST_AUDIO}

📊 SUCCESSFUL BASELINE PATTERN:
A Sonnet model previously generated a working solution. Learn from this approach:

KEY SUCCESSFUL ELEMENTS:
1. ✅ Segment extraction: Use trim=start=X:duration=3.0 (NOT trim=start:end)
2. ✅ Timestamp reset: ALWAYS add setpts=PTS-STARTPTS after trim
3. ✅ Six specific segments: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s
4. ✅ Effects: 8-bit on first 3 segments, Leica on last 3 segments  
5. ✅ Fades: 0.3s duration, different for each segment position
6. ✅ Concatenation: [seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo]
7. ✅ Audio: [1:a]atrim=duration=18.0[finalaudio]
8. ✅ Output: -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p

🎨 EFFECTS TO APPLY:
- 8-bit (segments 1-3): scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10
- Leica (segments 4-6): colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4

🔄 FADES (0.3s duration):
- Segment 1: fade out at end only
- Segments 2-5: fade in at start AND fade out at end
- Segment 6: fade in at start only

OUTPUT FILE: {OUTPUT_DIR}{model_name.lower()}_collaborative.mp4

🤝 COLLABORATION GOALS:
As {model_name}, you're contributing to a team effort. Focus on:
- Following the proven successful pattern above
- Making your command as similar as possible to the working baseline
- Avoiding common pitfalls (missing setpts, wrong trim syntax, file path issues)

Generate ONLY the complete FFMPEG command. Make it work reliably."""

    return prompt

async def test_llm_with_registry_guidance(model_name: str, client, prompt: str) -> Dict[str, Any]:
    """Test a specific LLM with registry guidance"""
    
    print(f"🧠 Testing {model_name} with registry guidance...")
    
    start_time = time.time()
    
    try:
        if "haiku" in model_name.lower():
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
            )
            generated_command = response.content[0].text.strip()
            cost = ((response.usage.input_tokens * 0.25) + (response.usage.output_tokens * 1.25)) / 1_000_000
            tokens = {"input": response.usage.input_tokens, "output": response.usage.output_tokens}
            
        elif "gemini" in model_name.lower():
            if "pro-2" in model_name.lower():
                model = genai.GenerativeModel('gemini-2.0-flash-exp')
                cost = 0.0  # Experimental model pricing
            else:
                model = genai.GenerativeModel('gemini-1.5-flash')
                cost = 0.0  # Free tier
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )
            generated_command = response.text.strip()
            tokens = {"input": 0, "output": 0}  # Gemini doesn't expose token counts easily
        else:
            return {"success": False, "error": f"Unknown model: {model_name}"}
        
        processing_time = time.time() - start_time
        
        # Clean command (remove markdown if present)
        if "```" in generated_command:
            parts = generated_command.split("```")
            for part in parts:
                if "ffmpeg" in part and not part.strip().startswith("bash"):
                    generated_command = part.strip()
                    break
        
        return {
            "success": True,
            "processing_time": processing_time,
            "generated_command": generated_command,
            "command_length": len(generated_command),
            "cost": cost,
            "tokens": tokens
        }
        
    except Exception as e:
        return {
            "success": False,
            "processing_time": time.time() - start_time,
            "error": str(e)
        }

def analyze_command_similarity_to_baseline(command: str, baseline: str) -> Dict[str, Any]:
    """Analyze how similar a command is to the Sonnet baseline"""
    
    # Key patterns to check
    critical_patterns = {
        "trim_syntax": "trim=start=\\d+\\.\\d+:duration=3\\.0",
        "setpts": "setpts=PTS-STARTPTS",
        "8bit_effects": "scale=320:240,scale=1280:720:flags=neighbor",
        "leica_effects": "colorbalance=rs=0\\.1.*vignette=angle=PI/4",
        "fades": "fade=t=(in|out):st=\\d+\\.\\d+:d=0\\.3",
        "concatenation": "concat=n=6:v=1:a=0\\[finalvideo\\]",
        "audio_trim": "atrim=duration=18\\.0",
        "output_settings": "-c:v libx264.*-pix_fmt yuv420p"
    }
    
    # Count pattern matches
    import re
    pattern_matches = {}
    
    for pattern_name, pattern in critical_patterns.items():
        matches = len(re.findall(pattern, command))
        expected = len(re.findall(pattern, baseline))
        
        pattern_matches[pattern_name] = {
            "found": matches,
            "expected": expected,
            "score": min(matches / expected, 1.0) if expected > 0 else 0.0
        }
    
    # Calculate overall similarity score
    weighted_scores = {
        "trim_syntax": 0.20,
        "setpts": 0.15,
        "8bit_effects": 0.10,
        "leica_effects": 0.10,
        "fades": 0.15,
        "concatenation": 0.15,
        "audio_trim": 0.10,
        "output_settings": 0.05
    }
    
    overall_score = sum(
        pattern_matches[pattern]["score"] * weight
        for pattern, weight in weighted_scores.items()
    )
    
    return {
        "overall_score": overall_score,
        "pattern_matches": pattern_matches,
        "likely_executable": overall_score > 0.8,
        "critical_issues": [
            pattern for pattern, data in pattern_matches.items()
            if data["score"] < 0.5 and weighted_scores[pattern] > 0.10
        ]
    }

async def validate_command_execution(command: str, model_name: str) -> Dict[str, Any]:
    """Execute and validate a generated command"""
    
    print(f"   🧪 Executing {model_name} command...")
    
    # Prepare command with correct file paths
    clean_command = command.format(
        video=TEST_VIDEO,
        audio=TEST_AUDIO,
        output=f"{OUTPUT_DIR}{model_name.lower()}_collaborative.mp4"
    )
    
    start_time = time.time()
    
    try:
        result = subprocess.run(clean_command, shell=True, capture_output=True, text=True, timeout=120)
        execution_time = time.time() - start_time
        
        output_file = Path(f"{OUTPUT_DIR}{model_name.lower()}_collaborative.mp4")
        
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
            
            duration_accuracy = abs(duration - 18.0) if duration else 999
            
            return {
                "success": True,
                "execution_time": execution_time,
                "output_file": str(output_file),
                "file_size": file_size,
                "duration": duration,
                "duration_accuracy": duration_accuracy,
                "quality_score": 1.0 if duration_accuracy < 0.2 else 0.5
            }
        else:
            return {
                "success": False,
                "execution_time": execution_time,
                "error": f"No output file. FFMPEG error: {result.stderr[-300:]}"
            }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "execution_time": 120, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "execution_time": time.time() - start_time, "error": str(e)}

async def run_registry_guided_collaboration():
    """Run the complete registry-guided LLM collaboration test"""
    
    print("🎵 Registry-Guided LLM Collaboration Test")
    print("=" * 60)
    print("🎯 APPROACH:")
    print("   1. Test multimedia registry system")
    print("   2. Guide LLMs using registry + Sonnet baseline")
    print("   3. Compare collaborative vs previous results")
    print("   4. Test: Haiku, Gemini Flash, Gemini Pro 2.5")
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Test registry system
    print(f"\n🗂️ STEP 1: REGISTRY SYSTEM TEST")
    print("=" * 40)
    
    registry_info = await test_registry_system()
    
    # Step 2: Initialize LLM clients
    print(f"\n🤖 STEP 2: LLM CLIENT INITIALIZATION")
    print("=" * 40)
    
    clients = {}
    
    # Anthropic Haiku
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        clients["Haiku"] = anthropic.Anthropic(api_key=api_key)
        print("✅ Haiku client initialized")
    else:
        print("❌ Haiku client failed - no API key")
    
    # Gemini clients
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        genai.configure(api_key=gemini_key)
        clients["Gemini-Flash"] = "gemini_flash"  # Placeholder for client type
        clients["Gemini-Pro-2.5"] = "gemini_pro_2"
        print("✅ Gemini clients initialized")
    else:
        print("❌ Gemini clients failed - no API key")
    
    # Step 3: Run collaborative tests
    print(f"\n🤝 STEP 3: COLLABORATIVE LLM TESTS")
    print("=" * 40)
    
    results = {
        "timestamp": time.time(),
        "registry_info": registry_info,
        "baseline_command": SONNET_BASELINE,
        "llm_results": {}
    }
    
    for model_name, client in clients.items():
        print(f"\n🧠 Testing {model_name}")
        print("-" * 30)
        
        # Create registry-guided prompt
        prompt = create_registry_guided_prompt(registry_info, model_name)
        
        # Test command generation
        generation_result = await test_llm_with_registry_guidance(model_name, client, prompt)
        
        if generation_result["success"]:
            print(f"✅ Generation: SUCCESS ({generation_result['processing_time']:.2f}s)")
            print(f"💰 Cost: ${generation_result['cost']:.6f}")
            
            # Analyze similarity to baseline
            similarity = analyze_command_similarity_to_baseline(
                generation_result["generated_command"], 
                SONNET_BASELINE
            )
            
            print(f"🎯 Similarity to baseline: {similarity['overall_score']:.2%}")
            print(f"🔧 Likely executable: {similarity['likely_executable']}")
            
            generation_result["similarity_analysis"] = similarity
            
            # Execute if promising
            if similarity["likely_executable"]:
                validation = await validate_command_execution(
                    generation_result["generated_command"], 
                    model_name
                )
                generation_result["validation"] = validation
                
                if validation["success"]:
                    print(f"✅ Execution: SUCCESS ({validation['execution_time']:.2f}s)")
                    print(f"📁 Duration: {validation['duration']:.2f}s (accuracy: {validation['duration_accuracy']:.2f}s)")
                else:
                    print(f"❌ Execution: FAILED")
                    print(f"   Error: {validation['error'][:100]}...")
            else:
                print(f"⚠️ Similarity too low - skipping execution")
                if similarity["critical_issues"]:
                    print(f"   Critical issues: {', '.join(similarity['critical_issues'])}")
        
        else:
            print(f"❌ Generation: FAILED")
            print(f"   Error: {generation_result['error']}")
        
        results["llm_results"][model_name] = generation_result
    
    # Step 4: Collaboration analysis
    print(f"\n📊 STEP 4: COLLABORATION ANALYSIS")
    print("=" * 40)
    
    successful_models = [
        model for model, result in results["llm_results"].items()
        if result.get("success") and result.get("validation", {}).get("success")
    ]
    
    print(f"✅ Successful executions: {len(successful_models)}/{len(clients)}")
    
    if successful_models:
        print(f"\n🏆 SUCCESSFUL MODELS:")
        for model in successful_models:
            result = results["llm_results"][model]
            similarity = result["similarity_analysis"]["overall_score"]
            duration = result["validation"]["duration"]
            
            print(f"   • {model}: {similarity:.2%} similarity, {duration:.2f}s duration")
        
        # Best collaborative result
        best_model = max(successful_models, 
                        key=lambda m: results["llm_results"][m]["similarity_analysis"]["overall_score"])
        
        print(f"\n🥇 BEST COLLABORATIVE RESULT: {best_model}")
        best_result = results["llm_results"][best_model]
        print(f"   • Similarity: {best_result['similarity_analysis']['overall_score']:.2%}")
        print(f"   • Duration accuracy: {best_result['validation']['duration_accuracy']:.2f}s")
        print(f"   • Processing time: {best_result['processing_time']:.2f}s")
        print(f"   • Cost: ${best_result['cost']:.6f}")
    
    # Registry impact analysis
    print(f"\n🗂️ REGISTRY IMPACT ANALYSIS:")
    if registry_info["available"]:
        print("✅ Registry system operational")
        print(f"   • Files in registry: {len(registry_info['files'])}")
        print("   • LLMs received proper file guidance")
    else:
        print("❌ Registry system not available")
        print("   • LLMs used direct file paths")
        print("   • Recommend fixing registry for better abstraction")
    
    # Save results
    results_file = Path(OUTPUT_DIR) / "registry_guided_collaboration_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📂 Results saved: {results_file}")
    
    # Open directory
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print(f"📂 Opened output directory")
    except:
        pass
    
    return results

if __name__ == "__main__":
    asyncio.run(run_registry_guided_collaboration())