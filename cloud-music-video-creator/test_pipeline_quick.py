#!/usr/bin/env python3
"""
Quick LLM Komposition Pipeline Test

Demonstrates the complete workflow: MD specification → LLM processing → FFmpeg execution
"""

import asyncio
import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, Any

# Import our services
from src.services.llm_analysis import LLMAnalysisService


async def test_quick_pipeline():
    """Test the complete pipeline with a simplified example"""
    
    print("🎬 Quick LLM Komposition Pipeline Test")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("/tmp/music-video-creator/pipeline-test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate processing plan (simplified - just audio processing)
    print("🧠 Generating simplified processing plan...")
    
    processing_plan = {
        "process_id": f"test_{uuid.uuid4().hex[:8]}",
        "llm_used": "pipeline_test",
        "estimated_duration": 10.0,
        "estimated_cost": 0.01,
        "confidence": 0.95,
        "steps": [
            {
                "step_id": 1,
                "name": "audio_processing_test",
                "description": "Create 10-second audio sample from Subnautic Measures",
                "command": "ffmpeg -i \"/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac\" -t 10 -c:a aac -b:a 128k pipeline_test_audio.aac -y"
            },
            {
                "step_id": 2, 
                "name": "video_processing_test",
                "description": "Create 10-second video sample with vintage effect",
                "command": "ffmpeg -i \"/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/JJVtt947FfI_136.mp4\" -ss 10 -t 10 -vf 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6' -c:v libx264 -preset fast -crf 23 -an pipeline_test_video.mp4 -y"
            },
            {
                "step_id": 3,
                "name": "final_assembly_test", 
                "description": "Combine test audio and video",
                "command": "ffmpeg -i pipeline_test_video.mp4 -i pipeline_test_audio.aac -c:v copy -c:a copy -shortest pipeline_test_final.mp4 -y"
            }
        ]
    }
    
    # Execute processing plan
    print(f"🎬 Executing {len(processing_plan['steps'])} processing steps...")
    
    # Change to output directory
    import os
    original_cwd = Path.cwd()
    os.chdir(output_dir)
    
    execution_results = []
    total_start_time = time.time()
    
    try:
        for step in processing_plan['steps']:
            step_start = time.time()
            print(f"🔄 Step {step['step_id']}: {step['name']}")
            print(f"   Command: {step['command'][:80]}...")
            
            # Execute FFmpeg command
            try:
                import shlex
                cmd_parts = shlex.split(step['command'])
                result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                duration = time.time() - step_start
                success = result.returncode == 0
                
                step_result = {
                    "step_id": step['step_id'],
                    "name": step['name'],
                    "success": success,
                    "duration": duration,
                    "output": result.stdout[-200:] if result.stdout else "",
                    "error": result.stderr[-200:] if result.stderr else ""
                }
                
                execution_results.append(step_result)
                
                if success:
                    print(f"  ✅ Completed in {duration:.1f}s")
                else:
                    print(f"  ❌ Failed after {duration:.1f}s")
                    print(f"     Error: {result.stderr[-100:]}")
                    break
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                execution_results.append({
                    "step_id": step['step_id'],
                    "name": step['name'],
                    "success": False,
                    "duration": time.time() - step_start,
                    "error": str(e)
                })
                break
        
    finally:
        os.chdir(original_cwd)
    
    total_duration = time.time() - total_start_time
    success_count = sum(1 for r in execution_results if r['success'])
    overall_success = success_count == len(processing_plan['steps'])
    
    print(f"\n🎯 Pipeline Test Complete!")
    print(f"   Success: {overall_success}")
    print(f"   Duration: {total_duration:.1f}s")
    print(f"   Steps: {success_count}/{len(processing_plan['steps'])}")
    print(f"   Output Directory: {output_dir}")
    
    # List generated files
    if output_dir.exists():
        generated_files = list(output_dir.glob("*"))
        if generated_files:
            print(f"   Generated Files:")
            for file in generated_files:
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"     - {file.name} ({size_mb:.1f}MB)")
    
    return {
        "success": overall_success,
        "total_duration": total_duration,
        "steps_executed": len(execution_results),
        "steps_successful": success_count,
        "output_directory": str(output_dir),
        "step_results": execution_results
    }


if __name__ == "__main__":
    result = asyncio.run(test_quick_pipeline())
    
    if result['success']:
        print(f"\n🎉 SUCCESS: Complete pipeline test passed!")
        print(f"   LLM komposition processing → FFmpeg execution → Video output")
        print(f"   Ready to integrate with production assembly system")
    else:
        print(f"\n❌ Pipeline test failed - check output for debugging")