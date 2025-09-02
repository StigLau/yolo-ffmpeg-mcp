#!/usr/bin/env python3
"""
80 BPM Music Video - Command Validation Framework
Tests our reference command and provides framework for LLM comparison
Ready for Haiku/Gemini testing when API keys are available
"""

import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any

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
OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/80bpm-validation/"

# Our proven working command
REFERENCE_COMMAND = f"""ffmpeg -y -i {VIDEO_SOURCE} -i "{AUDIO_SOURCE}" -filter_complex [0:v]trim=start=84.82:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=out:st=2.7:d=0.3[seg0];[0:v]trim=start=180.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg1];[0:v]trim=start=167.33:duration=3.0,setpts=PTS-STARTPTS,scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg2];[0:v]trim=start=42.98:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg3];[0:v]trim=start=17.95:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3,fade=t=out:st=2.7:d=0.3[seg4];[0:v]trim=start=13.11:duration=3.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4,fade=t=in:st=0:d=0.3[seg5];[seg0][seg1][seg2][seg3][seg4][seg5]concat=n=6:v=1:a=0[finalvideo];[1:a]atrim=duration=18.0[finalaudio] -map [finalvideo] -map [finalaudio] -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p {OUTPUT_DIR}reference_validation.mp4"""

def create_llm_prompts() -> Dict[str, str]:
    """Create standardized prompts for LLM testing"""
    
    base_requirements = f"""Create an 80 BPM music video using FFMPEG with these specifications:

INPUT FILES:
- Video: {VIDEO_SOURCE}
- Audio: {AUDIO_SOURCE}

SEGMENTS (extract 6 segments, 3.0s each for 80 BPM timing):
1. 84.82s-87.82s → 8-bit effect + fade out at end
2. 180.33s-183.33s → 8-bit effect + fade in/out  
3. 167.33s-170.33s → 8-bit effect + fade in/out
4. 42.98s-45.98s → Leica effect + fade in/out
5. 17.95s-20.95s → Leica effect + fade in/out
6. 13.11s-16.11s → Leica effect + fade in at start

EFFECTS:
- 8-bit: scale=320:240,scale=1280:720:flags=neighbor,eq=contrast=1.3:brightness=0.05:saturation=1.2,hue=h=10
- Leica: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4
- Fades: 0.3s duration (fade=t=in:st=0:d=0.3 and fade=t=out:st=2.7:d=0.3)

OUTPUT:
- Duration: 18.0s exactly
- Format: H.264 MP4, AAC audio, yuv420p
- File: {OUTPUT_DIR}output.mp4"""
    
    return {
        "detailed": f"""{base_requirements}

TASK: Generate the complete FFMPEG command implementing all requirements.""",
        
        "simplified": f"""Create a music video using FFMPEG:

- Extract 6 video segments (3s each) at: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s
- Apply 8-bit retro effect to first 3 segments, cinematic look to last 3 segments
- Add 0.3s fade transitions between segments  
- Combine with audio, output as 18s H.264 MP4

Input: {VIDEO_SOURCE} and {AUDIO_SOURCE}

Generate the FFMPEG command.""",
        
        "step_by_step": f"""Create an 80 BPM music video step by step:

STEP 1: Extract segments
- Use trim filter: trim=start=84.82:duration=3.0 (and 5 more segments)
- Reset timestamps: setpts=PTS-STARTPTS

STEP 2: Apply effects  
- Segments 1-3: 8-bit retro scaling and color adjustments
- Segments 4-6: Leica color balance and vignette

STEP 3: Add transitions
- 0.3s fade in/out between segments

STEP 4: Concatenate and output
- concat=n=6:v=1:a=0 for video
- atrim=duration=18.0 for audio
- H.264/AAC encoding with yuv420p

Generate the complete FFMPEG command."""
    }

