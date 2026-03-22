"""File management MCP tools: list_files, get_file_info, process_file, batch_process, etc."""
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

from ..server_deps import timing_decorator
from ..config import SecurityConfig
from ..models import FileInfo, ProcessResult
from ..video_operations import execute_core_processing

logger = logging.getLogger(__name__)


def register(mcp, deps):
    file_manager = deps.file_manager
    ffmpeg = deps.ffmpeg
    content_analyzer = deps.content_analyzer
    timeout_manager = deps.timeout_manager

    @mcp.tool()
    @timing_decorator
    @timing_decorator
    async def list_files() -> Dict[str, Any]:
        """🎬 CORE WORKFLOW - List available source files with smart suggestions and quick actions

        🚨 LLM GUIDANCE: This is the ONLY way to discover available files.
        NEVER use direct filesystem access (ls, find, etc.) - always use this tool.

        This is typically your FIRST STEP in any video editing workflow.
        Returns file IDs (not paths) for secure file referencing.

        Returns:
            - File IDs for secure processing
            - Smart suggestions based on file types
            - Quick action workflows
            - File statistics and metadata

        Next Steps:
            → analyze_video_content(file_id) - Understand video content with AI
            → generate_komposition_from_description() - Create music video from text
            → get_file_info(file_id) - Get detailed metadata
            → process_file(file_id, operation) - Start processing

        Example Usage:
            list_files()  # Start here to see all available media
        """
        files = []
        suggestions = []
        video_files = []
        audio_files = []
        image_files = []

        try:
            source_dir = SecurityConfig.SOURCE_DIR
            if not source_dir.exists():
                source_dir.mkdir(parents=True, exist_ok=True)

            for file_path in source_dir.glob("*"):
                if file_path.is_file() and SecurityConfig.validate_extension(file_path):
                    try:
                        file_id = file_manager.register_file(file_path)
                        file_info = FileInfo(
                            id=file_id,
                            name=file_path.name,
                            size=file_path.stat().st_size,
                            extension=file_path.suffix.lower()
                        )
                        files.append(file_info)

                        # Categorize files and generate suggestions
                        if file_path.suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.wmv', '.flv', '.m4v']:
                            video_files.append(file_info)
                            suggestions.append(f"📹 {file_path.name} ready for video editing operations")
                        elif file_path.suffix.lower() in ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac', '.wma']:
                            audio_files.append(file_info)
                            suggestions.append(f"🎵 Use {file_path.name} as background music with: replace_audio operation, params='audio_file={file_id}'")
                        elif file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']:
                            image_files.append(file_info)
                            suggestions.append(f"🖼️ Convert {file_path.name} to video: image_to_video operation, params='duration=2' (or any duration in seconds)")
                    except Exception:
                        continue

            # Generate workflow suggestions
            quick_actions = []
            if len(video_files) >= 2:
                quick_actions.append("🎬 Create montage: 1) trim multiple videos 2) concatenate_simple 3) replace_audio with music")
            if len(video_files) >= 1 and len(audio_files) >= 1:
                quick_actions.append("🎵 Add background music: use replace_audio operation with any audio file")
            if len(video_files) >= 1:
                quick_actions.append("✂️ Extract highlights: use trim operation to get best moments")
            if len(image_files) >= 1:
                quick_actions.append("🖼️ Create image videos: use image_to_video to convert images to video clips")
            if len(image_files) >= 1 and len(video_files) >= 1:
                quick_actions.append("🎞️ Mixed media montage: convert images to video clips, then concatenate with videos")

            if not suggestions:
                suggestions.append("✅ All files look ready for processing!")

            # Enhanced workflow-specific next steps
            what_next_suggestions = []
            if len(video_files) >= 1:
                what_next_suggestions.extend([
                    "🧠 Understand content: analyze_video_content(file_id) → AI-powered scene detection",
                    "🎬 Start editing: get_file_info(file_id) → process_file(file_id, 'operation')",
                    "✂️ Smart trimming: smart_trim_suggestions(file_id) → intelligent content-based cuts"
                ])

            if len(audio_files) >= 1 and len(video_files) >= 1:
                what_next_suggestions.append("🎵 Create music video: generate_komposition_from_description('your idea here')")

            if len(video_files) >= 2:
                what_next_suggestions.append("🔗 Complex workflow: batch_process([operations]) → multi-step processing")

            # Check for existing manifests
            temp_dir = Path("/tmp/music/temp")
            if (temp_dir / "AUDIO_TIMING_MANIFEST.json").exists():
                what_next_suggestions.append("🎵 Use audio manifest: build_video_from_audio_manifest() → direct manifest execution")

            what_next_suggestions.extend([
                "📁 Track outputs: list_generated_files() → see all processed videos",
                "🧹 Clean workspace: cleanup_temp_files() → remove temporary files"
            ])

        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}", "files": [], "suggestions": [], "quick_actions": []}

        return {
            "files": files,
            "suggestions": suggestions,
            "quick_actions": quick_actions,
            "what_next_suggestions": what_next_suggestions,
            "stats": {
                "total_files": len(files),
                "videos": len(video_files),
                "audio": len(audio_files),
                "images": len(image_files)
            }
        }


    @mcp.tool()
    @timing_decorator
    async def get_file_info(file_id: str) -> Dict[str, Any]:
        """📋 FILE INFO - Get detailed metadata for a file by ID

        🚨 LLM GUIDANCE: Use file IDs from list_files(), NEVER file paths.
        Example: get_file_info("src_video_abc123") not get_file_info("/path/to/video.mp4")

        Returns comprehensive metadata including duration, resolution, format, and processing history.
        """
        file_path = file_manager.resolve_id(file_id)

        if not file_path:
            return {"error": f"File ID '{file_id}' not found"}

        if not file_path.exists():
            return {"error": f"File no longer exists: {file_path.name}"}

        # Get basic file info
        basic_info = {
            "id": file_id,
            "name": file_path.name,
            "size": file_path.stat().st_size,
            "extension": file_path.suffix.lower()
        }

        # Get detailed media info using ffprobe with caching
        media_info = await ffmpeg.get_file_info(file_path, file_manager, file_id)

        return {
            "basic_info": basic_info,
            "media_info": media_info
        }


    @mcp.tool()
    @timing_decorator
    async def get_available_operations() -> Dict[str, Dict[str, str]]:
        """Get list of available FFMPEG operations"""
        operations = ffmpeg.get_available_operations()
        return {"operations": operations}

    @mcp.tool()
    @timing_decorator
    async def get_available_transitions() -> Dict[str, Any]:
        """Get catalog of available video transition effects with parameters and examples"""

        transitions = {
            "crossfade_transition": {
                "name": "Crossfade Transition",
                "description": "Classic dissolve transition between two clips",
                "category": "fade",
                "performance": "fast",
                "parameters": [
                    {
                        "name": "duration_beats",
                        "type": "float",
                        "min": 0.5,
                        "max": 8.0,
                        "default": 2.0,
                        "description": "Length of transition in beats"
                    },
                    {
                        "name": "start_offset_beats",
                        "type": "float",
                        "min": -4.0,
                        "max": 4.0,
                        "default": -1.0,
                        "description": "When to start transition (negative = overlap)"
                    }
                ],
                "example": {
                    "effect_id": "crossfade_demo",
                    "type": "crossfade_transition",
                    "parameters": {
                        "duration_beats": 2,
                        "start_offset_beats": -1
                    },
                    "applies_to": [
                        {"type": "segment", "id": "clip1"},
                        {"type": "segment", "id": "clip2"}
                    ]
                }
            },
            "gradient_wipe": {
                "name": "Gradient Wipe",
                "description": "Directional wipe transition (right-to-left)",
                "category": "wipe",
                "performance": "fast",
                "parameters": [
                    {
                        "name": "duration_beats",
                        "type": "float",
                        "min": 0.5,
                        "max": 8.0,
                        "default": 2.0,
                        "description": "Length of wipe in beats"
                    },
                    {
                        "name": "start_offset_beats",
                        "type": "float",
                        "min": -4.0,
                        "max": 4.0,
                        "default": -1.0,
                        "description": "Wipe start timing offset"
                    }
                ],
                "example": {
                    "effect_id": "wipe_demo",
                    "type": "gradient_wipe",
                    "parameters": {
                        "duration_beats": 1.5,
                        "start_offset_beats": -0.5
                    },
                    "applies_to": [
                        {"type": "segment", "id": "clip1"},
                        {"type": "segment", "id": "clip2"}
                    ]
                }
            },
            "opacity_transition": {
                "name": "Opacity Transition",
                "description": "Alpha-blended overlay transition",
                "category": "overlay",
                "performance": "medium",
                "parameters": [
                    {
                        "name": "opacity",
                        "type": "float",
                        "min": 0.0,
                        "max": 1.0,
                        "default": 0.5,
                        "description": "Transparency level (0=transparent, 1=opaque)"
                    }
                ],
                "example": {
                    "effect_id": "opacity_demo",
                    "type": "opacity_transition",
                    "parameters": {
                        "opacity": 0.7
                    },
                    "applies_to": [
                        {"type": "segment", "id": "clip1"},
                        {"type": "segment", "id": "clip2"}
                    ]
                }
            }
        }

        # Add new xfade transition types
        xfade_transitions = {
            "wipe_left": {
                "name": "Wipe Left",
                "description": "Left-to-right wipe transition",
                "category": "wipe",
                "performance": "fast"
            },
            "wipe_up": {
                "name": "Wipe Up",
                "description": "Bottom-to-top wipe transition",
                "category": "wipe",
                "performance": "fast"
            },
            "wipe_down": {
                "name": "Wipe Down",
                "description": "Top-to-bottom wipe transition",
                "category": "wipe",
                "performance": "fast"
            },
            "slide_left": {
                "name": "Slide Left",
                "description": "Slide transition moving left",
                "category": "slide",
                "performance": "fast"
            },
            "slide_right": {
                "name": "Slide Right",
                "description": "Slide transition moving right",
                "category": "slide",
                "performance": "fast"
            },
            "slide_up": {
                "name": "Slide Up",
                "description": "Slide transition moving up",
                "category": "slide",
                "performance": "fast"
            },
            "slide_down": {
                "name": "Slide Down",
                "description": "Slide transition moving down",
                "category": "slide",
                "performance": "fast"
            },
            "circle_crop": {
                "name": "Circle Crop",
                "description": "Circular crop reveal transition",
                "category": "crop",
                "performance": "fast"
            },
            "fade_black": {
                "name": "Fade Black",
                "description": "Fade through black transition",
                "category": "fade",
                "performance": "fast"
            },
            "fade_white": {
                "name": "Fade White",
                "description": "Fade through white transition",
                "category": "fade",
                "performance": "fast"
            }
        }

        # Add standard parameters for all xfade transitions
        standard_xfade_params = [
            {
                "name": "duration_beats",
                "type": "float",
                "min": 0.5,
                "max": 8.0,
                "default": 2.0,
                "description": "Length of transition in beats"
            },
            {
                "name": "start_offset_beats",
                "type": "float",
                "min": -4.0,
                "max": 4.0,
                "default": -1.0,
                "description": "When to start transition (negative = overlap)"
            }
        ]

        # Add xfade transitions to catalog
        for transition_id, transition_info in xfade_transitions.items():
            transitions[transition_id] = {
                **transition_info,
                "parameters": standard_xfade_params,
                "example": {
                    "effect_id": f"{transition_id}_demo",
                    "type": transition_id,
                    "parameters": {
                        "duration_beats": 1.5,
                        "start_offset_beats": -0.5
                    },
                    "applies_to": [
                        {"type": "segment", "id": "clip1"},
                        {"type": "segment", "id": "clip2"}
                    ]
                }
            }

        return {
            "transitions": transitions,
            "total_count": len(transitions),
            "categories": ["fade", "wipe", "overlay", "slide", "crop"],
            "performance_tiers": ["fast", "medium", "slow"],
            "schema_version": "1.1",
            "usage_notes": [
                "Use effects_tree structure in komposition JSON",
                "duration_beats calculated as: beats / (bpm/60)",
                "Negative start_offset_beats creates overlap between clips",
                "All transitions require exactly 2 clips in applies_to array",
                "New in v1.1: Added 10 additional xfade transition types"
            ]
        }


    @mcp.tool()
    @timing_decorator
    async def process_file(
        input_file_id: str,
        operation: str,  # Available: convert, extract_audio, trim, resize, normalize_audio, to_mp3, replace_audio, concatenate_simple, image_to_video, reverse
        output_extension: str = "mp4",  # Common: mp4, mp3, wav, mov, avi
        params: str = ""  # This is params_str for execute_core_processing
    ) -> ProcessResult:
        """🎬 CORE WORKFLOW - Process a file using FFMPEG with specified operation

        This is your main processing tool for individual file operations.

        Parameters:
            input_file_id: File ID from list_files()
            operation: Operation name (see get_available_operations())
            output_extension: Output format (mp4, mp3, wav, etc.)
            params: Operation-specific parameters as string

        Common Examples:
            → process_file(file_id, "to_mp3", "mp3") - Convert to MP3
            → process_file(file_id, "trim", "mp4", "start=10 duration=5") - Trim 5s from 10s mark
            → process_file(file_id, "resize", "mp4", "width=1920 height=1080") - Resize video
            → process_file(file_id, "extract_audio", "wav") - Extract audio track

        Next Steps:
            → list_generated_files() - See what was created
            → batch_process() - Chain multiple operations
            → get_file_info() - Check output metadata
        """
        # Delegate to the core processing logic in video_operations.py
        # Simple user identification - in production this would come from authentication
        user_id = os.getenv("MCP_USER_ID", "anonymous")

        return await execute_core_processing(
            input_file_id=input_file_id,
            operation=operation,
            output_extension=output_extension,
            params_str=params, # Pass the original 'params' string here
            file_manager=file_manager, # Pass the global instance
            ffmpeg=ffmpeg,             # Pass the global instance
            user_id=user_id
        )


    @mcp.tool()
    @timing_decorator
    async def analyze_video_content(file_id: str, force_reanalysis: bool = False) -> Dict[str, Any]:
        """Analyze video content to understand scenes, objects, and generate intelligent editing suggestions"""

        # Resolve file path
        file_path = file_manager.resolve_id(file_id)
        if not file_path:
            return {"success": False, "error": f"File ID '{file_id}' not found"}

        if not file_path.exists():
            return {"success": False, "error": f"File no longer exists: {file_path.name}"}

        # Only analyze video files
        if file_path.suffix.lower() not in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            return {"success": False, "error": f"Content analysis only supported for video files"}

        try:
            # Calculate timeout based on file size (5 minutes base + 1 minute per 10MB)
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            timeout_seconds = min(300 + (file_size_mb * 6), 1800)  # Max 30 minutes
            operation_id = f"analyze_content_{file_id}_{int(time.time())}"

            logger.info(f"Starting video analysis with {timeout_seconds:.0f}s timeout (file: {file_size_mb:.1f}MB)")

            # Wrap with timeout protection
            result = await timeout_manager.execute_with_timeout(
                content_analyzer.analyze_video_content(file_path, file_id, force_reanalysis),
                operation_id=operation_id,
                timeout_seconds=timeout_seconds,
                cleanup_callback=lambda: content_analyzer.cleanup_analysis_resources()
            )
            return result

        except TimeoutError as e:
            logger.error(f"Video analysis timed out for {file_id}: {e}")
            return {
                "success": False,
                "error": f"Analysis timed out after {timeout_seconds:.0f} seconds",
                "suggestion": "Try with a smaller video file or increase timeout limits"
            }
        except Exception as e:
            return {"success": False, "error": f"Analysis failed: {str(e)}"}


    @mcp.tool()
    async def get_video_insights(file_id: str) -> Dict[str, Any]:
        """Get cached video content insights and intelligent editing suggestions"""

        # First check if we have cached analysis
        analysis = await content_analyzer.get_cached_analysis(file_id)

        if not analysis:
            return {
                "success": False,
                "error": "No analysis available. Run analyze_video_content first.",
                "suggestion": f"Call analyze_video_content(file_id='{file_id}') to generate insights"
            }

        # Extract useful insights for editing
        insights = {
            "success": True,
            "file_info": analysis.get("file_info", {}),
            "scene_count": analysis.get("total_scenes", 0),
            "total_duration": analysis.get("total_duration", 0),
            "highlights": analysis.get("summary", {}).get("best_scenes_for_highlights", []),
            "editing_suggestions": analysis.get("summary", {}).get("editing_suggestions", []),
            "detected_content": analysis.get("summary", {}).get("detected_objects", []),
            "visual_characteristics": analysis.get("summary", {}).get("common_characteristics", [])
        }

        # Add scene breakdown
        scenes = analysis.get("scenes", [])
        insights["scenes"] = [
            {
                "scene_id": scene["scene_id"],
                "start": scene["start"],
                "end": scene["end"],
                "duration": scene["duration"],
                "objects": scene["objects"],
                "characteristics": scene["characteristics"]
            }
            for scene in scenes
        ]

        return insights


    @mcp.tool()
    @timing_decorator
    async def smart_trim_suggestions(file_id: str, desired_duration: float = 10.0) -> Dict[str, Any]:
        """Get intelligent trim suggestions based on video content analysis"""

        # Get cached analysis
        analysis = await content_analyzer.get_cached_analysis(file_id)

        if not analysis:
            return {
                "success": False,
                "error": "No analysis available. Run analyze_video_content first.",
                "suggestion": f"Call analyze_video_content(file_id='{file_id}') to enable smart trimming"
            }

        try:
            suggestions = content_analyzer.get_smart_trim_suggestions(analysis, desired_duration)

            return {
                "success": True,
                "file_id": file_id,
                "desired_duration": desired_duration,
                "suggestions": suggestions,
                "usage_hint": "Use the start/end times from suggestions with the 'trim' operation"
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to generate suggestions: {str(e)}"}


    @mcp.tool()
    @timing_decorator
    async def get_scene_screenshots(file_id: str) -> Dict[str, Any]:
        """Get scene screenshots with URLs for visual scene selection"""

        # Validate file exists
        file_path = file_manager.resolve_id(file_id)
        if not file_path:
            return {"success": False, "error": f"File ID '{file_id}' not found"}

        # Only work with video files
        if file_path.suffix.lower() not in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            return {"success": False, "error": f"Screenshots only supported for video files"}

        try:
            result = await content_analyzer.get_scene_screenshots(file_id)

            if result["success"]:
                result["usage_hint"] = "Use screenshot URLs to visually select scenes for editing operations"
                result["next_steps"] = [
                    "Use scene start/end times with trim operation",
                    "Reference scenes by scene_id for consistent editing",
                    "Combine multiple scenes using concatenate operations"
                ]

            return result

        except Exception as e:
            return {"success": False, "error": f"Failed to get screenshots: {str(e)}"}


    @mcp.tool()
    @timing_decorator
    async def list_generated_files() -> Dict[str, Any]:
        """📁 GENERATED FILES - List all processed files with metadata

        🚨 LLM GUIDANCE: Use this to find previously generated content in the registry.
        NEVER scan /tmp/music/temp/ directly - trust the registry system.

        Shows files you've created through video processing operations.
        """

        try:
            temp_files = []

            # Scan temp directory for generated files
            for temp_file in SecurityConfig.TEMP_DIR.glob("temp_*.mp4"):
                if temp_file.is_file() and temp_file.stat().st_size > 0:
                    # Register file to get file ID
                    file_id = file_manager.register_file(temp_file)

                    temp_files.append({
                        "file_id": file_id,
                        "name": temp_file.name,
                        "size": temp_file.stat().st_size,
                        "created": temp_file.stat().st_mtime,
                        "extension": temp_file.suffix,
                        "type": "generated_video"
                    })

            # Also scan for generated audio files
            for temp_file in SecurityConfig.TEMP_DIR.glob("temp_*.mp3"):
                if temp_file.is_file() and temp_file.stat().st_size > 0:
                    file_id = file_manager.register_file(temp_file)

                    temp_files.append({
                        "file_id": file_id,
                        "name": temp_file.name,
                        "size": temp_file.stat().st_size,
                        "created": temp_file.stat().st_mtime,
                        "extension": temp_file.suffix,
                        "type": "generated_audio"
                    })

            # Sort by creation time (newest first)
            temp_files.sort(key=lambda x: x["created"], reverse=True)

            return {
                "success": True,
                "generated_files": temp_files,
                "total_count": len(temp_files),
                "usage_hint": "These are files created by video processing operations",
                "next_steps": [
                    "Use file_id with other operations",
                    "Get detailed info with get_file_info(file_id)",
                    "Clean up with cleanup_temp_files()"
                ]
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to list generated files: {str(e)}"}


    @mcp.tool()
    @timing_decorator
    async def batch_process(operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """🔧 WORKFLOW TOOL - Execute multiple video operations in sequence with atomic transaction support

        Perfect for complex workflows that require multiple processing steps.
        Supports operation chaining where output of one becomes input of next.

        Args:
            operations: List of operation dicts with keys:
                - input_file_id: File ID (use "OUTPUT_PREVIOUS" to chain operations)
                - operation: Operation name from get_available_operations()
                - output_extension: Output format (mp4, mp3, wav, etc.)
                - params: Operation-specific parameters
                - output_name: Optional custom output filename

        Common Workflow Examples:
            # Music Video Creation:
            operations = [
                {"input_file_id": "file_123", "operation": "trim", "output_extension": "mp4", "params": "start=0 duration=10"},
                {"input_file_id": "OUTPUT_PREVIOUS", "operation": "resize", "output_extension": "mp4", "params": "width=1080 height=1920"},
                {"input_file_id": "OUTPUT_PREVIOUS", "operation": "replace_audio", "output_extension": "mp4", "params": "audio_file_id=file_456"}
            ]

            # Audio Processing Chain:
            operations = [
                {"input_file_id": "file_789", "operation": "extract_audio", "output_extension": "wav"},
                {"input_file_id": "OUTPUT_PREVIOUS", "operation": "normalize_audio", "output_extension": "wav"}
            ]

        Next Steps:
            → list_generated_files() - See all outputs created
            → get_file_info() - Check final result metadata
            → cleanup_temp_files() - Clean up intermediate files

        Returns:
            Results for each operation with file IDs for chaining
        """

        try:
            results = []
            current_file_id = None

            for i, op in enumerate(operations):
                # Use previous output as input for chaining (if input_file_id is 'OUTPUT_PREVIOUS')
                input_id = op.get('input_file_id')
                if input_id in ['OUTPUT_PREVIOUS', 'CHAIN'] and current_file_id:
                    input_id = current_file_id
                elif input_id in ['OUTPUT_PREVIOUS', 'CHAIN'] and not current_file_id:
                    return {"success": False, "error": f"Operation {i}: Cannot chain - no previous output"}

                operation = op.get('operation')
                output_ext = op.get('output_extension', 'mp4')
                params = op.get('params', '')

                print(f"Batch step {i+1}: {operation} on {input_id}")

                # Execute operation
                result = await process_file(
                    input_file_id=input_id,
                    operation=operation,
                    output_extension=output_ext,
                    params=params
                )

                # Handle result format (both dict and object)
                success = result.success if hasattr(result, 'success') else result.get('success', False)
                message = result.message if hasattr(result, 'message') else result.get('message', 'No message')
                output_id = result.output_file_id if hasattr(result, 'output_file_id') else result.get('output_file_id')

                step_result = {
                    "step": i + 1,
                    "operation": operation,
                    "success": success,
                    "message": message,
                    "output_file_id": output_id,
                    "input_file_id": input_id
                }

                results.append(step_result)

                if success and output_id:
                    current_file_id = output_id  # For chaining
                else:
                    # Stop on first failure
                    return {
                        "success": False,
                        "error": f"Batch failed at step {i+1}: {message}",
                        "completed_steps": results,
                        "final_output": None
                    }

            return {
                "success": True,
                "total_steps": len(operations),
                "completed_steps": results,
                "final_output": current_file_id,
                "usage_hint": "All operations completed successfully. Use final_output file_id for further processing."
            }

        except Exception as e:
            return {"success": False, "error": f"Batch processing failed: {str(e)}"}


    @mcp.tool()
    @timing_decorator
    async def cleanup_temp_files() -> Dict[str, str]:
        """Clean up temporary files"""
        try:
            file_manager.cleanup_temp_files()
            return {"message": "Temporary files cleaned up successfully"}
        except Exception as e:
            return {"error": f"Failed to cleanup temp files: {str(e)}"}


    @mcp.tool()
    @timing_decorator
    async def get_registry_status() -> Dict[str, Any]:
        """📊 REGISTRY STATUS - Get file registry health and statistics

        🚨 LLM GUIDANCE: Use this to check registry health and find orphaned files.
        If you suspect cache misses or missing files, this is your diagnostic tool.

        Returns counts, storage usage, orphaned files, and registry health metrics.
        """
        try:
            # Get source files count
            source_files = await list_files()
            source_count = len(source_files.get("files", []))

            # Get generated files count
            generated_files = await list_generated_files()
            generated_count = len(generated_files.get("temp_files", []))

            # Check for potential issues
            issues = []
            if generated_count > 0 and "temp_files" in generated_files:
                # Check if any files have missing registry entries
                temp_files = generated_files["temp_files"]
                for temp_file in temp_files:
                    if not temp_file.get("file_id"):
                        issues.append(f"Orphaned file detected: {temp_file.get('name', 'unknown')}")

            # Calculate storage estimates
            total_storage = 0
            if "files" in source_files:
                total_storage += sum(f.get("size", 0) for f in source_files["files"])
            if "temp_files" in generated_files:
                total_storage += sum(f.get("size", 0) for f in generated_files["temp_files"])

            return {
                "registry_health": "healthy" if len(issues) == 0 else "issues_detected",
                "source_files_count": source_count,
                "generated_files_count": generated_count,
                "total_storage_bytes": total_storage,
                "total_storage_mb": round(total_storage / (1024 * 1024), 2),
                "issues": issues,
                "recommendations": [
                    "🎬 Use list_files() to discover available content",
                    "📋 Use get_file_info(file_id) for file details",
                    "🔑 Work with file IDs, never direct paths",
                    "🗂️ Trust the registry as single source of truth"
                ]
            }
        except Exception as e:
            return {"error": f"Failed to get registry status: {str(e)}"}
