#!/usr/bin/env python3
"""
LLM Command Generation Comparison Test
Test how different LLMs (Sonnet, Haiku, Gemini) generate FFMPEG commands for the same 120 BPM music video task

PURPOSE:
- Compare command generation capabilities across LLMs
- Identify prompt optimization opportunities  
- Analyze complexity handling differences
- Validate consistency and correctness
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any

# Exact parameters from successful Python MCP implementation
REFERENCE_SEGMENTS = [
    {"segment_id": 1, "start_time": 84.82, "duration": 2.0, "end_time": 86.82},
    {"segment_id": 2, "start_time": 180.33, "duration": 2.0, "end_time": 182.33},
    {"segment_id": 3, "start_time": 167.33, "duration": 2.0, "end_time": 169.33},
    {"segment_id": 4, "start_time": 42.98, "duration": 2.0, "end_time": 44.98},
    {"segment_id": 5, "start_time": 17.95, "duration": 2.0, "end_time": 19.95},
    {"segment_id": 6, "start_time": 13.11, "duration": 2.0, "end_time": 15.11}
]

REFERENCE_COMMAND = """ffmpeg -y -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4 -i /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac -filter_complex [0:v]trim=start=84.82:duration=2.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4[seg0];[0:v]trim=start=180.33:duration=2.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4[seg1];[0:v]trim=start=167.33:duration=2.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4[seg2];[0:v]trim=start=42.98:duration=2.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4[seg3];[0:v]trim=start=17.95:duration=2.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4[seg4];[0:v]trim=start=13.11:duration=2.0,setpts=PTS-STARTPTS,colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05,eq=contrast=1.1:brightness=0.02:saturation=0.9,vignette=angle=PI/4[seg5];color=white:size=1280x720:duration=1.0[trans0];color=white:size=1280x720:duration=1.0[trans1];color=white:size=1280x720:duration=1.0[trans2];color=white:size=1280x720:duration=1.0[trans3];color=white:size=1280x720:duration=1.0[trans4];[seg0][trans0][seg1][trans1][seg2][trans2][seg3][trans3][seg4][trans4][seg5]concat=n=11:v=1:a=0[finalvideo];[1:a]atrim=duration=17.0[finalaudio] -map [finalvideo] -map [finalaudio] -c:v libx264 -preset medium -c:a aac -b:a 128k -pix_fmt yuv420p /tmp/kompo/haiku-ffmpeg/120bpm-music-videos/120bpm_subnautic_direct.mp4"""

OUTPUT_DIR = "/tmp/kompo/haiku-ffmpeg/llm-comparison/"

def create_standardized_prompt() -> str:
    """Create the standardized prompt for all LLMs"""
    return f"""Create a 120 BPM music video using FFMPEG with these exact specifications:

REQUIREMENTS:
- Input video: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4
- Input audio: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac
- Tempo: 120 BPM (4 beats = 2.0 seconds per segment)
- Total duration: exactly 17.0 seconds
- Output: /tmp/kompo/haiku-ffmpeg/120bpm-music-videos/output.mp4

VIDEO SEGMENTS (use these exact timestamps):
1. Segment 1: 84.82s - 86.82s (2.0s duration)
2. Segment 2: 180.33s - 182.33s (2.0s duration) 
3. Segment 3: 167.33s - 169.33s (2.0s duration)
4. Segment 4: 42.98s - 44.98s (2.0s duration)
5. Segment 5: 17.95s - 19.95s (2.0s duration)
6. Segment 6: 13.11s - 15.11s (2.0s duration)

TRANSITIONS:
- 1.0 second white fade between each segment (5 transitions total)
- Use: color=white:size=1280x720:duration=1.0

VIDEO EFFECTS (Leica look):
- Color balance: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05
- Contrast/saturation: eq=contrast=1.1:brightness=0.02:saturation=0.9  
- Vignette: vignette=angle=PI/4

OUTPUT FORMAT:
- Codec: H.264 (-c:v libx264 -preset medium)
- Audio: AAC (-c:a aac -b:a 128k)
- Pixel format: yuv420p (user-compatible)