def analyze_command_quality(command: str) -> Dict[str, Any]:
    """Comprehensive analysis of FFMPEG command quality"""
    
    # Core components that must be present
    required_elements = {
        "input_files": {
            "patterns": ["-i", "JJVtt947FfI_136.mp4", "Subnautic Measures.flac"],
            "weight": 1.0,
            "critical": True
        },
        "segment_extraction": {
            "patterns": ["trim=start=84.82", "trim=start=180.33", "trim=start=167.33", 
                        "trim=start=42.98", "trim=start=17.95", "trim=start=13.11"],
            "weight": 2.0,
            "critical": True
        },
        "segment_duration": {
            "patterns": ["duration=3.0"],
            "weight": 1.5,
            "critical": True  
        },
        "8bit_effects": {
            "patterns": ["scale=320:240", "scale=1280:720:flags=neighbor", "eq=contrast=1.3"],
            "weight": 1.0,
            "critical": False
        },
        "leica_effects": {
            "patterns": ["colorbalance=rs=0.1", "eq=contrast=1.1", "vignette=angle=PI/4"],
            "weight": 1.0, 
            "critical": False
        },
        "fade_transitions": {
            "patterns": ["fade=t=in", "fade=t=out", "d=0.3"],
            "weight": 1.5,
            "critical": True
        },
        "concatenation": {
            "patterns": ["concat=n=6:v=1:a=0", "[finalvideo]"],
            "weight": 2.0,
            "critical": True
        },
        "audio_processing": {
            "patterns": ["atrim=duration=18.0", "[finalaudio]"],
            "weight": 1.5,
            "critical": True
        },
        "output_encoding": {
            "patterns": ["-c:v libx264", "-c:a aac", "yuv420p"],
            "weight": 1.0,
            "critical": True
        }
    }
    
    analysis_results = {}
    total_weighted_score = 0
    total_weight = 0
    critical_failures = []
    
    for component, config in required_elements.items():
        patterns = config["patterns"]
        weight = config["weight"]
        is_critical = config["critical"]
        
        found_patterns = sum(1 for pattern in patterns if pattern in command)
        component_score = found_patterns / len(patterns) if patterns else 0
        weighted_score = component_score * weight
        
        analysis_results[component] = {
            "found": found_patterns,
            "expected": len(patterns),
            "score": component_score,
            "weighted_score": weighted_score,
            "critical": is_critical,
            "passed": component_score > 0.7
        }
        
        if is_critical and component_score < 0.7:
            critical_failures.append(component)
        
        total_weighted_score += weighted_score
        total_weight += weight
    
    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
    
    # Quality assessment
    if overall_score >= 0.9 and not critical_failures:
        quality_rating = "EXCELLENT"
    elif overall_score >= 0.75 and len(critical_failures) <= 1:
        quality_rating = "GOOD"
    elif overall_score >= 0.6 and len(critical_failures) <= 2:
        quality_rating = "FAIR"
    else:
        quality_rating = "POOR"
    
    return {
        "overall_score": overall_score,
        "quality_rating": quality_rating,
        "component_analysis": analysis_results,
        "critical_failures": critical_failures,
        "command_length": len(command),
        "executable": command.strip().startswith("ffmpeg"),
        "validation_ready": overall_score > 0.8 and len(critical_failures) == 0
    }

async def validate_command_execution(command: str, test_name: str = "test") -> Dict[str, Any]:
    """Execute command and validate output"""
    
    print(f"🧪 Validating command: {test_name}")
    
    # Prepare command
    clean_command = command.strip()
    if not clean_command.startswith("ffmpeg"):
        return {"success": False, "error": "Not an FFMPEG command"}
    
    # Modify output path for validation
    test_output = Path(OUTPUT_DIR) / f"{test_name}_validation.mp4"
    
    # Replace output path in command
    if "reference_validation.mp4" in clean_command:
        clean_command = clean_command.replace("reference_validation.mp4", str(test_output))
    elif "output.mp4" in clean_command:
        clean_command = clean_command.replace("output.mp4", str(test_output))
    else:
        # Append output path
        clean_command += f" {test_output}"
    
    start_time = time.time()
    
    try:
        # Execute command with proper shell handling for spaces in paths
        result = subprocess.run(clean_command, shell=True, capture_output=True, text=True, timeout=120)
        execution_time = time.time() - start_time
        
        if test_output.exists():
            file_size = test_output.stat().st_size
            
            # Get duration using ffprobe
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
            
            # Quality checks
            duration_accurate = abs(duration - 18.0) < 0.2 if duration else False
            size_reasonable = 1_000_000 < file_size < 10_000_000  # 1MB - 10MB range
            
            return {
                "success": True,
                "execution_time": execution_time,
                "output_file": str(test_output),
                "file_size": file_size,
                "duration": duration,
                "duration_accurate": duration_accurate,
                "size_reasonable": size_reasonable,
                "ffmpeg_returncode": result.returncode,
                "quality_score": sum([duration_accurate, size_reasonable, result.returncode == 0]) / 3
            }
        else:
            return {
                "success": False,
                "execution_time": execution_time,
                "error": f"No output file. FFMPEG stderr: {result.stderr[-300:]}",
                "ffmpeg_returncode": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "execution_time": 120,
            "error": "Command execution timeout (120s)"
        }
    except Exception as e:
        return {
            "success": False,
            "execution_time": time.time() - start_time,
            "error": str(e)
        }

