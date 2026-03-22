"""Komposition generation tools - create compositions from descriptions."""
import asyncio
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..server_deps import timing_decorator

logger = logging.getLogger(__name__)


def register(mcp, deps):
    file_manager = deps.file_manager
    ffmpeg = deps.ffmpeg
    komposition_generator = deps.komposition_generator
    komposition_build_planner = deps.komposition_build_planner
    timeout_manager = deps.timeout_manager

    try:
        from ..timeout_manager import ProcessingTimeEstimator, calculate_operation_timeout
    except ImportError:
        from timeout_manager import ProcessingTimeEstimator, calculate_operation_timeout

    @mcp.tool()
    @timing_decorator
    async def generate_komposition_from_description(
        description: str,
        title: str = "Generated Composition",
        custom_bpm: Optional[int] = None,
        custom_resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate komposition.json from natural language description.

        Args:
            description: Natural language description of desired composition
            title: Title for the generated composition
            custom_bpm: Override BPM
            custom_resolution: Override resolution like "600x800"
        """
        try:
            available_sources = komposition_generator.get_available_sources()

            result = await komposition_generator.generate_from_description(
                description=description,
                title=title,
                available_sources=available_sources
            )

            if not result["success"]:
                return result

            komposition = result["komposition"]

            if custom_bpm:
                komposition["metadata"]["bpm"] = custom_bpm
                total_beats = komposition["metadata"]["totalBeats"]
                komposition["metadata"]["estimatedDuration"] = total_beats * 60 / custom_bpm

            if custom_resolution:
                try:
                    width, height = map(int, custom_resolution.split('x'))
                    komposition["outputSettings"]["resolution"] = f"{width}x{height}"
                    komposition["outputSettings"]["aspectRatio"] = f"{width}:{height}"
                except ValueError:
                    pass

            return result

        except Exception as e:
            return {"success": False, "error": f"Failed to generate komposition from description: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def generate_enhanced_komposition_from_description(
        description: str,
        title: str = "Enhanced Content-Aware Composition",
        use_source_metadata: bool = True
    ) -> Dict[str, Any]:
        """Enhanced workflow - Generate komposition with deep content analysis integration.

        Args:
            description: Natural language description of desired composition
            title: Title for the enhanced composition
            use_source_metadata: Whether to use existing source metadata files
        """
        try:
            try:
                from ..enhanced_komposition_generator import generate_enhanced_komposition_from_description as _gen
            except ImportError:
                from enhanced_komposition_generator import generate_enhanced_komposition_from_description as _gen

            result = await _gen(
                description=description,
                title=title,
                use_source_metadata=use_source_metadata
            )

            if result["success"]:
                result["processing_summary"] = {
                    "description": description,
                    "title": title,
                    "use_source_metadata": use_source_metadata,
                    "enhancement_features": [
                        "AI-powered scene analysis",
                        "Content-aware segment selection",
                        "Visual characteristic mapping",
                        "Source metadata integration",
                        "Musical structure optimization"
                    ]
                }

            return result

        except Exception as e:
            return {"success": False, "error": f"Failed to generate enhanced komposition: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def create_build_plan_from_komposition(
        komposition_file: str,
        render_start_beat: Optional[int] = None,
        render_end_beat: Optional[int] = None,
        output_resolution: str = "1920x1080",
        custom_bpm: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create detailed build plan from komposition.json with beat-precise calculations.

        Args:
            komposition_file: Path to komposition.json file
            render_start_beat: Override start beat
            render_end_beat: Override end beat
            output_resolution: Target resolution like "1920x1080"
            custom_bpm: Override BPM for timing calculations
        """
        try:
            try:
                width, height = map(int, output_resolution.split('x'))
                resolution_tuple = (width, height)
            except ValueError:
                return {"success": False, "error": f"Invalid resolution format: {output_resolution}"}

            result = await komposition_build_planner.create_build_plan(
                komposition_path=komposition_file,
                render_start_beat=render_start_beat,
                render_end_beat=render_end_beat,
                output_resolution=resolution_tuple,
                custom_bpm=custom_bpm
            )

            return result

        except Exception as e:
            return {"success": False, "error": f"Failed to create build plan: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def validate_build_plan_for_bpms(
        build_plan_file: str,
        test_bpms: List[int] = [120, 135, 140, 100]
    ) -> Dict[str, Any]:
        """Validate build plan calculations for multiple BPM values.

        Args:
            build_plan_file: Path to build plan JSON file
            test_bpms: List of BPM values to test
        """
        try:
            plan_path = Path(build_plan_file)
            if not plan_path.is_absolute():
                plan_path = komposition_build_planner.build_cache_dir / build_plan_file

            if not plan_path.exists():
                return {"success": False, "error": f"Build plan file not found: {build_plan_file}"}

            with open(plan_path, 'r') as f:
                build_plan_data = json.load(f)

            from ..komposition_build_planner import BuildPlan, BeatTiming, SnippetExtraction

            beat_timing_data = build_plan_data["beat_timing"]
            beat_timing = BeatTiming(
                bpm=beat_timing_data["bpm"],
                beats_per_measure=beat_timing_data["beats_per_measure"],
                start_beat=beat_timing_data["start_beat"],
                end_beat=beat_timing_data["end_beat"]
            )

            snippet_extractions = []
            for extraction_data in build_plan_data["snippet_extractions"]:
                target_timing = BeatTiming(
                    bpm=extraction_data["target_timing"]["bpm"],
                    start_beat=extraction_data["target_timing"]["start_beat"],
                    end_beat=extraction_data["target_timing"]["end_beat"]
                )
                extraction = SnippetExtraction(
                    id=extraction_data["id"],
                    source_file_id=extraction_data["source_file_id"],
                    source_start=extraction_data["source_start"],
                    source_duration=extraction_data["source_duration"],
                    target_start_beat=extraction_data["target_start_beat"],
                    target_end_beat=extraction_data["target_end_beat"],
                    target_timing=target_timing
                )
                snippet_extractions.append(extraction)

            build_plan = BuildPlan(
                id=build_plan_data["id"],
                title=build_plan_data["title"],
                source_komposition_path=build_plan_data["source_komposition_path"],
                created_at=build_plan_data["created_at"],
                beat_timing=beat_timing,
                render_range=tuple(build_plan_data["render_range"]),
                output_resolution=tuple(build_plan_data["output_resolution"]),
                snippet_extractions=snippet_extractions
            )

            validation_results = komposition_build_planner.validate_build_plan_bpm(build_plan, test_bpms)
            overall_valid = all(result["valid"] for result in validation_results.values())

            error_summary = []
            for bpm, result in validation_results.items():
                if not result["valid"]:
                    error_summary.extend([f"BPM {bpm}: {error}" for error in result["extraction_errors"]])

            return {
                "success": True,
                "validation_results": validation_results,
                "overall_valid": overall_valid,
                "error_summary": error_summary,
                "tested_bpms": test_bpms
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to validate build plan: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def generate_and_build_from_description(
        description: str,
        title: str = "Generated Video",
        render_start_beat: Optional[int] = None,
        render_end_beat: Optional[int] = None,
        output_resolution: str = "1920x1080",
        validate_bpms: List[int] = [120, 135]
    ) -> Dict[str, Any]:
        """Complete workflow: Generate komposition from description and create build plan.

        Args:
            description: Natural language description of desired video
            title: Title for the composition
            render_start_beat: Override render start beat
            render_end_beat: Override render end beat
            output_resolution: Target resolution
            validate_bpms: BPM values to validate
        """
        try:
            komposition_result = await generate_komposition_from_description(
                description=description,
                title=title,
                custom_resolution=output_resolution
            )

            if not komposition_result["success"]:
                return {"success": False, "error": f"Komposition generation failed: {komposition_result.get('error')}"}

            komposition_file = komposition_result["komposition_file"]

            build_plan_result = await create_build_plan_from_komposition(
                komposition_file=komposition_file,
                render_start_beat=render_start_beat,
                render_end_beat=render_end_beat,
                output_resolution=output_resolution
            )

            if not build_plan_result["success"]:
                return {"success": False, "error": f"Build plan creation failed: {build_plan_result.get('error')}"}

            build_plan_file = build_plan_result["build_plan_file"]

            validation_result = await validate_build_plan_for_bpms(
                build_plan_file=build_plan_file,
                test_bpms=validate_bpms
            )

            workflow_summary = {
                "komposition_segments": len(komposition_result["komposition"]["segments"]),
                "komposition_effects": len(komposition_result["komposition"]["effects_tree"]),
                "build_plan_operations": build_plan_result["summary"]["total_operations"],
                "estimated_processing_time": build_plan_result["summary"]["estimated_time"],
                "output_resolution": output_resolution,
                "validation_passed": validation_result.get("overall_valid", False),
                "validated_bpms": validate_bpms
            }

            return {
                "success": True,
                "komposition": komposition_result["komposition"],
                "build_plan": build_plan_result["build_plan"],
                "validation_results": validation_result.get("validation_results", {}),
                "files": {"komposition_file": komposition_file, "build_plan_file": build_plan_file},
                "summary": workflow_summary
            }

        except Exception as e:
            return {"success": False, "error": f"Complete workflow failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def build_video_from_audio_manifest(
        manifest_file: str = "AUDIO_TIMING_MANIFEST.json",
        execution_strategy: str = "ffmpeg_direct"
    ) -> Dict[str, Any]:
        """Build final video directly from audio timing manifest.

        Args:
            manifest_file: Path to AUDIO_TIMING_MANIFEST.json
            execution_strategy: "ffmpeg_direct" for direct ffmpeg
        """
        try:
            manifest_path = None
            if manifest_file == "AUDIO_TIMING_MANIFEST.json":
                temp_dir = Path("/tmp/music/temp")
                manifest_path = temp_dir / manifest_file
                if not manifest_path.exists():
                    metadata_dir = Path("/tmp/music/metadata")
                    manifest_path = metadata_dir / manifest_file
            else:
                manifest_path = Path(manifest_file)

            if not manifest_path.exists():
                return {"success": False, "error": f"Manifest file not found: {manifest_file}"}

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            silent_video = Path(manifest['metadata']['silentVideoFile'])
            background_music = Path(f"/tmp/music/source/{manifest['metadata']['backgroundMusic']}")

            if not silent_video.exists():
                return {"success": False, "error": f"Silent video not found: {silent_video}"}
            if not background_music.exists():
                return {"success": False, "error": f"Background music not found: {background_music}"}

            output_file = Path("/tmp/music/temp") / "FINAL_FROM_AUDIO_MANIFEST.mp4"

            if execution_strategy == "ffmpeg_direct":
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(silent_video),
                    "-i", str(background_music),
                    "-c:v", "copy",
                    "-filter:a", "volume=0.5",
                    "-shortest",
                    str(output_file)
                ]

                result = await ffmpeg.execute_command(cmd)

                if result["success"]:
                    output_file_id = file_manager.register_file(output_file)
                    return {
                        "success": True,
                        "message": "Successfully built video from audio manifest",
                        "output_file": str(output_file),
                        "output_file_id": output_file_id,
                        "output_size_mb": round(output_file.stat().st_size / (1024*1024), 1),
                        "manifest_processed": str(manifest_path),
                        "execution_strategy": execution_strategy
                    }
                else:
                    return {"success": False, "error": f"FFmpeg execution failed: {result.get('stderr', 'Unknown error')}"}
            else:
                return {"success": False, "error": "mcp_batch strategy not yet implemented - use ffmpeg_direct"}

        except Exception as e:
            return {"success": False, "error": f"Failed to build video from audio manifest: {str(e)}"}

    async def _internal_create_video_from_description(
        description, title, execution_mode, quality, custom_bpm, custom_resolution
    ):
        """Internal implementation of video creation without timeout wrapper"""
        mcp_instance = deps.mcp_instance
        workflow_start = asyncio.get_event_loop().time()
        workflow_results = {
            "success": True, "workflow_steps": [], "files_created": [],
            "processing_summary": {}, "total_time": 0
        }

        try:
            # Step 1: File discovery
            step_start = asyncio.get_event_loop().time()
            files_result = await mcp_instance.call_tool('list_files', {})
            files_text = files_result[0].text if files_result and len(files_result) > 0 else '{}'
            files_data = json.loads(files_text)
            workflow_results["workflow_steps"].append({
                "step": "file_discovery",
                "duration": asyncio.get_event_loop().time() - step_start,
                "files_found": len(files_data.get("files", [])),
                "status": "completed"
            })

            # Step 2: Komposition generation
            step_start = asyncio.get_event_loop().time()
            komposition_result = await mcp_instance.call_tool('generate_komposition_from_description', {
                'description': description, 'title': title,
                'custom_bpm': custom_bpm, 'custom_resolution': custom_resolution
            })
            komposition_text = komposition_result[0].text if komposition_result and len(komposition_result) > 0 else '{}'
            komposition_data = json.loads(komposition_text)

            if not komposition_data.get('success'):
                return {"success": False, "error": f"Komposition generation failed: {komposition_data.get('error')}", "workflow_results": workflow_results}

            komposition_file = komposition_data.get('komposition_file', '')
            workflow_results["files_created"].append(komposition_file)
            workflow_results["workflow_steps"].append({
                "step": "komposition_generation",
                "duration": asyncio.get_event_loop().time() - step_start,
                "komposition_file": komposition_file,
                "status": "completed"
            })

            # Step 3: Build plan
            step_start = asyncio.get_event_loop().time()
            build_plan_result = await mcp_instance.call_tool('create_build_plan_from_komposition', {'komposition_file': komposition_file})
            build_plan_text = build_plan_result[0].text if build_plan_result and len(build_plan_result) > 0 else '{}'
            build_plan_data = json.loads(build_plan_text)

            if not build_plan_data.get('success'):
                return {"success": False, "error": f"Build plan creation failed: {build_plan_data.get('error')}", "workflow_results": workflow_results}

            build_plan_file = build_plan_data.get('build_plan_file', '')
            workflow_results["files_created"].append(build_plan_file)
            workflow_results["workflow_steps"].append({
                "step": "build_plan_creation",
                "duration": asyncio.get_event_loop().time() - step_start,
                "build_plan_file": build_plan_file,
                "status": "completed"
            })

            # Step 4: Validation
            step_start = asyncio.get_event_loop().time()
            validation_result = await mcp_instance.call_tool('validate_build_plan_for_bpms', {
                'build_plan_file': build_plan_file, 'test_bpms': [120, 134, 140]
            })
            validation_text = validation_result[0].text if validation_result and len(validation_result) > 0 else '{}'
            validation_data = json.loads(validation_text)
            workflow_results["workflow_steps"].append({
                "step": "validation",
                "duration": asyncio.get_event_loop().time() - step_start,
                "validation_passed": validation_data.get("overall_valid", False),
                "status": "completed"
            })

            # Step 5: Conditional execution
            if execution_mode == "full":
                step_start = asyncio.get_event_loop().time()
                processing_result = await mcp_instance.call_tool('process_komposition_file', {'komposition_path': komposition_file})
                processing_text = processing_result[0].text if processing_result and len(processing_result) > 0 else '{}'
                processing_data = json.loads(processing_text)
                workflow_results["workflow_steps"].append({
                    "step": "video_processing",
                    "duration": asyncio.get_event_loop().time() - step_start,
                    "status": "completed" if processing_data.get("success") else "failed"
                })
                if not processing_data.get("success"):
                    workflow_results["success"] = False
            elif execution_mode == "plan_only":
                workflow_results["workflow_steps"].append({"step": "video_processing", "status": "skipped", "reason": "plan_only mode"})

            workflow_results["total_time"] = asyncio.get_event_loop().time() - workflow_start
            workflow_results["processing_summary"] = {
                "description": description, "title": title,
                "execution_mode": execution_mode, "quality": quality,
                "total_steps": len(workflow_results["workflow_steps"]),
                "total_files_created": len(workflow_results["files_created"]),
                "total_processing_time": workflow_results["total_time"]
            }

            return workflow_results

        except Exception as e:
            return {"success": False, "error": f"Atomic video creation failed: {str(e)}", "workflow_results": workflow_results}

    @mcp.tool()
    @timing_decorator
    async def create_video_from_description(
        description: str,
        title: str = "Generated Video",
        execution_mode: str = "full",
        quality: str = "standard",
        custom_bpm: Optional[int] = None,
        custom_resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """Atomic video creation - Complete video from text description in single call.

        Args:
            description: Natural language description of desired video
            title: Video title
            execution_mode: "full", "plan_only", or "preview"
            quality: "draft", "standard", or "high"
            custom_bpm: Override detected BPM
            custom_resolution: Override resolution
        """
        try:
            timeout_seconds = calculate_operation_timeout(
                description, execution_mode=execution_mode,
                quality=quality, custom_resolution=custom_resolution
            )

            operation_id = f"video_creation_{int(time.time())}_{hashlib.md5(description.encode()).hexdigest()[:8]}"

            async def cleanup():
                try:
                    await deps.mcp_instance.call_tool('cleanup_temp_files', {})
                except Exception:
                    pass

            result = await timeout_manager.execute_with_timeout(
                _internal_create_video_from_description(
                    description, title, execution_mode, quality, custom_bpm, custom_resolution
                ),
                operation_id, timeout_seconds, cleanup
            )

            if isinstance(result, dict):
                result["timeout_info"] = {
                    "estimated_time": timeout_seconds / 1.5,
                    "actual_timeout": timeout_seconds,
                    "operation_id": operation_id
                }

            return result

        except TimeoutError as e:
            return {
                "success": False, "error": str(e), "error_type": "timeout",
                "recommendation": "Try with a simpler description, lower quality, or plan_only mode"
            }
        except Exception as e:
            return {"success": False, "error": f"Video creation failed: {str(e)}", "error_type": "general"}