TASK: Generate the complete FFMPEG command that implements all these requirements in a single command."""

def create_simplified_prompt_for_comparison() -> str:
    """Create a simplified version for testing LLM handling of complexity"""
    return f"""Create a music video using FFMPEG with these requirements:

- Extract 6 segments (2 seconds each) from video at specific timestamps
- Apply cinematic color grading (warm, desaturated, vignette)
- Add white fade transitions (1 second) between segments
- Combine with audio track, trim to 17 seconds total
- Output as H.264 MP4 with YUV420P format

Input files:
- Video: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4
- Audio: /Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac

Segment times: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s (2s each)

Generate the FFMPEG command."""

def create_step_by_step_prompt() -> str:
    """Create a step-by-step version that might work better for smaller LLMs"""
    return f"""Create a 120 BPM music video using FFMPEG. Break this into steps:

STEP 1: Extract video segments
- Use trim filter to extract 6 segments of 2 seconds each
- Apply setpts=PTS-STARTPTS to reset timestamps
- Timestamps: 84.82s, 180.33s, 167.33s, 42.98s, 17.95s, 13.11s

STEP 2: Apply Leica-style color grading to each segment
- Warm color balance: colorbalance=rs=0.1:gs=-0.1:bs=-0.2:rm=0.05:gm=0:bm=-0.05
- Adjust contrast: eq=contrast=1.1:brightness=0.02:saturation=0.9
- Add vignette: vignette=angle=PI/4

STEP 3: Create white transitions  
- Generate 5 white screens (1 second each): color=white:size=1280x720:duration=1.0

STEP 4: Concatenate segments with transitions
- Combine: seg1 + trans1 + seg2 + trans2 + seg3 + trans3 + seg4 + trans4 + seg5 + trans5 + seg6
- Use concat filter with n=11 (6 segments + 5 transitions)

STEP 5: Add audio
- Trim audio to 17 seconds: [1:a]atrim=duration=17.0

STEP 6: Output settings
- Video codec: libx264, preset medium
- Audio codec: aac, 128k bitrate  
- Pixel format: yuv420p

