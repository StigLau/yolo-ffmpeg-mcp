#!/usr/bin/env python3
"""
LLM-Driven Komposition Processor

Reads komposition.md files and uses LLM to generate FFmpeg processing steps
"""

import asyncio
import json
import subprocess
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

class LLMKompositionProcessor:
    """Processes komposition.md files using LLM for FFmpeg command generation"""
    
    def __init__(self, use_fasttrack: bool = True):
        self.use_fasttrack = use_fasttrack
        self.output_dir = Path("/tmp/music-video-creator/llm-processing")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def process_komposition_md(self, komposition_file: str) -> Dict[str, Any]:
        """Process a komposition.md file through LLM"""
        
        print(f"🎬 Processing komposition file: {komposition_file}")
        
        # Read komposition specification
        komposition_path = Path(komposition_file)
        if not komposition_path.exists():
            raise FileNotFoundError(f"Komposition file not found: {komposition_file}")
            
        with open(komposition_path, 'r') as f:
            komposition_content = f.read()
        
        print(f"✅ Loaded komposition: {len(komposition_content)} characters")
        
        # Generate unique processing ID
        process_id = f"komp_{uuid.uuid4().hex[:8]}"
        process_dir = self.output_dir / process_id
        process_dir.mkdir(exist_ok=True)
        
        # Use LLM to analyze komposition and generate processing plan
        processing_plan = await self._generate_processing_plan(komposition_content, process_id)
        
        # Save processing plan for reference
        plan_file = process_dir / "processing_plan.json"
        with open(plan_file, 'w') as f:
            json.dump(processing_plan, f, indent=2)
        
        print(f"✅ Generated processing plan: {len(processing_plan['steps'])} steps")
        
        # Execute processing plan
        execution_result = await self._execute_processing_plan(processing_plan, process_dir)
        
        return {
            "process_id": process_id,
            "komposition_file": komposition_file,
            "processing_plan": processing_plan,
            "execution_result": execution_result,
            "output_directory": str(process_dir)
        }
    
    async def _generate_processing_plan(self, komposition_content: str, process_id: str) -> Dict[str, Any]:
        """Use LLM to generate processing plan from komposition.md"""
        
        if self.use_fasttrack:
            return await self._use_fasttrack_agent(komposition_content, process_id)
        else:
            return await self._use_direct_llm(komposition_content, process_id)
    
    async def _use_fasttrack_agent(self, komposition_content: str, process_id: str) -> Dict[str, Any]:
        """Use FastTrack agent for processing plan generation"""
        
        from src.services.llm_analysis import LLMAnalysisService
        
        print("🧠 Using FastTrack agent for processing plan generation...")
        
        # Create FastTrack prompt
        fasttrack_prompt = f"""
        Analyze this komposition specification and generate a complete FFmpeg processing plan.
        
        KOMPOSITION CONTENT:
        {komposition_content}
        
        Generate a detailed processing plan with these components:
        
        1. AUDIO_PROCESSING: Commands for audio preparation and BPM adjustment
        2. SEGMENT_PROCESSING: Individual FFmpeg commands for each video segment
        3. CONCATENATION: Commands to combine all segments
        4. FINAL_ASSEMBLY: Commands to add audio and create final output
        5. BILL_OF_MATERIALS: List all input files, intermediate files, and final outputs
        
        Return a JSON structure with:
        - estimated_duration: total processing time estimate
        - estimated_cost: processing cost estimate  
        - steps: array of processing steps with FFmpeg commands
        - inputs: list of required input files
        - outputs: list of generated output files
        
        Focus on practical, working FFmpeg commands that match the komposition exactly.
        """
        
        # Use FastTrack for analysis (would integrate with actual FastTrack agent)
        analysis_service = LLMAnalysisService()
        result = await analysis_service.analyze_komposition(komposition_content, fasttrack_prompt)
        
        # Mock FastTrack response for now (would be actual agent call)
        processing_plan = {
            "process_id": process_id,
            "llm_used": "fasttrack_haiku",
            "estimated_duration": 120.0,  # seconds
            "estimated_cost": 0.05,       # dollars
            "confidence": 0.85,
            "steps": [
                {
                    "step_id": 1,
                    "name": "audio_processing",
                    "description": "Process Subnautic Measures.flac to 80 BPM, 54 seconds",
                    "command": "ffmpeg -i '/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/.testdata/Subnautic Measures.flac' -filter_complex '[0:a]atempo=0.8,volume=0.75,afade=t=in:st=0:d=1,afade=t=out:st=52:d=2[audio_out]' -map '[audio_out]' -c:a aac -b:a 128k -ar 44100 -t 54 subnautic_audio_80bpm.aac"
                },
                {
                    "step_id": 2,
                    "name": "segment_extraction",
                    "description": "Extract and process 9 segments with 3 different filter groups",
                    "commands": [
                        {
                            "segment": 1,
                            "filter_group": "noir", 
                            "command": "ffmpeg -i '../.testdata/JJVtt947FfI_136.mp4' -ss 10 -t 6 -vf 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black,eq=contrast=1.5:brightness=-0.1:saturation=0.3,curves=all=\"0/0.1 0.5/0.4 1/0.9\",fade=t=out:st=5:d=1:color=white' -c:v libx264 -preset medium -crf 23 -r 25 -an segment_01_noir.mp4"
                        }
                        # ... more segments would be generated by actual LLM
                    ]
                },
                {
                    "step_id": 3,
                    "name": "concatenation",
                    "description": "Concatenate all 9 segments in sequence",
                    "command": "ffmpeg -f concat -safe 0 -i segment_list.txt -c copy -avoid_negative_ts make_zero subnautic_video_only.mp4"
                },
                {
                    "step_id": 4,
                    "name": "final_assembly", 
                    "description": "Combine video and audio for final output",
                    "command": "ffmpeg -i subnautic_video_only.mp4 -i subnautic_audio_80bpm.aac -c:v copy -c:a copy -shortest -movflags +faststart subnautic_9segments_final.mp4"
                }
            ],
            "inputs": [
                "../.testdata/JJVtt947FfI_136.mp4",
                "../.testdata/_wZ5Hof5tXY_136.mp4", 
                "../.testdata/Subnautic Measures.flac"
            ],
            "outputs": [
                "subnautic_audio_80bpm.aac",
                "segment_01_noir.mp4",
                "segment_02_noir.mp4",
                "segment_03_noir.mp4",
                "segment_04_vintage.mp4",
                "segment_05_vintage.mp4",
                "segment_06_vintage.mp4",
                "segment_07_dreamy.mp4", 
                "segment_08_dreamy.mp4",
                "segment_09_dreamy.mp4",
                "subnautic_video_only.mp4",
                "subnautic_9segments_final.mp4"
            ]
        }
        
        return processing_plan
    
    async def _use_direct_llm(self, komposition_content: str, process_id: str) -> Dict[str, Any]:
        """Use direct LLM integration for processing plan generation"""
        # Would implement direct Claude/OpenAI integration
        pass
    
    async def _execute_processing_plan(self, plan: Dict[str, Any], process_dir: Path) -> Dict[str, Any]:
        """Execute the generated processing plan"""
        
        print(f"🎬 Executing processing plan with {len(plan['steps'])} steps...")
        
        execution_results = []
        total_start_time = time.time()
        
        # Change to process directory for execution
        import os
        original_cwd = Path.cwd()
        os.chdir(process_dir)
        
        try:
            for step in plan['steps']:
                step_start = time.time()
                print(f"🔄 Step {step['step_id']}: {step['name']}")
                
                if step['name'] == 'segment_extraction':
                    # Handle multiple commands for segment processing
                    segment_results = []
                    for cmd_info in step.get('commands', []):
                        cmd_result = await self._execute_ffmpeg_command(cmd_info['command'])
                        segment_results.append({
                            "segment": cmd_info.get('segment'),
                            "filter_group": cmd_info.get('filter_group'),
                            "success": cmd_result['success'],
                            "duration": cmd_result['duration']
                        })
                    
                    step_result = {
                        "step_id": step['step_id'],
                        "name": step['name'],
                        "success": all(r['success'] for r in segment_results),
                        "duration": time.time() - step_start,
                        "segment_results": segment_results
                    }
                else:
                    # Handle single command steps
                    cmd_result = await self._execute_ffmpeg_command(step['command'])
                    step_result = {
                        "step_id": step['step_id'],
                        "name": step['name'],
                        "success": cmd_result['success'],
                        "duration": time.time() - step_start,
                        "output": cmd_result.get('output', ''),
                        "error": cmd_result.get('error', '')
                    }
                
                execution_results.append(step_result)
                
                if step_result['success']:
                    print(f"  ✅ Completed in {step_result['duration']:.1f}s")
                else:
                    print(f"  ❌ Failed after {step_result['duration']:.1f}s")
                    break
        
        finally:
            os.chdir(original_cwd)
        
        total_duration = time.time() - total_start_time
        success_count = sum(1 for r in execution_results if r['success'])
        
        return {
            "total_duration": total_duration,
            "steps_executed": len(execution_results),
            "steps_successful": success_count, 
            "overall_success": success_count == len(plan['steps']),
            "step_results": execution_results
        }
    
    async def _execute_ffmpeg_command(self, command: str) -> Dict[str, Any]:
        """Execute a single FFmpeg command"""
        
        start_time = time.time()
        
        try:
            # Parse command into list for subprocess
            cmd_parts = command.split()
            
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "duration": duration,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": "Command timed out after 300 seconds"
            }
        except Exception as e:
            return {
                "success": False, 
                "duration": time.time() - start_time,
                "error": str(e)
            }

# Test function
async def test_subnautic_processing():
    """Test processing the Subnautic 9-segment komposition"""
    
    processor = LLMKompositionProcessor(use_fasttrack=True)
    
    komposition_file = "subnautic_9segments_komposition.md"
    
    try:
        result = await processor.process_komposition_md(komposition_file)
        
        print(f"\n🎯 Processing Complete!")
        print(f"   Process ID: {result['process_id']}")
        print(f"   Success: {result['execution_result']['overall_success']}")
        print(f"   Duration: {result['execution_result']['total_duration']:.1f}s")
        print(f"   Steps: {result['execution_result']['steps_successful']}/{result['execution_result']['steps_executed']}")
        print(f"   Output: {result['output_directory']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        return None

if __name__ == "__main__":
    import os
    
    print("🎬 LLM Komposition Processor Test")
    print("=" * 50)
    
    result = asyncio.run(test_subnautic_processing())