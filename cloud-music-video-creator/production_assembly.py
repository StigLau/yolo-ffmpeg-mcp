#!/usr/bin/env python3
"""
Production Assembly: Bill of Materials Processing

Final step that combines all video segments, audio, and effects into final production video.
This is the most likely candidate for Python scripting since it's repetitive and predictable.
"""

import asyncio
import json
import subprocess
import time
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class MediaAsset:
    """Represents a media file in the bill of materials"""
    id: str
    path: str
    type: str  # video, audio, image
    metadata: Dict[str, Any]
    
@dataclass  
class ProcessingStep:
    """Represents a processing step in the production pipeline"""
    step_id: int
    name: str
    operation: str
    inputs: List[str]
    outputs: List[str]
    parameters: Dict[str, Any]
    estimated_duration: float
    
@dataclass
class BillOfMaterials:
    """Complete bill of materials for video production"""
    production_id: str
    title: str
    total_duration: float
    target_resolution: str
    target_fps: int
    
    # Assets
    video_assets: List[MediaAsset]
    audio_assets: List[MediaAsset] 
    
    # Processing pipeline
    processing_steps: List[ProcessingStep]
    
    # Output specification
    final_output: str
    quality_settings: Dict[str, Any]

class ProductionAssembler:
    """Production-ready assembly engine for music video creation"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or "/tmp/music-video-creator/production")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def process_bill_of_materials(self, bom: BillOfMaterials) -> Dict[str, Any]:
        """Process complete bill of materials into final video"""
        
        print(f"🎬 Processing Production: {bom.title}")
        print(f"   Production ID: {bom.production_id}")
        print(f"   Duration: {bom.total_duration}s")
        print(f"   Assets: {len(bom.video_assets)} video, {len(bom.audio_assets)} audio")
        print(f"   Steps: {len(bom.processing_steps)} processing steps")
        
        # Create production directory
        production_dir = self.output_dir / bom.production_id
        production_dir.mkdir(exist_ok=True)
        
        # Validate all input assets exist
        validation_result = await self._validate_assets(bom)
        if not validation_result['valid']:
            return {
                "success": False,
                "error": f"Asset validation failed: {validation_result['errors']}"
            }
        
        # Execute processing pipeline
        pipeline_result = await self._execute_pipeline(bom, production_dir)
        
        # Final quality check
        if pipeline_result['success']:
            quality_result = await self._quality_check(production_dir / bom.final_output)
            pipeline_result['quality_check'] = quality_result
        
        return pipeline_result
    
    async def _validate_assets(self, bom: BillOfMaterials) -> Dict[str, Any]:
        """Validate all required assets exist and are accessible"""
        
        print("🔍 Validating assets...")
        
        errors = []
        all_assets = bom.video_assets + bom.audio_assets
        
        for asset in all_assets:
            asset_path = Path(asset.path)
            if not asset_path.exists():
                errors.append(f"Missing asset: {asset.id} at {asset.path}")
            elif not asset_path.is_file():
                errors.append(f"Asset is not a file: {asset.id} at {asset.path}")
            else:
                # Quick media validation
                try:
                    cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', 
                           '-show_entries', 'stream=duration', '-of', 'csv=p=0', str(asset_path)]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode != 0 and asset.type == 'video':
                        errors.append(f"Invalid video file: {asset.id}")
                        
                except Exception as e:
                    errors.append(f"Asset validation error {asset.id}: {e}")
        
        if errors:
            print(f"❌ Asset validation failed: {len(errors)} errors")
            for error in errors:
                print(f"   • {error}")
        else:
            print(f"✅ All {len(all_assets)} assets validated")
            
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "assets_checked": len(all_assets)
        }
    
    async def _execute_pipeline(self, bom: BillOfMaterials, production_dir: Path) -> Dict[str, Any]:
        """Execute the complete processing pipeline"""
        
        print(f"🎬 Executing production pipeline...")
        
        start_time = time.time()
        step_results = []
        
        # Change to production directory
        original_cwd = Path.cwd()
        os.chdir(production_dir)
        
        try:
            for step in bom.processing_steps:
                step_result = await self._execute_production_step(step, bom)
                step_results.append(step_result)
                
                if not step_result['success']:
                    print(f"❌ Pipeline failed at step {step.step_id}: {step.name}")
                    break
                    
                print(f"✅ Step {step.step_id} completed: {step.name} ({step_result['duration']:.1f}s)")
        
        finally:
            os.chdir(original_cwd)
        
        total_duration = time.time() - start_time
        successful_steps = sum(1 for r in step_results if r['success'])
        
        return {
            "success": successful_steps == len(bom.processing_steps),
            "total_duration": total_duration,
            "steps_executed": len(step_results),
            "steps_successful": successful_steps,
            "step_results": step_results,
            "final_output": str(production_dir / bom.final_output) if successful_steps == len(bom.processing_steps) else None
        }
    
    async def _execute_production_step(self, step: ProcessingStep, bom: BillOfMaterials) -> Dict[str, Any]:
        """Execute a single production step"""
        
        step_start = time.time()
        
        # Generate command based on operation type
        if step.operation == "audio_processing":
            command = self._generate_audio_command(step, bom)
        elif step.operation == "segment_extraction": 
            command = self._generate_segment_commands(step, bom)
        elif step.operation == "concatenation":
            command = self._generate_concat_command(step, bom)
        elif step.operation == "final_assembly":
            command = self._generate_assembly_command(step, bom)
        else:
            return {
                "success": False,
                "duration": time.time() - step_start,
                "error": f"Unknown operation: {step.operation}"
            }
        
        # Execute command(s)
        if isinstance(command, list):
            # Multiple commands for segment processing
            results = []
            for cmd in command:
                result = await self._run_ffmpeg_command(cmd)
                results.append(result)
                if not result['success']:
                    break
            
            overall_success = all(r['success'] for r in results)
            return {
                "success": overall_success,
                "duration": time.time() - step_start,
                "commands_executed": len(results),
                "command_results": results
            }
        else:
            # Single command
            result = await self._run_ffmpeg_command(command)
            return {
                "success": result['success'],
                "duration": time.time() - step_start,
                "command": command,
                "output": result.get('output', ''),
                "error": result.get('error', '')
            }
    
    def _generate_audio_command(self, step: ProcessingStep, bom: BillOfMaterials) -> str:
        """Generate audio processing command"""
        
        audio_asset = bom.audio_assets[0]  # Assume first audio asset
        output_file = step.outputs[0]
        
        # Extract parameters
        target_bpm = step.parameters.get('target_bpm', 80)
        duration = step.parameters.get('duration', bom.total_duration)
        volume = step.parameters.get('volume', 0.75)
        
        # Calculate tempo adjustment (assuming original is ~100-120 BPM)
        tempo_ratio = target_bpm / step.parameters.get('original_bpm', 100)
        
        return f"""ffmpeg -i "{audio_asset.path}" \