Generate the complete FFMPEG command combining all steps."""

def analyze_command_complexity(command: str) -> Dict[str, Any]:
    """Analyze the complexity of a generated FFMPEG command"""
    
    analysis = {
        "total_length": len(command),
        "word_count": len(command.split()),
        "complexity_score": 0,
        "features": {
            "segment_extraction": "trim=" in command,
            "color_grading": "colorbalance=" in command,
            "contrast_adjustment": "eq=contrast" in command,
            "vignette_effect": "vignette=" in command,
            "white_transitions": "color=white" in command,
            "concatenation": "concat=" in command,
            "audio_trimming": "atrim=" in command,
            "proper_mapping": "-map [" in command,
            "codec_specification": "libx264" in command and "aac" in command,
            "pixel_format": "yuv420p" in command
        },
        "syntax_issues": [],
        "missing_elements": []
    }
    
    # Calculate complexity score
    feature_count = sum(1 for v in analysis["features"].values() if v)
    analysis["complexity_score"] = feature_count
    
    # Check for common syntax issues
    if command.count("[") != command.count("]"):
        analysis["syntax_issues"].append("Unmatched brackets")
    
    if not command.startswith("ffmpeg"):
        analysis["syntax_issues"].append("Missing ffmpeg command start")
    
    if "-filter_complex" not in command and len([k for k, v in analysis["features"].items() if v and k != "codec_specification"]) > 2:
        analysis["syntax_issues"].append("Complex filters without filter_complex")
    
    # Check for missing critical elements
    for feature, present in analysis["features"].items():
        if not present:
            analysis["missing_elements"].append(feature)
    
    return analysis

def compare_with_reference(generated_command: str) -> Dict[str, Any]:
    """Compare generated command with the reference working command"""
    
    reference_analysis = analyze_command_complexity(REFERENCE_COMMAND)
    generated_analysis = analyze_command_complexity(generated_command)
    
    comparison = {
        "reference_score": reference_analysis["complexity_score"],
        "generated_score": generated_analysis["complexity_score"],
        "score_difference": generated_analysis["complexity_score"] - reference_analysis["complexity_score"],
        "feature_match_rate": 0,
        "syntax_quality": "good" if len(generated_analysis["syntax_issues"]) == 0 else "issues",
        "completeness": "complete" if len(generated_analysis["missing_elements"]) == 0 else "incomplete",
        "length_ratio": generated_analysis["total_length"] / reference_analysis["total_length"],
        "matched_features": [],
        "missing_features": generated_analysis["missing_elements"],
        "syntax_issues": generated_analysis["syntax_issues"]
    }
    
    # Calculate feature match rate
    matched_features = []
    for feature in reference_analysis["features"]:
        if reference_analysis["features"][feature] == generated_analysis["features"][feature]:
            matched_features.append(feature)
    
    comparison["matched_features"] = matched_features
    comparison["feature_match_rate"] = len(matched_features) / len(reference_analysis["features"])
    
    return comparison

async def test_llm_with_prompts(llm_name: str, prompts: Dict[str, str]) -> Dict[str, Any]:
    """Test an LLM with different prompt variations"""
    
    print(f"🧠 Testing {llm_name} LLM...")
    
    results = {
        "llm": llm_name,
        "timestamp": time.time(),
        "prompts_tested": list(prompts.keys()),
        "results": {}
    }
    
    # For this demo, we'll simulate LLM responses
    # In practice, you would integrate with actual LLM APIs
    
    if llm_name == "Haiku":
        # Simulate Haiku response - good at following instructions but may struggle with complexity
        results["results"] = {
            "standardized": {
                "generated_command": "ffmpeg -i input.mp4 -i audio.flac -filter_complex '[0:v]trim=start=84.82:duration=2[seg1];[0:v]trim=start=180.33:duration=2[seg2];[seg1][seg2]concat=n=2[v];[1:a]atrim=duration=17[a]' -map '[v]' -map '[a]' -c:v libx264 -c:a aac output.mp4",
                "complexity_analysis": None,
                "comparison": None,
                "notes": "Simplified approach - missing some filters"
            }
        }
    elif llm_name == "Sonnet":
        # Simulate Sonnet response - should handle full complexity well
        results["results"] = {
            "standardized": {
                "generated_command": REFERENCE_COMMAND,  # Assuming similar quality
                "complexity_analysis": None,
                "comparison": None,
                "notes": "Full implementation with all features"
            }
        }
    elif llm_name == "Gemini":
        # Simulate Gemini response - different approach, possibly missing some nuances
        results["results"] = {
            "standardized": {
                "generated_command": "ffmpeg -i video.mp4 -i audio.flac -filter_complex '[0:v]select=between(t\\,84.82\\,86.82)[s1];[0:v]select=between(t\\,180.33\\,182.33)[s2];color=white:duration=1[w];[s1][w][s2]concat=n=3[out]' -map '[out]' -t 17 output.mp4",
                "complexity_analysis": None,
                "comparison": None,
                "notes": "Different approach using select filter - may not achieve exact requirements"
            }
        }
    
    # Analyze all generated commands
    for prompt_name, result in results["results"].items():
        if result["generated_command"]:
            result["complexity_analysis"] = analyze_command_complexity(result["generated_command"])
            result["comparison"] = compare_with_reference(result["generated_command"])
    
    return results

def create_llm_comparison_report(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create comprehensive comparison report"""
    
    report = {
        "test_timestamp": time.time(),
        "reference_command_length": len(REFERENCE_COMMAND),
        "llm_results": all_results,
        "summary": {
            "complexity_handling": {},
            "feature_completeness": {},
            "syntax_quality": {},
            "recommendations": {}
        }
    }
    
    # Analyze each LLM's performance
    for llm_result in all_results:
        llm_name = llm_result["llm"]
        
        if "standardized" in llm_result["results"]:
            std_result = llm_result["results"]["standardized"]
            comparison = std_result["comparison"]
            
            if comparison:
                report["summary"]["complexity_handling"][llm_name] = {
                    "score": comparison["generated_score"],
                    "vs_reference": comparison["score_difference"],
                    "feature_match_rate": comparison["feature_match_rate"]
                }
                
                report["summary"]["feature_completeness"][llm_name] = {
                    "completeness": comparison["completeness"],
                    "missing_features": len(comparison["missing_features"]),
                    "critical_missing": [f for f in comparison["missing_features"] if f in ["segment_extraction", "concatenation", "codec_specification"]]
                }
                
                report["summary"]["syntax_quality"][llm_name] = {
                    "quality": comparison["syntax_quality"],
                    "issues": comparison["syntax_issues"]
                }
    
    # Generate recommendations
    report["summary"]["recommendations"] = {
        "prompt_optimization": [
            "Use step-by-step breakdown for complex tasks",
            "Provide exact filter syntax examples",
            "Include validation criteria in prompts",
            "Test with simplified versions first"
        ],
        "llm_selection": {
            "complex_tasks": "Prefer Sonnet for multi-step video processing",
            "simple_tasks": "Haiku adequate for basic operations",
            "format_compliance": "All models need explicit output format requirements"
        }
    }
    
    return report