async def run_validation_framework():
    """Execute comprehensive command validation framework"""
    
    print("🎵 80 BPM Music Video - Command Validation Framework")
    print("=" * 60)
    print("📋 FRAMEWORK PURPOSE:")
    print("   • Validate our reference working command")
    print("   • Establish quality metrics for LLM comparison")
    print("   • Provide ready framework for Haiku/Gemini testing")
    print("   • Document CI test requirements")
    
    # Ensure output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    results = {
        "timestamp": time.time(),
        "test_purpose": "80 BPM Command Validation Framework",
        "baseline_command": REFERENCE_COMMAND,
        "prompts": create_llm_prompts()
    }
    
    print(f"\\n📋 REFERENCE COMMAND VALIDATION")
    print("-" * 50)
    
    # Analyze reference command
    reference_analysis = analyze_command_quality(REFERENCE_COMMAND)
    
    print(f"📊 Reference Analysis:")
    print(f"   • Overall score: {reference_analysis['overall_score']:.2%}")
    print(f"   • Quality rating: {reference_analysis['quality_rating']}")
    print(f"   • Command length: {reference_analysis['command_length']} chars")
    print(f"   • Critical failures: {len(reference_analysis['critical_failures'])}")
    
    if reference_analysis['validation_ready']:
        print(f"   ✅ Ready for execution validation")
        
        # Execute reference command
        reference_validation = await validate_command_execution(REFERENCE_COMMAND, "reference")
        
        if reference_validation['success']:
            print(f"   ✅ Execution: SUCCESS ({reference_validation['execution_time']:.2f}s)")
            print(f"   📁 File: {reference_validation['file_size']:,} bytes")
            print(f"   🕐 Duration: {reference_validation['duration']:.2f}s (accurate: {reference_validation['duration_accurate']})")
            print(f"   🎯 Quality: {reference_validation['quality_score']:.2%}")
        else:
            print(f"   ❌ Execution: FAILED")
            print(f"   💥 Error: {reference_validation['error']}")
        
        results["reference_validation"] = reference_validation
    else:
        print(f"   ⚠️ Reference command has issues - not executing")
        results["reference_validation"] = {"success": False, "reason": "Quality issues"}
    
    results["reference_analysis"] = reference_analysis
    
    # Show LLM testing framework
    print(f"\\n📋 LLM TESTING FRAMEWORK READY")
    print("-" * 40)
    
    prompts = create_llm_prompts()
    
    for prompt_name, prompt_text in prompts.items():
        print(f"\\n🔸 {prompt_name.upper()} PROMPT:")
        print(f"   • Length: {len(prompt_text)} characters")
        print(f"   • Preview: {prompt_text[:100]}...")
        
        # Show what quality score this should achieve
        if prompt_name == "detailed":
            print(f"   • Expected quality: 85-95% (comprehensive requirements)")
        elif prompt_name == "simplified":
            print(f"   • Expected quality: 70-85% (basic requirements)")
        else:
            print(f"   • Expected quality: 75-90% (structured approach)")
    
    # Save results
    results_file = Path(OUTPUT_DIR) / "validation_framework_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create LLM test template
    test_template = {
        "llm_test_template": {
            "instruction": "Use this template to test LLM command generation",
            "steps": [
                "1. Send prompt to LLM (Haiku/Gemini/etc)",
                "2. Extract generated FFMPEG command from response", 
                "3. Analyze command quality using analyze_command_quality()",
                "4. If quality > 80%, validate execution using validate_command_execution()",
                "5. Compare results with reference baseline"
            ],
            "prompts": prompts,
            "success_criteria": {
                "minimum_quality_score": 0.75,
                "maximum_critical_failures": 1,
                "execution_success_required": True,
                "duration_tolerance_seconds": 0.2
            }
        }
    }
    
    template_file = Path(OUTPUT_DIR) / "llm_test_template.json"
    with open(template_file, 'w') as f:
        json.dump(test_template, f, indent=2)
    
    # Summary
    print(f"\\n📊 VALIDATION FRAMEWORK SUMMARY")
    print("=" * 60)
    
    if reference_analysis['quality_rating'] in ['EXCELLENT', 'GOOD']:
        print(f"✅ Reference command: {reference_analysis['quality_rating']} ({reference_analysis['overall_score']:.2%})")
    else:
        print(f"⚠️ Reference command: {reference_analysis['quality_rating']} ({reference_analysis['overall_score']:.2%})")
    
    if results.get("reference_validation", {}).get("success"):
        validation = results["reference_validation"]
        print(f"✅ Execution validation: SUCCESS")
        print(f"   • Duration: {validation['duration']:.2f}s (target: 18.0s)")
        print(f"   • File size: {validation['file_size']:,} bytes") 
        print(f"   • Quality score: {validation['quality_score']:.2%}")
    else:
        print(f"❌ Execution validation: FAILED")
    
    print(f"\\n📋 FRAMEWORK READY FOR:")
    print(f"   • Haiku command generation testing")
    print(f"   • Gemini command generation testing")
    print(f"   • Any LLM FFMPEG capability assessment")
    print(f"   • CI/CD integration for command validation")
    
    print(f"\\n📂 Files created:")
    print(f"   • {results_file}")
    print(f"   • {template_file}")
    
    # Open directory  
    try:
        subprocess.run(['open', OUTPUT_DIR])
        print(f"   📂 Opened output directory")
    except:
        pass
    
    return results

if __name__ == "__main__":
    asyncio.run(run_validation_framework())