-filter_complex "[0:a]atempo={tempo_ratio:.2f},volume={volume},afade=t=in:st=0:d=1,afade=t=out:st={duration-2}:d=2[audio_out]" \
-map "[audio_out]" -c:a aac -b:a 128k -ar 44100 -t {duration} "{output_file}\""""
    
    def _generate_segment_commands(self, step: ProcessingStep, bom: BillOfMaterials) -> List[str]:
        """Generate segment extraction commands"""
        
        commands = []
        segments = step.parameters.get('segments', [])
        
        for i, segment_info in enumerate(segments, 1):
            video_asset = next(a for a in bom.video_assets if a.id == segment_info['source_id'])
            output_file = f"segment_{i:02d}_{segment_info['filter_group']}.mp4"
            
            # Build filter chain
            filters = []
            
            # Standard scaling and padding
            filters.append("scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1:black")
            
            # Add specific filters based on group
            if segment_info['filter_group'] == 'noir':
                filters.append("eq=contrast=1.5:brightness=-0.1:saturation=0.3,curves=all='0/0.1 0.5/0.4 1/0.9'")
            elif segment_info['filter_group'] == 'vintage':
                filters.append("colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=15:allf=t,vignette=PI/8")
            elif segment_info['filter_group'] == 'dreamy':
                filters.append("gblur=sigma=2.5:steps=1,eq=brightness=0.15:saturation=1.1,boxblur=luma_radius=1:luma_power=0.3")
            
            # Add fade transition
            fade_color = segment_info.get('fade_color', 'white')
            fade_start = segment_info.get('duration', 6) - 1
            filters.append(f"fade=t=out:st={fade_start}:d=1:color={fade_color}")
            
            filter_chain = ",".join(filters)
            
            command = f"""ffmpeg -i "{video_asset.path}" \
-ss {segment_info.get('start_time', 0)} -t {segment_info.get('duration', 6)} \
-vf "{filter_chain}" \
-c:v libx264 -preset medium -crf 23 -r 25 -an "{output_file}\""""
            
            commands.append(command)
        
        return commands
    
    def _generate_concat_command(self, step: ProcessingStep, bom: BillOfMaterials) -> str:
        """Generate concatenation command"""
        
        # Create concat file list
        segment_files = step.inputs
        concat_content = "\n".join(f"file '{f}'" for f in segment_files)
        
        with open("segment_list.txt", "w") as f:
            f.write(concat_content)
        
        output_file = step.outputs[0]
        
        return f"""ffmpeg -f concat -safe 0 -i segment_list.txt \
-c copy -avoid_negative_ts make_zero "{output_file}\""""
    
    def _generate_assembly_command(self, step: ProcessingStep, bom: BillOfMaterials) -> str:
        """Generate final assembly command"""
        
        video_file = step.inputs[0]  # Video-only file
        audio_file = step.inputs[1]  # Processed audio
        output_file = step.outputs[0]  # Final output
        
        return f"""ffmpeg -i "{video_file}" -i "{audio_file}" \
-c:v copy -c:a copy -shortest -movflags +faststart "{output_file}\""""
    
    async def _run_ffmpeg_command(self, command: str) -> Dict[str, Any]:
        """Execute FFmpeg command with error handling"""
        
        try:
            # Parse command for subprocess
            import shlex
            cmd_parts = shlex.split(command)
            
            result = subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else ""
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout (300s)"
            }
        except Exception as e:
            return {
                "success": False, 
                "error": str(e)
            }
    
    async def _quality_check(self, output_file: Path) -> Dict[str, Any]:
        """Perform quality check on final output"""
        
        if not output_file.exists():
            return {
                "passed": False,
                "error": "Output file does not exist"
            }
        
        try:
            # Check basic video properties
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', 
                   '-show_format', '-show_streams', str(output_file)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {
                    "passed": False,
                    "error": "FFprobe analysis failed"
                }
            
            probe_data = json.loads(result.stdout)
            
            # Extract quality metrics
            video_stream = next((s for s in probe_data['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in probe_data['streams'] if s['codec_type'] == 'audio'), None)
            
            quality_check = {
                "passed": True,
                "duration": float(probe_data['format']['duration']),
                "file_size_mb": float(probe_data['format']['size']) / (1024*1024),
                "has_video": video_stream is not None,
                "has_audio": audio_stream is not None
            }
            
            if video_stream:
                quality_check.update({
                    "resolution": f"{video_stream['width']}x{video_stream['height']}",
                    "frame_rate": video_stream.get('r_frame_rate', 'unknown'),
                    "video_codec": video_stream['codec_name']
                })
            
            if audio_stream:
                quality_check.update({
                    "audio_codec": audio_stream['codec_name'],
                    "sample_rate": audio_stream.get('sample_rate', 'unknown')
                })
            
            return quality_check
            
        except Exception as e:
            return {
                "passed": False,
                "error": f"Quality check failed: {e}"
            }

# Example usage and testing
def create_subnautic_bom() -> BillOfMaterials:
    """Create bill of materials for the Subnautic 9-segment video"""
    
    return BillOfMaterials(
        production_id="subnautic_9seg_production",
        title="Subnautic 9-Segment Music Video",
        total_duration=54.0,
        target_resolution="1920x1080", 
        target_fps=25,
        
        video_assets=[
            MediaAsset(
                id="video1",
                path="../.testdata/JJVtt947FfI_136.mp4",
                type="video",
                metadata={"usage": "segments 1,3,5,7,9"}
            ),
            MediaAsset(
                id="video2", 
                path="../.testdata/_wZ5Hof5tXY_136.mp4",
                type="video",
                metadata={"usage": "segments 2,4,6,8"}
            )
        ],
        
        audio_assets=[
            MediaAsset(
                id="audio1",
                path="../.testdata/Subnautic Measures.flac", 
                type="audio",
                metadata={"original_bpm": 100, "target_bpm": 80}
            )
        ],
        
        processing_steps=[
            ProcessingStep(
                step_id=1,
                name="audio_processing",
                operation="audio_processing",
                inputs=["audio1"],
                outputs=["subnautic_audio_80bpm.aac"],
                parameters={"target_bpm": 80, "duration": 54.0, "volume": 0.75, "original_bpm": 100},
                estimated_duration=10.0
            ),
            ProcessingStep(
                step_id=2,
                name="segment_extraction",
                operation="segment_extraction", 
                inputs=["video1", "video2"],
                outputs=[f"segment_{i:02d}.mp4" for i in range(1, 10)],
                parameters={
                    "segments": [
                        {"source_id": "video1", "start_time": 10, "duration": 6, "filter_group": "noir", "fade_color": "white"},
                        {"source_id": "video2", "start_time": 5, "duration": 6, "filter_group": "noir", "fade_color": "white"},
                        {"source_id": "video1", "start_time": 25, "duration": 6, "filter_group": "noir", "fade_color": "white"},
                        {"source_id": "video2", "start_time": 15, "duration": 6, "filter_group": "vintage", "fade_color": "white"}, 
                        {"source_id": "video1", "start_time": 40, "duration": 6, "filter_group": "vintage", "fade_color": "white"},
                        {"source_id": "video2", "start_time": 30, "duration": 6, "filter_group": "vintage", "fade_color": "black"},
                        {"source_id": "video1", "start_time": 60, "duration": 6, "filter_group": "dreamy", "fade_color": "black"},
                        {"source_id": "video2", "start_time": 50, "duration": 6, "filter_group": "dreamy", "fade_color": "black"},
                        {"source_id": "video1", "start_time": 80, "duration": 6, "filter_group": "dreamy", "fade_color": "black"}
                    ]
                },
                estimated_duration=90.0
            ),
            ProcessingStep(
                step_id=3,
                name="concatenation",
                operation="concatenation",
                inputs=[f"segment_{i:02d}.mp4" for i in range(1, 10)],
                outputs=["subnautic_video_only.mp4"],
                parameters={},
                estimated_duration=5.0
            ),
            ProcessingStep(
                step_id=4,
                name="final_assembly",
                operation="final_assembly",
                inputs=["subnautic_video_only.mp4", "subnautic_audio_80bpm.aac"],
                outputs=["subnautic_9segments_final.mp4"],
                parameters={},
                estimated_duration=5.0
            )
        ],
        
        final_output="subnautic_9segments_final.mp4",
        quality_settings={
            "video_codec": "libx264",
            "preset": "medium", 
            "crf": 23,
            "audio_codec": "aac",
            "audio_bitrate": "128k"
        }
    )

async def test_production_assembly():
    """Test the production assembly system"""
    
    print("🎬 Testing Production Assembly System")
    print("=" * 50)
    
    # Create bill of materials
    bom = create_subnautic_bom()
    
    # Initialize assembler
    assembler = ProductionAssembler()
    
    # Process bill of materials
    result = await assembler.process_bill_of_materials(bom)
    
    print(f"\n🎯 Production Assembly Results:")
    print(f"   Success: {result['success']}")
    print(f"   Duration: {result.get('total_duration', 0):.1f}s") 
    print(f"   Steps: {result.get('steps_successful', 0)}/{result.get('steps_executed', 0)}")
    
    if result['success']:
        print(f"   Final Output: {result['final_output']}")
        quality = result.get('quality_check', {})
        if quality.get('passed'):
            print(f"   Quality Check: ✅ PASSED")
            print(f"     Duration: {quality.get('duration', 0):.1f}s")
            print(f"     File Size: {quality.get('file_size_mb', 0):.1f}MB")
            print(f"     Resolution: {quality.get('resolution', 'unknown')}")
    
    return result

if __name__ == "__main__":
    import os
    
    result = asyncio.run(test_production_assembly())