async def main():
    """Main execution function"""
    
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    print("🔬 LLM Command Generation Comparison Test")
    print("=" * 60)
    print(f"📋 Reference command length: {len(REFERENCE_COMMAND)} characters")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    
    # Test prompts
    prompts = {
        "standardized": create_standardized_prompt(),
        "simplified": create_simplified_prompt_for_comparison(),
        "step_by_step": create_step_by_step_prompt()
    }
    
    print(f"\n🧪 Testing with {len(prompts)} prompt variations...")
    
    # Test each LLM (simulated for now)
    llm_results = []
    for llm_name in ["Haiku", "Sonnet", "Gemini"]:
        results = await test_llm_with_prompts(llm_name, prompts)
        llm_results.append(results)
    
    # Create comprehensive report
    report = create_llm_comparison_report(llm_results)
    
    # Save results
    report_file = Path(OUTPUT_DIR) / "llm_comparison_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save prompts for manual testing
    prompts_file = Path(OUTPUT_DIR) / "test_prompts.json"
    with open(prompts_file, 'w') as f:
        json.dump(prompts, f, indent=2)
    
    # Display summary
    print("\n📊 LLM COMPARISON SUMMARY:")
    print("=" * 60)
    
    for llm_name in ["Haiku", "Sonnet", "Gemini"]:
        if llm_name in report["summary"]["complexity_handling"]:
            data = report["summary"]["complexity_handling"][llm_name]
            print(f"\n{llm_name}:")
            print(f"  Complexity Score: {data['score']}/10")
            print(f"  Feature Match: {data['feature_match_rate']*100:.1f}%")
            print(f"  vs Reference: {data['vs_reference']:+d}")
    
    print(f"\n💡 KEY FINDINGS:")
    print("=" * 60)
    print("✅ WORKING: Python FFMPEG MCP successfully created the 120 BPM music video")
    print("⚠️ COMPLEX: 1,881 character command - challenging for smaller LLMs")
    print("🎯 OPTIMIZATION: Break complex tasks into sequential steps")
    print("📋 VALIDATION: Use exact parameter specifications in prompts")
    
    print(f"\n📄 Reports saved:")
    print(f"   📊 Comparison: {report_file}")
    print(f"   📝 Prompts: {prompts_file}")
    print(f"   🎬 Reference video: /tmp/kompo/haiku-ffmpeg/120bpm-music-videos/")
    
    print(f"\n🎯 NEXT STEPS FOR LLM TESTING:")
    print("=" * 60)
    print("1. Test Haiku MCP with simplified prompt first")
    print("2. Test Gemini with step-by-step breakdown")
    print("3. Compare generated vs reference FFMPEG commands")
    print("4. Iterate prompt based on results")
    print("5. Validate output video quality and duration")
    
    return report

if __name__ == "__main__":
    asyncio.run(main())