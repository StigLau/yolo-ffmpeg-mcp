import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP
# Pydantic BaseModel is now in models.py, but FileInfo and ProcessResult are imported directly
# from pydantic import BaseModel # No longer needed here if all models are imported

try:
    from .file_manager import FileManager
    from .ffmpeg_wrapper import FFMPEGWrapper
    from .config import SecurityConfig
    from .content_analyzer import VideoContentAnalyzer
    from .komposition_processor import KompositionProcessor
    from .transition_processor import TransitionProcessor
    from .speech_detector import SpeechDetector
    from .speech_komposition_processor import SpeechKompositionProcessor
    from .enhanced_speech_analyzer import EnhancedSpeechAnalyzer
    from .composition_planner import CompositionPlanner
    from .komposition_build_planner import KompositionBuildPlanner
    from .komposition_generator import KompositionGenerator
    from .effect_processor import EffectProcessor
    from .analytics_service import configure_analytics, cleanup_analytics
    from .audio_effect_processor import AudioEffectProcessor
    from .format_manager import FormatManager, COMMON_PRESETS
    from .models import FileInfo, ProcessResult # Import models
    from .video_operations import execute_core_processing # Import core processing logic
    from .video_comparison_tool import VideoComparisonTool
except ImportError:
    from file_manager import FileManager
    from ffmpeg_wrapper import FFMPEGWrapper
    from config import SecurityConfig
    from content_analyzer import VideoContentAnalyzer
    from komposition_processor import KompositionProcessor
    from transition_processor import TransitionProcessor
    from speech_detector import SpeechDetector
    from speech_komposition_processor import SpeechKompositionProcessor
    from enhanced_speech_analyzer import EnhancedSpeechAnalyzer
    from composition_planner import CompositionPlanner
    from komposition_build_planner import KompositionBuildPlanner
    from komposition_generator import KompositionGenerator
    from effect_processor import EffectProcessor
    from audio_effect_processor import AudioEffectProcessor
    from format_manager import FormatManager, COMMON_PRESETS
    from models import FileInfo, ProcessResult # Import models
    from video_operations import execute_core_processing # Import core processing logic
    from video_comparison_tool import VideoComparisonTool


# Initialize MCP server
mcp = FastMCP("ffmpeg-mcp")

# Configure analytics
firebase_endpoint = os.getenv("FIREBASE_ANALYTICS_ENDPOINT")
firebase_api_key = os.getenv("FIREBASE_API_KEY")
analytics_enabled = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"
configure_analytics(firebase_endpoint, analytics_enabled, firebase_api_key)

# Initialize components
file_manager = FileManager()
ffmpeg = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
content_analyzer = VideoContentAnalyzer()
komposition_processor = KompositionProcessor(file_manager, ffmpeg)
transition_processor = TransitionProcessor(file_manager, ffmpeg)
speech_detector = SpeechDetector()
speech_komposition_processor = SpeechKompositionProcessor(file_manager, ffmpeg)
enhanced_speech_analyzer = EnhancedSpeechAnalyzer()
composition_planner = CompositionPlanner()
komposition_build_planner = KompositionBuildPlanner()
komposition_generator = KompositionGenerator()
effect_processor = EffectProcessor(ffmpeg, file_manager)
audio_effect_processor = AudioEffectProcessor(ffmpeg, file_manager)
format_manager = FormatManager()
video_comparison_tool = VideoComparisonTool(ffmpeg, file_manager, content_analyzer)

# FileInfo and ProcessResult classes are now in models.py

@mcp.tool()
async def list_files() -> Dict[str, Any]:
    """🎬 CORE WORKFLOW - List available source files with smart suggestions and quick actions
    
    This is typically your FIRST STEP in any video editing workflow.
    
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
async def get_file_info(file_id: str) -> Dict[str, Any]:
    """Get detailed metadata for a file by ID"""
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
async def get_available_operations() -> Dict[str, Dict[str, str]]:
    """Get list of available FFMPEG operations"""
    operations = ffmpeg.get_available_operations()
    return {"operations": operations}


@mcp.tool()
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
        result = await content_analyzer.analyze_video_content(file_path, file_id, force_reanalysis)
        return result
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
async def list_generated_files() -> Dict[str, Any]:
    """List all generated/processed files in temp directory with metadata"""
    
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
async def cleanup_temp_files() -> Dict[str, str]:
    """Clean up temporary files"""
    try:
        file_manager.cleanup_temp_files()
        return {"message": "Temporary files cleaned up successfully"}
    except Exception as e:
        return {"error": f"Failed to cleanup temp files: {str(e)}"}


# MCP Prompts for Video Editing Guidance
@mcp.prompt()
async def analyze_video_for_editing(file_id: str = "") -> str:
    """Analyze video metadata and suggest optimal editing operations"""
    if not file_id:
        return """Please provide a file_id to analyze. Use list_files() to see available videos.

This prompt will analyze your video's:
- Duration, resolution, and aspect ratio
- Video and audio codecs
- Bitrate and quality metrics
- Stream information

And suggest optimal operations like:
- Best formats for conversion
- Recommended compression settings
- Potential quality improvements
- Compatibility considerations"""
    
    # Get file info if file_id provided
    file_info = await get_file_info(file_id)
    if "error" in file_info:
        return f"Error analyzing file: {file_info['error']}"
    
    basic = file_info.get("basic_info", {})
    media = file_info.get("media_info", {})
    
    analysis = f"""# Video Analysis Report for {basic.get('name', 'Unknown')}

## Basic Information
- File Size: {basic.get('size', 0) / 1024 / 1024:.1f} MB
- Format: {basic.get('extension', 'Unknown')}

## Recommendations
Based on your video characteristics:"""
    
    if media.get("success") and "info" in media:
        info = media["info"]
        format_info = info.get("format", {})
        duration = float(format_info.get("duration", 0))
        
        analysis += f"""
- Duration: {duration:.1f} seconds
- Container: {format_info.get('format_name', 'Unknown')}

### Suggested Operations:
1. **trim** - Extract specific segments (use start= and duration= parameters)
2. **convert** - Standardize format for compatibility
3. **extract_audio** - Separate audio track for replacement
4. **replace_audio** - Add background music or narration
5. **resize** - Optimize for different platforms

### Platform Optimization:
- **YouTube**: Keep current resolution, consider converting to MP4
- **Social Media**: Consider resize to 1080p or 720p for faster upload
- **Mobile**: Compress using convert operation to reduce file size"""
    else:
        analysis += """
Media analysis unavailable. Basic operations still available:
- Use **convert** to standardize format
- Use **trim** to extract segments
- Use **extract_audio** for audio processing"""
    
    return analysis


@mcp.prompt()
async def create_video_montage() -> str:
    """Guide users through creating video montages from multiple clips"""
    return """# Creating Video Montages - Step by Step Guide

## Planning Your Montage

### 1. Identify Your Source Videos
```
Use list_files() to see available videos
Note the file_ids of videos you want to use
```

### 2. Plan Your Clips
For each video, decide:
- Start time (seconds from beginning)
- Duration (how many seconds to extract)
- Order in final montage

### 3. Extract Clips
```
For each clip:
process_file(
    input_file_id="file_xxxxx",
    operation="trim",
    output_extension="mp4",
    params="start=X duration=Y"
)
```

### 4. Standardize Format (Recommended)
```
For each extracted clip:
process_file(
    input_file_id="extracted_clip_id",
    operation="convert",
    output_extension="mp4",
    params=""
)
```

### 5. Combine Clips
```
Use concatenate_simple to join clips:
process_file(
    input_file_id="first_clip_id",
    operation="concatenate_simple",
    output_extension="mp4",
    params="second_video=second_clip_id"
)
```

### 6. Add Final Audio
```
Replace with background music:
process_file(
    input_file_id="combined_video_id",
    operation="replace_audio",
    output_extension="mp4",
    params="audio_file=music_file_id"
)
```

## Pro Tips:
- Keep clips short (3-10 seconds) for dynamic montages
- Ensure consistent resolution across all clips
- Consider rhythm when timing cuts to music
- Test with small clips before processing long videos"""


@mcp.prompt()
async def optimize_for_platform(platform: str = "") -> str:
    """Provide platform-specific optimization recommendations"""
    
    platforms = {
        "youtube": {
            "resolution": "1920x1080 (1080p) or 1280x720 (720p)",
            "aspect_ratio": "16:9",
            "format": "MP4 (H.264 video, AAC audio)",
            "max_size": "128GB or 12 hours",
            "bitrate": "8-12 Mbps for 1080p",
            "fps": "24, 25, 30, 50, or 60 fps"
        },
        "instagram": {
            "resolution": "1080x1080 (square) or 1080x1350 (portrait)",
            "aspect_ratio": "1:1 or 4:5",
            "format": "MP4 or MOV",
            "max_size": "4GB",
            "duration": "60 seconds max for feed, 15 seconds for stories",
            "bitrate": "3.5 Mbps recommended"
        },
        "tiktok": {
            "resolution": "1080x1920 (vertical)",
            "aspect_ratio": "9:16",
            "format": "MP4 or MOV",
            "max_size": "287.6MB",
            "duration": "10 minutes max",
            "bitrate": "Variable, platform optimizes"
        },
        "twitter": {
            "resolution": "1920x1080 or 1280x720",
            "aspect_ratio": "16:9 recommended",
            "format": "MP4 or MOV",
            "max_size": "512MB",
            "duration": "2 minutes 20 seconds max",
            "bitrate": "6-10 Mbps"
        }
    }
    
    if not platform:
        return f"""# Platform Optimization Guide

Choose your target platform:
{chr(10).join([f"- **{p.title()}**" for p in platforms.keys()])}

## General Optimization Steps:

### 1. Check Current Video Properties
```
get_file_info(file_id="your_video_id")
```

### 2. Resize if Needed
```
process_file(
    input_file_id="your_video_id",
    operation="resize", 
    output_extension="mp4",
    params="width=1920 height=1080"
)
```

### 3. Convert for Compatibility
```
process_file(
    input_file_id="your_video_id",
    operation="convert",
    output_extension="mp4",
    params=""
)
```

### 4. Compress for Size Limits
```
Use convert operation with MP4 output
This automatically applies reasonable compression
```

Call this prompt again with platform="youtube" (or instagram, tiktok, twitter) for specific guidelines."""
    
    platform = platform.lower()
    if platform in platforms:
        specs = platforms[platform]
        return f"""# {platform.title()} Optimization Guide

## Technical Specifications:
- **Resolution**: {specs['resolution']}
- **Aspect Ratio**: {specs['aspect_ratio']}
- **Format**: {specs['format']}
- **Max File Size**: {specs['max_size']}
- **Recommended Bitrate**: {specs.get('bitrate', 'Variable')}
{f"- **Frame Rate**: {specs['fps']}" if 'fps' in specs else ""}
{f"- **Max Duration**: {specs['duration']}" if 'duration' in specs else ""}

## Optimization Steps:

### 1. Resize Video (if needed)
```
process_file(
    input_file_id="your_video_id",
    operation="resize",
    output_extension="mp4", 
    params="width=X height=Y"  # Use resolution from specs above
)
```

### 2. Convert to Optimal Format
```
process_file(
    input_file_id="your_video_id",
    operation="convert",
    output_extension="mp4",
    params=""
)
```

### 3. Trim if Exceeding Duration Limits
```
process_file(
    input_file_id="your_video_id",
    operation="trim",
    output_extension="mp4",
    params="start=0 duration=X"  # X = max seconds allowed
)
```

## {platform.title()}-Specific Tips:
{_get_platform_tips(platform)}"""
    else:
        return f"Platform '{platform}' not recognized. Available: {', '.join(platforms.keys())}"


def _get_platform_tips(platform: str) -> str:
    """Get platform-specific tips"""
    tips = {
        "youtube": """- Use clear thumbnails and titles
- Consider adding captions with extract_audio + replace_audio workflow
- Longer content performs better (8+ minutes)
- Maintain consistent upload schedule""",
        "instagram": """- First 3 seconds are crucial for engagement
- Use trending audio with replace_audio operation
- Square format works best for feed posts
- Stories should be 9:16 vertical""",
        "tiktok": """- Vertical format is mandatory (9:16)
- Hook viewers in first 3 seconds
- Trending sounds boost visibility
- Quick cuts and dynamic editing work best""",
        "twitter": """- Auto-play is silent, add captions
- Keep videos under 2 minutes for best engagement
- Square or landscape formats work well
- Consider GIF conversion for short clips"""
    }
    return tips.get(platform, "No specific tips available")


@mcp.prompt()
async def improve_video_quality() -> str:
    """Provide guidance for enhancing video quality"""
    return """# Video Quality Enhancement Guide

## Quality Assessment Steps

### 1. Analyze Current Quality
```
get_file_info(file_id="your_video_id")
```
Look for:
- Resolution (higher is generally better)
- Bitrate (affects file size vs quality)
- Codec (newer codecs like H.264/H.265 are more efficient)

### 2. Basic Quality Improvements

#### Convert to Modern Codec
```
process_file(
    input_file_id="your_video_id",
    operation="convert",
    output_extension="mp4",
    params=""
)
```
Benefits:
- Better compression efficiency
- Wider compatibility
- Improved streaming performance

#### Audio Enhancement
```
# Extract current audio
process_file(
    input_file_id="your_video_id", 
    operation="extract_audio",
    output_extension="m4a",
    params=""
)

# Normalize audio levels
process_file(
    input_file_id="extracted_audio_id",
    operation="normalize_audio", 
    output_extension="m4a",
    params=""
)

# Replace with normalized audio
process_file(
    input_file_id="your_video_id",
    operation="replace_audio",
    output_extension="mp4", 
    params="audio_file=normalized_audio_id"
)
```

## Quality Issues & Solutions

### Low Resolution
**Problem**: Video appears pixelated or blurry
**Solution**: Unfortunately, upscaling isn't available in current operations
**Prevention**: Always record/export at highest available resolution

### Audio Issues
**Problem**: Audio too quiet, too loud, or inconsistent
**Solution**: Use normalize_audio operation
```
process_file(operation="normalize_audio", ...)
```

### Large File Sizes
**Problem**: File too big for sharing/uploading
**Solution**: Re-encode with convert operation
```
process_file(operation="convert", output_extension="mp4", ...)
```

### Compatibility Issues
**Problem**: Video won't play on certain devices/platforms
**Solution**: Convert to MP4 with H.264 codec
```
process_file(operation="convert", output_extension="mp4", ...)
```

## Best Practices:
- Always keep original files as backup
- Test conversions with short clips first
- Consider target platform requirements
- Balance file size with quality needs
- Use consistent settings across related videos"""


@mcp.prompt()
async def compress_efficiently() -> str:
    """Guide users through efficient video compression"""
    return """# Efficient Video Compression Guide

## Understanding Compression

### File Size Factors:
1. **Resolution** - Higher resolution = larger files
2. **Duration** - Longer videos = larger files  
3. **Bitrate** - Higher bitrate = better quality but larger files
4. **Codec** - Modern codecs compress better

## Compression Workflow

### 1. Check Current File Size
```
list_files()  # Check size column
```

### 2. Estimate Target Size
- **Email**: < 25MB typically
- **SMS/Messaging**: < 100MB
- **Social Media**: varies by platform (see optimize_for_platform prompt)
- **Streaming**: Balance quality vs bandwidth

### 3. Apply Compression
```
process_file(
    input_file_id="your_video_id",
    operation="convert", 
    output_extension="mp4",
    params=""
)
```

### 4. Check Results
```
list_files()  # Compare new file size
```

## Advanced Compression Strategies

### For Large Size Reductions:
1. **Trim Unnecessary Content**
```
process_file(
    operation="trim",
    params="start=X duration=Y"  # Keep only essential parts
)
```

2. **Reduce Resolution** 
```
process_file(
    operation="resize",
    params="width=1280 height=720"  # From 1080p to 720p
)
```

3. **Convert to Efficient Format**
```
process_file(operation="convert", output_extension="mp4")
```

## Compression Decision Matrix

### Original > 1GB:
- Try resize to 720p first
- Then convert to MP4
- Consider trimming if possible

### Original 100MB - 1GB:
- Convert to MP4 first
- Resize only if still too large

### Original < 100MB:
- Usually just convert to MP4
- May not need compression

## Quality vs Size Estimates:
- **1080p MP4**: ~8-12 Mbps (1MB per second)
- **720p MP4**: ~4-6 Mbps (0.5MB per second)  
- **480p MP4**: ~2-3 Mbps (0.25MB per second)

## Pro Tips:
- Always test with a short clip first
- Keep original files as backup
- Different content compresses differently (talking head vs action)
- Modern phones can handle lower resolutions well"""


@mcp.prompt()
async def create_highlight_reel() -> str:
    """Guide users through creating highlight reels from longer content"""
    return """# Creating Highlight Reels - Complete Guide

## Planning Your Highlight Reel

### 1. Content Analysis
- Watch your source video(s) and note timestamps of best moments
- Aim for 30-60 seconds total for social media
- 2-3 minutes for longer form content

### 2. Identify Key Moments
Look for:
- Peak action or excitement
- Emotional moments
- Key information or quotes
- Visually stunning scenes
- Audience reactions

## Step-by-Step Workflow

### 1. Extract Individual Highlights
```
# For each highlight moment:
process_file(
    input_file_id="source_video_id",
    operation="trim",
    output_extension="mp4", 
    params="start=X duration=Y"  # X=start time, Y=clip length
)
```

**Recommended clip lengths:**
- Action moments: 3-5 seconds
- Dialogue/quotes: 5-10 seconds  
- Establishing shots: 2-3 seconds

### 2. Standardize All Clips
```
# Convert each extracted clip:
process_file(
    input_file_id="highlight_clip_id",
    operation="convert",
    output_extension="mp4",
    params=""
)
```

### 3. Combine Highlights
```
# Join clips sequentially:
process_file(
    input_file_id="first_clip_id", 
    operation="concatenate_simple",
    output_extension="mp4",
    params="second_video=second_clip_id"
)

# Continue adding more clips as needed
```

### 4. Add Background Music
```
# Replace audio with energetic music:
process_file(
    input_file_id="combined_highlights_id",
    operation="replace_audio", 
    output_extension="mp4",
    params="audio_file=music_file_id"
)
```

## Highlight Reel Best Practices

### Pacing & Flow:
- Start with your strongest moment
- Vary clip lengths for rhythm
- Build energy throughout
- End with a memorable moment

### Music Selection:
- Match tempo to content energy
- Ensure music is royalty-free
- Consider platform requirements
- Volume should complement, not overpower

### Technical Tips:
- Keep consistent resolution across clips
- Ensure smooth transitions
- Test on target platform before sharing
- Consider adding text overlays (external tool needed)

## Common Workflows by Content Type:

### Sports/Action:
- 2-4 second clips of peak action
- Fast-paced music
- Quick cuts for energy

### Educational/Talking Head:
- 5-8 second clips of key points
- Moderate pacing
- Include visual variety

### Event/Documentary:
- Mix of 3-10 second clips
- Emotional music choices
- Tell a story through clip selection

### Gaming:
- Epic moments, fails, wins
- Synchronized to music beats
- Include reaction moments

## Example Highlight Reel Structure (60 seconds):
1. **Hook** (0-5s): Best/most exciting moment
2. **Introduction** (5-15s): Set context
3. **Build** (15-45s): 3-4 supporting highlights  
4. **Climax** (45-55s): Second best moment
5. **Outro** (55-60s): Memorable ending

Remember: Great highlight reels tell a story, not just show random good moments!"""


@mcp.prompt()
async def add_professional_audio() -> str:
    """Guide users through professional audio workflows"""
    return """# Professional Audio Enhancement Guide

## Audio Quality Assessment

### 1. Analyze Current Audio
```
get_file_info(file_id="your_video_id")
```
Look for audio stream information:
- Sample rate (44.1kHz or 48kHz preferred)
- Bit depth (16-bit minimum, 24-bit better)
- Codec (AAC is modern standard)

### 2. Extract for Analysis
```
process_file(
    input_file_id="your_video_id",
    operation="extract_audio", 
    output_extension="m4a",
    params=""
)
```

## Professional Audio Workflows

### Workflow 1: Audio Cleanup & Enhancement
```
# Step 1: Extract original audio
process_file(
    input_file_id="video_id",
    operation="extract_audio",
    output_extension="m4a", 
    params=""
)

# Step 2: Normalize levels
process_file(
    input_file_id="extracted_audio_id",
    operation="normalize_audio",
    output_extension="m4a",
    params=""
)

# Step 3: Replace with enhanced audio
process_file(
    input_file_id="video_id", 
    operation="replace_audio",
    output_extension="mp4",
    params="audio_file=normalized_audio_id"
)
```

### Workflow 2: Background Music Addition
```
# Replace original audio with music:
process_file(
    input_file_id="video_id",
    operation="replace_audio",
    output_extension="mp4", 
    params="audio_file=music_file_id"
)
```

### Workflow 3: Voiceover Replacement
```
# Record voiceover separately, then:
process_file(
    input_file_id="video_id",
    operation="replace_audio", 
    output_extension="mp4",
    params="audio_file=voiceover_file_id"
)
```

## Audio Best Practices

### Recording Quality:
- **Environment**: Quiet space, minimal echo
- **Distance**: 6-12 inches from microphone
- **Levels**: Avoid clipping, aim for -12dB to -6dB peaks
- **Format**: Record in highest quality available

### Post-Production:
- **Normalize**: Use normalize_audio for consistent levels
- **Noise Floor**: Keep ambient noise low
- **Dynamic Range**: Maintain natural variation
- **Sync**: Ensure audio matches video timing

### Music Selection:
- **Royalty-Free Sources**:
  - YouTube Audio Library
  - Freesound.org
  - CC Search
  - Local musician collaborations

- **Mood Matching**:
  - Upbeat for action/sports
  - Ambient for documentaries  
  - Dramatic for emotional content
  - Silent for dialogue-heavy content

### Platform Considerations:
- **Social Media**: Often viewed without sound initially
- **YouTube**: Good audio crucial for retention
- **Podcasts**: Audio quality is primary concern
- **Presentations**: Clear speech over music

## Audio Levels Guide:
- **Dialogue**: -12dB to -6dB average
- **Music**: -18dB to -12dB when under dialogue
- **Sound Effects**: -15dB to -8dB depending on impact needed
- **Ambient**: -24dB to -18dB for background

## Common Audio Issues & Solutions:

### Too Quiet:
```
Use normalize_audio operation
```

### Too Loud/Distorted:
- Re-record if possible
- Use normalize_audio to bring levels down

### Inconsistent Levels:
```
Extract audio → normalize_audio → replace_audio
```

### Poor Quality Music:
- Source higher quality audio files
- Ensure sample rate matches video (usually 48kHz)

### Sync Issues:
- May require external tools for fine adjustment
- Start with clean, well-synced source material

## Professional Audio Checklist:
✓ Audio levels consistent throughout
✓ No clipping or distortion
✓ Background noise minimized
✓ Music doesn't overpower dialogue
✓ Smooth transitions between clips
✓ Platform-appropriate volume levels
✓ High-quality source files used
✓ Proper format and codec selected"""


@mcp.prompt()
async def fix_video_issues() -> str:
    """Diagnose and provide solutions for common video problems"""
    return """# Video Troubleshooting & Repair Guide

## Common Issues Diagnostic

### 1. File Won't Play/Open
**Symptoms**: Error messages, black screen, no audio
**Diagnosis Steps**:
```
get_file_info(file_id="problem_video_id")
```
Look for:
- Unusual codecs
- Corruption indicators
- Missing audio/video streams

**Solutions**:
```
# Try conversion to standard format:
process_file(
    input_file_id="problem_video_id",
    operation="convert",
    output_extension="mp4", 
    params=""
)
```

### 2. Audio/Video Out of Sync
**Symptoms**: Lips don't match speech, music timing off
**Diagnosis**: Usually from encoding issues or editing errors
**Solutions**:
```
# Extract and replace audio:
process_file(operation="extract_audio", ...)
process_file(operation="replace_audio", ...)
```
*Note: Fine sync adjustment requires external tools*

### 3. Poor Video Quality
**Symptoms**: Pixelation, blurriness, artifacts
**Diagnosis**: Over-compression or low source quality
**Solutions**:
```
# Re-encode with better settings:
process_file(
    operation="convert",
    output_extension="mp4",
    params=""
)
```

### 4. File Too Large
**Symptoms**: Upload failures, storage issues
**Solutions**: See compress_efficiently prompt
```
# Basic compression:
process_file(operation="convert", output_extension="mp4")

# More aggressive:
process_file(operation="resize", params="width=1280 height=720")
```

### 5. Wrong Aspect Ratio
**Symptoms**: Black bars, stretched video
**Solutions**:
```
# Resize to correct dimensions:
process_file(
    operation="resize",
    params="width=X height=Y"  # Calculate proper aspect ratio
)
```

### 6. Audio Problems
**Symptoms**: No sound, distorted audio, wrong levels
**Solutions**:
```
# Check if audio exists:
get_file_info(file_id="video_id")

# Normalize audio levels:
process_file(operation="extract_audio", ...)
process_file(operation="normalize_audio", ...)
process_file(operation="replace_audio", ...)
```

## Preventive Measures

### Recording Best Practices:
- Use highest quality settings available
- Ensure adequate lighting
- Stable mounting/tripod use
- Test audio levels before recording
- Record in standard frame rates (24, 30, 60 fps)

### Export/Encoding Best Practices:
- Use standard codecs (H.264 video, AAC audio)
- Maintain original resolution when possible
- Use constant frame rate
- Avoid excessive compression
- Keep master copies in high quality

### Storage Best Practices:
- Regular backups of important videos
- Use reliable storage media
- Avoid network interruptions during transfers
- Verify file integrity after copying

## Emergency Recovery Procedures

### For Corrupted Files:
1. Try conversion to MP4
2. Extract working portions with trim operation
3. Check if audio can be salvaged separately

### For Upload Failures:
1. Check file size limits
2. Verify format compatibility
3. Test with smaller/shorter version first
4. Use platform-specific optimization

### For Playback Issues:
1. Convert to MP4 format
2. Test on different devices/players
3. Check codec compatibility
4. Verify file isn't corrupted

## When to Seek External Tools:
- Frame-accurate sync adjustment
- Advanced noise reduction
- Color correction/grading  
- Complex audio mixing
- Subtitle/caption addition
- Advanced effects or transitions

## File Recovery Checklist:
✓ Try basic conversion first
✓ Test with short clips before processing full video
✓ Keep original files until repair confirmed working
✓ Document what caused the issue to prevent recurrence
✓ Consider professional recovery services for critical content

## Platform-Specific Issues:

### YouTube:
- Check community guidelines compliance
- Verify copyright clearance
- Ensure proper format (MP4 recommended)

### Social Media:
- Check duration limits
- Verify aspect ratio requirements  
- Test mobile playback

### Email/Messaging:
- Compress to size limits
- Use widely compatible formats
- Test on recipient's likely device type

Remember: Prevention is better than repair - always maintain high-quality source files!"""


@mcp.prompt()
async def batch_processing_guide() -> str:
    """Guide users through efficient batch processing workflows"""
    return """# Batch Processing & Automation Guide

## Planning Batch Operations

### 1. Identify Common Tasks
- Converting multiple videos to same format
- Extracting clips from multiple long videos
- Adding same audio track to multiple videos
- Resizing multiple videos for platform
- Creating thumbnails from multiple videos

### 2. Standardize Parameters
Before starting, determine:
- Target format and resolution
- Consistent naming convention
- Output quality settings
- Processing order/priority

## Batch Workflow Strategies

### Strategy 1: Sequential Processing
Process one file completely before starting next:
```
# For each video:
1. list_files() → identify file_id
2. process_file(operation="convert", ...)
3. Verify success before continuing
4. Move to next file
```

**Pros**: Easy to track, can stop/resume
**Cons**: Slower overall, doesn't use full system capacity

### Strategy 2: Pipeline Processing  
Start multiple operations in sequence:
```
# Start multiple operations:
1. Begin trim operation on video 1
2. While that runs, start convert on video 2  
3. Chain operations as resources allow
```

**Pros**: Faster overall processing
**Cons**: More complex tracking, higher resource usage

## Common Batch Scenarios

### Scenario 1: Convert Multiple Videos to MP4
```
# Get all video files:
files = list_files()

# For each video file:
for video in video_files:
    result = process_file(
        input_file_id=video.id,
        operation="convert", 
        output_extension="mp4",
        params=""
    )
    # Check result.success before continuing
```

### Scenario 2: Extract Highlights from Multiple Long Videos
```
# Define highlight timestamps for each video:
highlights = {
    "video1_id": [(10, 5), (30, 8), (60, 6)],  # (start, duration)
    "video2_id": [(5, 4), (25, 7)],
    # etc...
}

# Extract each highlight:
for video_id, clips in highlights.items():
    for start, duration in clips:
        process_file(
            input_file_id=video_id,
            operation="trim",
            output_extension="mp4", 
            params=f"start={start} duration={duration}"
        )
```

### Scenario 3: Add Same Audio to Multiple Videos
```
# Assuming you have background_music_id:
for video_id in video_list:
    process_file(
        input_file_id=video_id,
        operation="replace_audio",
        output_extension="mp4",
        params=f"audio_file={background_music_id}"
    )
```

### Scenario 4: Platform Optimization for Multiple Videos
```
# For YouTube optimization:
target_specs = {
    "operation": "resize",
    "params": "width=1920 height=1080"
}

for video_id in video_list:
    # First resize:
    resized = process_file(
        input_file_id=video_id,
        **target_specs
    )
    
    # Then convert:
    if resized.success:
        process_file(
            input_file_id=resized.output_file_id,
            operation="convert",
            output_extension="mp4"
        )
```

## Performance Optimization

### Processing Time Estimates:
- **Convert**: ~1x video duration (10 min video = ~10 min processing)
- **Trim**: Very fast (~seconds regardless of source length)  
- **Resize**: ~0.5-2x video duration depending on size change
- **Audio operations**: ~0.1-0.5x video duration
- **Concatenate**: ~0.5x combined duration

### Resource Management:
- **CPU**: FFMPEG operations are CPU-intensive
- **Storage**: Ensure adequate temp space (2-3x source file size)
- **Memory**: Longer videos use more RAM
- **Thermal**: Extended processing may cause throttling

### Optimization Tips:
1. **Process shorter videos first** - quick wins and feedback
2. **Group similar operations** - batch all converts, then all resizes
3. **Monitor temp directory** - use cleanup_temp_files() regularly
4. **Test with samples** - verify settings work before full batch
5. **Keep source files safe** - don't delete until batch complete

## Error Handling & Recovery

### Tracking Progress:
```
# Create processing log:
results = []
for video_id in video_list:
    result = process_file(...)
    results.append({
        'video_id': video_id,
        'success': result.success,
        'output_id': result.output_file_id,
        'error': result.message if not result.success else None
    })
```

### Handling Failures:
- **Partial failures**: Skip failed files, continue with others
- **Storage full**: Use cleanup_temp_files(), then resume
- **Format errors**: Try convert operation first, then retry
- **Timeout errors**: Split large files into smaller segments

### Resume Strategies:
- Keep list of completed file_ids
- Check temp directory for existing outputs
- Restart from last successful operation

## Quality Control

### Batch Validation Checklist:
✓ All source files processed successfully
✓ Output file sizes reasonable (not 0 bytes or extremely large)
✓ Spot-check video quality on sample outputs
✓ Verify audio sync on audio-replaced videos
✓ Confirm all outputs play correctly
✓ Check that temp files cleaned up appropriately

### Testing Protocol:
1. **Small batch test** (2-3 files) with exact settings
2. **Quality verification** of test outputs
3. **Timing measurement** to estimate full batch duration
4. **Resource monitoring** to ensure system can handle load
5. **Full batch execution** with monitoring

## Automation Considerations:

### What Can Be Automated:
- Repetitive format conversions
- Standard resize operations
- Bulk audio replacement
- Cleanup operations

### What Requires Human Input:
- Creative timing decisions (clip selection)
- Quality assessment
- Error diagnosis and recovery
- Custom parameter adjustment

### Future Automation Ideas:
- Scheduled processing workflows
- Auto-detection of optimal settings
- Progress monitoring dashboards
- Automatic quality validation

Remember: Start small, test thoroughly, and always keep your source files safe during batch operations!"""


# CONTEXT SYSTEM - DISABLED (FastMCP doesn't support @mcp.context())
# These functions were originally designed as MCP context providers to give
# intelligent suggestions and workflow guidance. They can be reactivated as:
# 1. @mcp.prompt() functions for explicit context queries
# 2. Helper functions integrated into existing tool responses  
# 3. Part of enhanced tool outputs with contextual suggestions
# 
# Consider re-enabling these for better user experience when using
# a full MCP implementation that supports context providers.

# Global tracking for context intelligence
_operation_history = []
_performance_stats = {}

async def _get_files_summary() -> str:
    """Get a summary of available files - CONTEXT HELPER"""
    try:
        files_result = await list_files()
        if "error" in files_result:
            return f"Error: {files_result['error']}"
        
        files = files_result.get("files", [])
        if not files:
            return "No files available"
        
        summary = []
        total_size = 0
        
        for file in files:
            size_mb = file.size / (1024 * 1024)
            total_size += size_mb
            summary.append(f"- {file.name} ({size_mb:.1f}MB) - ID: {file.id}")
        
        return f"{len(files)} files, {total_size:.1f}MB total:\n" + "\n".join(summary)
    except Exception as e:
        return f"Error getting files: {str(e)}"

async def _get_recent_operations() -> str:
    """Get recent operations from history - CONTEXT HELPER"""
    if not _operation_history:
        return "No recent operations"
    
    recent = _operation_history[-5:]  # Last 5 operations
    summary = []
    
    for op in recent:
        timestamp = op.get('timestamp', 'Unknown time')
        operation = op.get('operation', 'Unknown')
        success = op.get('success', False)
        input_file = op.get('input_file', 'Unknown')
        status = "✅" if success else "❌"
        summary.append(f"{status} {operation} on {input_file} ({timestamp})")
    
    return "\n".join(summary)

async def _get_temp_files_status() -> str:
    """Get status of temporary files - CONTEXT HELPER"""
    try:
        import os
        temp_dir = SecurityConfig.TEMP_DIR
        
        if not temp_dir.exists():
            return "No temp directory"
        
        temp_files = list(temp_dir.glob("*"))
        if not temp_files:
            return "No temporary files"
        
        total_size = sum(f.stat().st_size for f in temp_files if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        return f"{len(temp_files)} temp files, {size_mb:.1f}MB"
    except Exception as e:
        return f"Error checking temp files: {str(e)}"

def _get_storage_info() -> str:
    """Get storage information - CONTEXT HELPER"""
    try:
        import shutil
        temp_dir = SecurityConfig.TEMP_DIR
        source_dir = SecurityConfig.SOURCE_DIR
        
        temp_free = shutil.disk_usage(temp_dir).free / (1024**3)  # GB
        source_free = shutil.disk_usage(source_dir).free / (1024**3)  # GB
        
        return f"Temp: {temp_free:.1f}GB free, Source: {source_free:.1f}GB free"
    except Exception:
        return "Storage info unavailable"

def _get_active_operations() -> str:
    """Get currently active operations - CONTEXT HELPER (placeholder for now)"""
    # In a real implementation, this would track running FFMPEG processes
    return "No active operations detected"

async def _get_file_genealogy() -> str:
    """Track file processing relationships - CONTEXT HELPER"""
    # This would track which files were created from which sources
    genealogy = {}
    
    for op in _operation_history:
        if op.get('success') and op.get('output_file_id'):
            input_file = op.get('input_file', 'Unknown')
            output_file = op.get('output_file_id', 'Unknown')
            operation = op.get('operation', 'Unknown')
            
            if input_file not in genealogy:
                genealogy[input_file] = []
            genealogy[input_file].append(f"{output_file} (via {operation})")
    
    if not genealogy:
        return "No file processing history available"
    
    summary = []
    for source, outputs in genealogy.items():
        summary.append(f"**{source}** →")
        for output in outputs:
            summary.append(f"  - {output}")
    
    return "\n".join(summary)

async def _suggest_next_operations() -> str:
    """Suggest logical next operations based on current state - CONTEXT HELPER"""
    try:
        files_result = await list_files()
        files = files_result.get("files", [])
        
        if not files:
            return "Add some video files to get started"
        
        suggestions = []
        
        # Check for large files that might need compression
        large_files = [f for f in files if f.size > 100 * 1024 * 1024]  # > 100MB
        if large_files:
            suggestions.append(f"• Consider compressing {len(large_files)} large files with convert operation")
        
        # Check for non-MP4 files
        non_mp4 = [f for f in files if f.extension.lower() != '.mp4']
        if non_mp4:
            suggestions.append(f"• Convert {len(non_mp4)} non-MP4 files for better compatibility")
        
        # Check for very long videos (based on file size estimation)
        potentially_long = [f for f in files if f.size > 500 * 1024 * 1024]  # > 500MB
        if potentially_long:
            suggestions.append(f"• Consider trimming {len(potentially_long)} potentially long videos")
        
        # Check temp files for cleanup
        temp_status = await _get_temp_files_status()
        if "temp files" in temp_status and not "No temporary" in temp_status:
            suggestions.append("• Run cleanup_temp_files() to free up space")
        
        if not suggestions:
            suggestions.append("• Files look good! Ready for editing operations")
        
        return "\n".join(suggestions)
    except Exception as e:
        return f"Error generating suggestions: {str(e)}"

def _analyze_platform_compatibility() -> str:
    """Analyze how current files match platform requirements - CONTEXT HELPER"""
    # This would analyze files against platform specs
    return """Current files analyzed against major platforms:
• YouTube: Most files compatible, consider MP4 conversion for optimal upload
• Instagram: Large files may need resizing to 1080p max
• TikTok: Consider vertical format conversion for better engagement
• Twitter: File sizes look good for platform limits"""

def _suggest_platform_optimizations() -> str:
    """Suggest platform-specific optimizations - CONTEXT HELPER"""
    return """Recommended optimizations:
1. Use resize operation for Instagram (1080x1080 or 1080x1350)
2. Convert all to MP4 for maximum compatibility
3. Use trim operation to create shorter clips for social media
4. Consider compress_efficiently for faster uploads"""

def _analyze_quality_issues() -> str:
    """Analyze potential quality issues - CONTEXT HELPER"""
    return """Quality analysis based on file characteristics:
• No obvious corruption detected
• Some files may benefit from audio normalization
• Consider format standardization for consistent quality
• Check individual files with get_file_info() for detailed analysis"""

def _suggest_quality_improvements() -> str:
    """Suggest quality enhancement opportunities - CONTEXT HELPER"""
    return """Enhancement opportunities:
1. Use normalize_audio operation for better audio levels
2. Convert to MP4 for optimal codec efficiency
3. Use extract_audio + replace_audio workflow for audio cleanup
4. Consider resize operation if source resolution is inconsistent"""

# process_file_internal and process_file_as_finished functions are now moved to video_operations.py

@mcp.tool()
async def process_komposition_file(komposition_path: str) -> Dict[str, Any]:
    """Process a komposition JSON file to create beat-synchronized music video
    
    Args:
        komposition_path: Path to komposition JSON file (relative to project root)
    
    Returns:
        Result with output file ID and composition details
    """
    try:
        # Load komposition from file
        full_path = Path(komposition_path)
        if not full_path.is_absolute():
            # Make relative to project root
            project_root = Path(__file__).parent.parent
            full_path = project_root / komposition_path
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"Komposition file not found: {komposition_path}"
            }
        
        # Load and process komposition
        komposition_data = await komposition_processor.load_komposition(str(full_path))
        result = await komposition_processor.process_komposition(komposition_data)
        
        return result
        
    except Exception as e:
        return {
            "success": False, 
            "error": f"Failed to process komposition: {str(e)}"
        }

# process_file_internal and process_file_as_finished functions are now moved to video_operations.py

@mcp.tool()
async def process_transition_effects_komposition(komposition_path: str) -> Dict[str, Any]:
    """Process a komposition JSON file with advanced transition effects tree
    
    Args:
        komposition_path: Path to komposition JSON file with effects_tree (relative to project root)
    
    Returns:
        Result with output file ID and effects composition details
    """
    try:
        # Load komposition from file
        full_path = Path(komposition_path)
        if not full_path.is_absolute():
            # Make relative to project root
            project_root = Path(__file__).parent.parent
            full_path = project_root / komposition_path
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"Transition effects komposition file not found: {komposition_path}"
            }
        
        # Load and process komposition with effects tree
        komposition_data = await transition_processor.load_komposition_with_effects(str(full_path))
        result = await transition_processor.process_effects_tree(komposition_data)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process transition effects komposition: {str(e)}"
        }


@mcp.tool()
async def process_speech_komposition(komposition_path: str) -> Dict[str, Any]:
    """Process a komposition JSON file with speech overlay capabilities
    
    This tool creates music videos that combine multiple video segments with intelligent
    speech detection and audio layering. It can detect speech in videos and layer the
    original speech over background music while maintaining perfect synchronization.
    
    Args:
        komposition_path: Path to komposition JSON file with speechOverlay settings (relative to project root)
    
    Returns:
        Result with output file ID and speech processing details
        
    Example komposition structure:
    {
        "metadata": {"title": "Speech Music Video", "bpm": 120, "estimatedDuration": 30},
        "segments": [
            {
                "id": "speech_segment",
                "sourceRef": "video_with_speech.mp4", 
                "speechOverlay": {
                    "enabled": true,
                    "backgroundMusic": "music.mp3",
                    "musicVolume": 0.3,
                    "speechVolume": 0.8,
                    "speechSegments": [{"start_time": 2.5, "end_time": 5.0, "duration": 2.5}]
                }
            }
        ]
    }
    """
    try:
        # Load komposition from file
        full_path = Path(komposition_path)
        if not full_path.is_absolute():
            # Make relative to project root
            project_root = Path(__file__).parent.parent
            full_path = project_root / komposition_path
        
        if not full_path.exists():
            return {
                "success": False,
                "error": f"Speech komposition file not found: {komposition_path}"
            }
        
        # Process komposition with speech overlay support
        result = await speech_komposition_processor.process_speech_komposition(str(full_path))
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process speech komposition: {str(e)}"
        }


@mcp.tool()
async def detect_speech_segments(file_id: str, force_reanalysis: bool = False, threshold: float = 0.5, 
                                min_speech_duration: int = 250, min_silence_duration: int = 100) -> Dict[str, Any]:
    """
    Detect speech segments in video/audio file using AI-powered voice activity detection.
    
    This tool uses Silero VAD (Voice Activity Detection) to identify when people are speaking
    in video or audio files. It provides precise timestamps and quality assessment for each
    speech segment, enabling intelligent audio editing and synchronization.
    
    Args:
        file_id: ID of the source video/audio file
        force_reanalysis: Skip cache and reanalyze (default: False)
        threshold: Speech detection sensitivity 0.1-0.9 (default: 0.5, higher = more strict)
        min_speech_duration: Minimum speech segment duration in ms (default: 250)
        min_silence_duration: Minimum silence gap to separate segments in ms (default: 100)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if detection succeeded
        - has_speech: Boolean indicating if speech was found
        - speech_segments: List of segments with start_time, end_time, duration, quality
        - total_speech_duration: Sum of all speech segment durations
        - total_segments: Number of speech segments detected
        - analysis_metadata: Processing details and engine used
        
    Example Response:
        {
            "success": true,
            "has_speech": true,
            "speech_segments": [
                {
                    "segment_id": 0,
                    "start_time": 5.2,
                    "end_time": 12.8,
                    "duration": 7.6,
                    "confidence": 0.5,
                    "audio_quality": "clear"
                }
            ],
            "total_speech_duration": 7.6,
            "total_segments": 1,
            "analysis_metadata": {
                "engine_used": "silero",
                "processing_time": 1640995200.0
            }
        }
    
    Use Cases:
    - Extract speech segments from music videos before adding background music
    - Identify dialogue sections in tutorial videos
    - Analyze podcast audio for editing and enhancement
    - Prepare audio for speech-to-text transcription
    
    Notes:
    - Results are cached for 5 minutes to improve performance
    - Supports all video formats (MP4, AVI, MOV) and audio formats (MP3, WAV, FLAC)
    - Audio is automatically extracted from video files for analysis
    - Uses pluggable backend system with Silero VAD as primary, WebRTC VAD as fallback
    """
    try:
        # Get file path from ID
        input_path = file_manager.resolve_id(file_id)
        if not input_path:
            return {
                "success": False,
                "error": f"File with ID '{file_id}' not found"
            }
        
        # Run speech detection
        result = await speech_detector.detect_speech_segments(
            input_path,
            force_reanalysis=force_reanalysis,
            threshold=threshold,
            min_speech_duration=min_speech_duration,
            min_silence_duration=min_silence_duration
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Speech detection failed: {str(e)}"
        }


@mcp.tool()
async def get_speech_insights(file_id: str) -> Dict[str, Any]:
    """
    Get detailed insights and analysis from cached speech detection results.
    
    This tool provides comprehensive analysis of previously detected speech segments,
    including quality metrics, timing patterns, and intelligent editing suggestions.
    Must be called after detect_speech_segments() to have cached data available.
    
    Args:
        file_id: ID of the analyzed video/audio file
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if insights were generated
        - summary: Statistical summary of speech segments
        - quality_distribution: Breakdown of audio quality levels
        - timing_analysis: Patterns in speech timing and gaps
        - editing_suggestions: AI-generated recommendations for editing
        - analysis_metadata: Original detection metadata
        
    Example Response:
        {
            "success": true,
            "summary": {
                "total_segments": 3,
                "total_speech_duration": 25.4,
                "average_segment_duration": 8.47,
                "longest_segment": 12.8,
                "shortest_segment": 5.2
            },
            "quality_distribution": {
                "clear": 2,
                "moderate": 1,
                "low": 0
            },
            "timing_analysis": {
                "average_gap": 2.1,
                "longest_gap": 4.5,
                "speech_density": 0.68
            },
            "editing_suggestions": [
                {
                    "type": "quality_improvement",
                    "message": "Segment 2 has moderate quality. Consider audio enhancement.",
                    "segment_id": 1,
                    "priority": "low"
                }
            ]
        }
    
    Use Cases:
    - Assess overall speech quality before proceeding with audio mixing
    - Identify segments that need audio enhancement or replacement
    - Get recommendations for optimal speech extraction and synchronization
    - Analyze speech patterns for automated editing decisions
    
    Notes:
    - Requires previous speech detection analysis (cached results)
    - Provides actionable editing suggestions based on AI analysis
    - Quality assessment helps prioritize which segments to use in final edit
    - Timing analysis useful for understanding natural speech flow
    """
    try:
        # Get file path from ID
        input_path = file_manager.resolve_id(file_id)
        if not input_path:
            return {
                "success": False,
                "error": f"File with ID '{file_id}' not found"
            }
        
        # Get insights from cached analysis
        insights = speech_detector.get_speech_insights(input_path)
        
        return insights
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get speech insights: {str(e)}"
        }


@mcp.tool()
async def analyze_composition_sources(source_filenames: List[str], force_reanalysis: bool = False) -> Dict[str, Any]:
    """
    Analyze multiple video sources for intelligent composition planning.
    
    This tool performs comprehensive analysis of video files to determine optimal processing strategies:
    - Enhanced speech detection with cut point identification
    - Content quality assessment and visual complexity analysis
    - Processing strategy recommendations (time-stretch vs smart-cut vs hybrid)
    - Priority scoring for source ordering in compositions
    
    Args:
        source_filenames: List of video filenames to analyze
        force_reanalysis: Force fresh analysis, ignore cache (default: False)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating analysis completion
        - analyzed_sources: List of source analysis results
        - recommendations: Processing strategy recommendations
        - priority_order: Suggested ordering by quality/speech importance
        
    Example Usage:
        analyze_composition_sources(["intro.mp4", "speech_video.mp4", "outro.mp4"])
    """
    try:
        analyzed_sources = []
        
        for i, filename in enumerate(source_filenames):
            
            # Get file ID and path
            file_id = file_manager.get_id_by_name(filename)
            if not file_id:
                continue
            
            file_path = file_manager.resolve_id(file_id)
            
            # Enhanced speech analysis
            speech_analysis = await enhanced_speech_analyzer.analyze_video_for_composition(
                file_path, force_reanalysis=force_reanalysis
            )
            
            if not speech_analysis["success"]:
                continue
            
            # Content analysis
            content_analysis = await content_analyzer.analyze_video_content(file_id)
            
            # Determine processing strategy
            has_speech = speech_analysis["has_speech"]
            speech_quality = speech_analysis["quality_metrics"]["overall_quality"]
            
            if not has_speech:
                strategy = "time_stretch"
            elif speech_quality > 0.8:
                strategy = "smart_cut"
            elif speech_quality > 0.5:
                strategy = "hybrid"
            else:
                strategy = "minimal_stretch"
            
            # Calculate priority score
            priority_score = 0.5
            if has_speech:
                priority_score += speech_quality * 0.3
            priority_score += content_analysis.get("overall_score", 0.5) * 0.2
            priority_score = min(1.0, priority_score)
            
            source_result = {
                "filename": filename,
                "file_id": file_id,
                "duration": speech_analysis["video_duration"],
                "has_speech": has_speech,
                "speech_quality": speech_quality if has_speech else 0.0,
                "content_score": content_analysis.get("overall_score", 0.5),
                "recommended_strategy": strategy,
                "priority_score": priority_score,
                "speech_segments": speech_analysis.get("speech_segments", []),
                "cut_points": speech_analysis.get("cut_points", []),
                "cut_strategies": speech_analysis.get("cut_strategies", [])
            }
            
            analyzed_sources.append(source_result)
        
        # Sort by priority score
        analyzed_sources.sort(key=lambda s: s["priority_score"], reverse=True)
        
        # Generate overall recommendations
        recommendations = {
            "total_sources": len(analyzed_sources),
            "sources_with_speech": sum(1 for s in analyzed_sources if s["has_speech"]),
            "high_priority_sources": sum(1 for s in analyzed_sources if s["priority_score"] > 0.8),
            "suggested_composition_order": [s["filename"] for s in analyzed_sources],
            "processing_strategies": {
                s["filename"]: s["recommended_strategy"] for s in analyzed_sources
            }
        }
        
        return {
            "success": True,
            "analyzed_sources": analyzed_sources,
            "recommendations": recommendations,
            "priority_order": [s["filename"] for s in analyzed_sources]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def generate_composition_plan(
    source_filenames: List[str], 
    background_music: str,
    total_duration: float = 24.0,
    bpm: int = 120,
    composition_title: str = "Intelligent Composition",
    force_reanalysis: bool = False
) -> Dict[str, Any]:
    """
    Generate intelligent composition plan with speech-aware processing strategies.
    
    This tool creates a comprehensive komposition-plan.json that intelligently handles:
    - Speech preservation with natural cut points
    - Time allocation based on beat synchronization
    - Audio mixing strategies for speech + music
    - Effects chain optimization
    - Processing workflow with estimated timings
    
    Args:
        source_filenames: List of video filenames for composition
        background_music: Background music filename
        total_duration: Total composition duration in seconds (default: 24.0)
        bpm: Beats per minute for synchronization (default: 120)
        composition_title: Title for the composition (default: "Intelligent Composition")
        force_reanalysis: Force fresh analysis of sources (default: False)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating plan generation success
        - composition_plan: Complete komposition-plan JSON structure
        - plan_file_path: Path to saved plan file
        - processing_summary: Summary of planned operations
        
    Example Usage:
        generate_composition_plan(
            ["intro.mp4", "speech_segment.mp4", "outro.mp4"],
            "background_music.mp3",
            total_duration=30.0,
            bpm=120
        )
    """
    try:
        # Generate composition plan using the planner engine
        composition_plan = await composition_planner.create_composition_plan(
            sources=source_filenames,
            background_music=background_music,
            total_duration=total_duration,
            bpm=bpm,
            composition_title=composition_title,
            force_reanalysis=force_reanalysis
        )
        
        if not composition_plan.get("success", False):
            return composition_plan
        
        # Create processing summary
        segments = composition_plan.get("composition", {}).get("segments", [])
        processing_summary = {
            "total_segments": len(segments),
            "speech_segments": sum(1 for s in segments if s.get("strategy", {}).get("preserve_speech_pitch", False)),
            "time_stretch_segments": sum(1 for s in segments if s.get("strategy", {}).get("type") == "time_stretch"),
            "smart_cut_segments": sum(1 for s in segments if s.get("strategy", {}).get("type") == "smart_cut"),
            "estimated_processing_time": len(segments) * 60,  # 1 minute per segment estimate
            "audio_overlays": len([s for s in segments if s.get("audio_handling", {}).get("extracted_audio")])
        }
        
        return {
            "success": True,
            "composition_plan": composition_plan,
            "plan_file_path": str(composition_planner.cache_dir / f"composition_plan_latest.json"),
            "processing_summary": processing_summary
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate composition plan: {str(e)}"
        }


@mcp.tool()
async def process_composition_plan(plan_file_path: str) -> Dict[str, Any]:
    """
    Execute an intelligent composition plan with speech-aware processing.
    
    This tool processes a komposition-plan.json file created by generate_composition_plan():
    - Executes speech-aware cutting strategies
    - Preserves natural speech pitch where specified
    - Creates time-stretched video segments for beat synchronization
    - Extracts and processes speech audio separately
    - Generates audio timing manifest for external mixing
    
    Args:
        plan_file_path: Path to komposition-plan.json file
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating processing completion
        - output_files: List of generated files with descriptions
        - audio_manifest: Audio timing information for external mixing
        - processing_log: Detailed log of operations performed
        
    Example Usage:
        process_composition_plan("composition_plan_latest.json")
    """
    try:
        print(f"🎬 PROCESSING INTELLIGENT COMPOSITION PLAN")
        
        # Load plan file
        plan_path = Path(plan_file_path)
        if not plan_path.is_absolute():
            plan_path = composition_planner.cache_dir / plan_file_path
        
        if not plan_path.exists():
            return {
                "success": False,
                "error": f"Plan file not found: {plan_file_path}"
            }
        
        with open(plan_path, 'r') as f:
            plan = json.load(f)
        
        if not plan.get("success", False):
            return {
                "success": False,
                "error": "Invalid composition plan"
            }
        
        segments = plan.get("composition", {}).get("segments", [])
        sources = plan.get("sources", {}).get("videos", [])
        audio_plan = plan.get("audio_plan", {})
        
        print(f"   📊 Processing {len(segments)} segments")
        
        # Create processing log
        processing_log = []
        output_files = []
        
        # Process each segment according to its strategy
        for i, segment in enumerate(segments):
            segment_id = segment["id"]
            source_id = segment["source_id"]
            strategy = segment["strategy"]
            cutting = segment["cutting"]
            audio_handling = segment["audio_handling"]
            
            print(f"\n   🎬 Processing {segment_id} ({strategy['type']})")
            
            # Find source file
            source_file = None
            for src in sources:
                if src["id"] == source_id:
                    source_file = src["file"]
                    break
            
            if not source_file:
                error_msg = f"Source file not found for {source_id}"
                processing_log.append({"segment": segment_id, "error": error_msg})
                continue
            
            # Get file ID
            file_id = file_manager.get_id_by_name(source_file)
            if not file_id:
                error_msg = f"File ID not found for {source_file}"
                processing_log.append({"segment": segment_id, "error": error_msg})
                continue
            
            try:
                # Process based on strategy type
                if strategy["type"] == "time_stretch":
                    # Time-stretch entire video
                    stretch_factor = strategy.get("stretch_factor", 1.0)
                    target_duration = cutting["resulting_duration"]
                    
                    # Create time-stretched segment
                    result = await process_file(
                        input_file_id=file_id,
                        operation="trim",
                        output_extension="mp4",
                        params=f"start={cutting['source_start']} duration={target_duration}"
                    )
                    
                    if result["success"]:
                        segment_file_id = result["output_file_id"]
                        output_files.append({
                            "file_id": segment_file_id,
                            "description": f"Time-stretched segment: {segment_id}",
                            "type": "video_segment"
                        })
                        processing_log.append({
                            "segment": segment_id,
                            "operation": "time_stretch",
                            "success": True,
                            "output_file_id": segment_file_id
                        })
                    
                elif strategy["type"] == "smart_cut":
                    # Smart cut preserving speech
                    cut_start = cutting["source_start"]
                    cut_end = cutting["source_end"]
                    duration = cut_end - cut_start
                    
                    # Extract segment using natural cut points
                    result = await process_file(
                        input_file_id=file_id,
                        operation="trim",
                        output_extension="mp4",
                        params=f"start={cut_start} duration={duration}"
                    )
                    
                    if result["success"]:
                        segment_file_id = result["output_file_id"]
                        output_files.append({
                            "file_id": segment_file_id,
                            "description": f"Smart-cut segment: {segment_id} (speech preserved)",
                            "type": "video_segment"
                        })
                        
                        # Extract speech audio if needed
                        if audio_handling.get("extracted_audio"):
                            speech_result = await process_file(
                                input_file_id=segment_file_id,
                                operation="extract_audio",
                                output_extension="wav",
                                params=""
                            )
                            
                            if speech_result["success"]:
                                speech_file_id = speech_result["output_file_id"]
                                output_files.append({
                                    "file_id": speech_file_id,
                                    "description": f"Extracted speech: {segment_id}",
                                    "type": "speech_audio"
                                })
                        
                        processing_log.append({
                            "segment": segment_id,
                            "operation": "smart_cut",
                            "success": True,
                            "output_file_id": segment_file_id,
                            "speech_preserved": True
                        })
                
            except Exception as e:
                processing_log.append({
                    "segment": segment_id,
                    "error": str(e),
                    "success": False
                })
                continue
        
        # Generate audio timing manifest
        audio_manifest = {
            "background_music": audio_plan.get("background_music", {}),
            "speech_overlays": audio_plan.get("speech_overlays", []),
            "timeline": plan.get("timeline", {}),
            "instructions": [
                "1. Load background music for full duration",
                "2. Insert speech overlays at specified times",
                "3. Mix with specified volume levels",
                "4. Export final audio track"
            ]
        }
        
        success_count = sum(1 for log in processing_log if log.get("success", False))
        
        print(f"\n✅ PROCESSING COMPLETE: {success_count}/{len(segments)} segments successful")
        
        return {
            "success": success_count > 0,
            "output_files": output_files,
            "audio_manifest": audio_manifest,
            "processing_log": processing_log,
            "segments_processed": success_count,
            "total_segments": len(segments)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process composition plan: {str(e)}"
        }


@mcp.tool()
async def preview_composition_timing(
    source_filenames: List[str],
    total_duration: float = 24.0,
    bpm: int = 120
) -> Dict[str, Any]:
    """
    Preview timing allocation for composition without full processing.
    
    This tool provides a quick preview of how sources will be allocated in time slots:
    - Shows time slot assignments based on BPM
    - Estimates processing strategies for each source
    - Identifies potential timing conflicts or issues
    - Provides recommendations before full processing
    
    Args:
        source_filenames: List of video filenames
        total_duration: Total composition duration in seconds (default: 24.0)
        bpm: Beats per minute for synchronization (default: 120)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating preview generation success
        - timing_preview: Time slot allocations and strategies
        - recommendations: Suggestions for optimization
        - estimated_processing_time: Predicted processing duration
    """
    try:
        print(f"⏰ PREVIEWING COMPOSITION TIMING")
        
        # Calculate time slots
        seconds_per_beat = 60.0 / bpm
        beats_per_measure = 16  # Standard for compositions
        slot_duration = seconds_per_beat * beats_per_measure
        
        time_slots = []
        current_time = 0.0
        
        for i in range(len(source_filenames)):
            if current_time >= total_duration:
                break
                
            end_time = min(current_time + slot_duration, total_duration)
            
            time_slots.append({
                "slot_number": i + 1,
                "source_file": source_filenames[i] if i < len(source_filenames) else None,
                "start_time": current_time,
                "end_time": end_time,
                "duration": end_time - current_time,
                "beat_start": int(current_time / seconds_per_beat),
                "beat_end": int(end_time / seconds_per_beat)
            })
            
            current_time = end_time
        
        # Get basic file info for strategy estimation
        timing_preview = []
        total_processing_estimate = 0
        
        for slot in time_slots:
            if not slot["source_file"]:
                continue
                
            file_id = file_manager.get_id_by_name(slot["source_file"])
            if not file_id:
                slot_info = {
                    **slot,
                    "strategy": "unknown",
                    "issue": "File not found",
                    "processing_time_estimate": 0
                }
            else:
                # Quick analysis for strategy estimation
                file_path = file_manager.resolve_id(file_id)
                
                # Estimate strategy based on filename and basic analysis
                if "speech" in slot["source_file"].lower() or "talk" in slot["source_file"].lower():
                    strategy = "smart_cut"
                    processing_time = 120  # 2 minutes for speech processing
                else:
                    strategy = "time_stretch"
                    processing_time = 60   # 1 minute for time stretching
                
                slot_info = {
                    **slot,
                    "strategy": strategy,
                    "processing_time_estimate": processing_time,
                    "note": f"Will use {strategy} processing"
                }
                
                total_processing_estimate += processing_time
            
            timing_preview.append(slot_info)
        
        # Generate recommendations
        recommendations = []
        
        if len(source_filenames) > len(time_slots):
            recommendations.append({
                "type": "warning",
                "message": f"Too many sources ({len(source_filenames)}) for duration ({total_duration}s). Only first {len(time_slots)} will be used."
            })
        
        if total_processing_estimate > 300:  # > 5 minutes
            recommendations.append({
                "type": "info",
                "message": f"Estimated processing time: {total_processing_estimate/60:.1f} minutes. Consider processing in smaller batches."
            })
        
        speech_sources = sum(1 for slot in timing_preview if slot.get("strategy") == "smart_cut")
        if speech_sources > 0:
            recommendations.append({
                "type": "info",
                "message": f"{speech_sources} sources detected as speech content. These will preserve natural pitch."
            })
        
        print(f"✅ TIMING PREVIEW COMPLETE: {len(timing_preview)} slots allocated")
        
        return {
            "success": True,
            "timing_preview": timing_preview,
            "recommendations": recommendations,
            "estimated_processing_time": total_processing_estimate,
            "total_duration": total_duration,
            "beats_per_minute": bpm,
            "slot_duration": slot_duration
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to preview composition timing: {str(e)}"
        }


@mcp.tool()
async def generate_komposition_from_description(
    description: str,
    title: str = "Generated Composition",
    custom_bpm: Optional[int] = None,
    custom_resolution: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate komposition.json from natural language description.
    
    This tool creates a complete komposition structure from text descriptions like:
    - "Create a 135 BPM music video with intro, speech segment, and outro"
    - "Make a 600x800 portrait video with lookin.mp4 and panning video" 
    - "Build composition from beat 32-48 with fade transitions"
    
    Args:
        description: Natural language description of desired composition
        title: Title for the generated composition (default: "Generated Composition")
        custom_bpm: Override BPM (parsed from description if not provided)
        custom_resolution: Override resolution like "600x800" (parsed from description if not provided)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating generation success
        - komposition: Complete komposition.json structure
        - komposition_file: Path to saved komposition file
        - intent: Parsed user intent and requirements
        - summary: Generation summary with segments, effects, duration
        
    Example Usage:
        generate_komposition_from_description(
            "Create a 135 BPM music video with PXL intro, lookin speech segment, and panning outro. Make it 600x800 format.",
            title="Custom Music Video"
        )
    """
    try:
        print(f"🤖 GENERATING KOMPOSITION FROM DESCRIPTION")
        
        # Get available source files
        available_sources = komposition_generator.get_available_sources()
        print(f"   📂 Available sources: {len(available_sources)} files")
        
        # Generate komposition
        result = await komposition_generator.generate_from_description(
            description=description,
            title=title,
            available_sources=available_sources
        )
        
        if not result["success"]:
            return result
        
        # Apply custom overrides if provided
        komposition = result["komposition"]
        
        if custom_bpm:
            komposition["metadata"]["bpm"] = custom_bpm
            # Recalculate duration
            total_beats = komposition["metadata"]["totalBeats"]
            komposition["metadata"]["estimatedDuration"] = total_beats * 60 / custom_bpm
            print(f"   🎵 BPM override: {custom_bpm}")
        
        if custom_resolution:
            try:
                width, height = map(int, custom_resolution.split('x'))
                komposition["outputSettings"]["resolution"] = f"{width}x{height}"
                komposition["outputSettings"]["aspectRatio"] = f"{width}:{height}"
                print(f"   📐 Resolution override: {width}x{height}")
            except ValueError:
                print(f"   ⚠️ Invalid resolution format: {custom_resolution}")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate komposition from description: {str(e)}"
        }


@mcp.tool()
async def create_build_plan_from_komposition(
    komposition_file: str,
    render_start_beat: Optional[int] = None,
    render_end_beat: Optional[int] = None,
    output_resolution: str = "1920x1080",
    custom_bpm: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create detailed build plan from komposition.json with beat-precise calculations.
    
    This tool transforms a komposition.json into a comprehensive build plan containing:
    - File dependency mapping (source → intermediate → final)
    - Beat-precise timing calculations for any BPM
    - Snippet extraction specifications with exact timestamps
    - Effects tree dependency ordering
    - Processing operation sequencing
    - Intermediate file tracking
    
    Args:
        komposition_file: Path to komposition.json file
        render_start_beat: Override start beat (default: use komposition)
        render_end_beat: Override end beat (default: use komposition)
        output_resolution: Target resolution like "1920x1080" or "600x800"
        custom_bpm: Override BPM for timing calculations
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating plan creation success
        - build_plan: Complete build plan with dependencies and execution order
        - build_plan_file: Path to saved build plan file
        - summary: Processing summary with operations, timing, resolution
        
    Example Usage:
        create_build_plan_from_komposition(
            "my_composition.json",
            render_start_beat=32,
            render_end_beat=48,
            output_resolution="600x800"
        )
    """
    try:
        print(f"🏗️ CREATING BUILD PLAN FROM KOMPOSITION")
        
        # Parse resolution
        try:
            width, height = map(int, output_resolution.split('x'))
            resolution_tuple = (width, height)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid resolution format: {output_resolution}"
            }
        
        # Create build plan
        result = await komposition_build_planner.create_build_plan(
            komposition_path=komposition_file,
            render_start_beat=render_start_beat,
            render_end_beat=render_end_beat,
            output_resolution=resolution_tuple,
            custom_bpm=custom_bpm
        )
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create build plan: {str(e)}"
        }


@mcp.tool()
async def validate_build_plan_for_bpms(
    build_plan_file: str,
    test_bpms: List[int] = [120, 135, 140, 100]
) -> Dict[str, Any]:
    """
    Validate build plan calculations for multiple BPM values.
    
    This tool tests build plan timing calculations across different BPMs to ensure:
    - Beat timing calculations are correct
    - Segment durations are reasonable
    - No mathematical errors in time conversions
    - All extractions have valid timing
    
    Args:
        build_plan_file: Path to build plan JSON file
        test_bpms: List of BPM values to test (default: [120, 135, 140, 100])
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating validation completion
        - validation_results: Results for each BPM tested
        - overall_valid: Boolean indicating if all BPMs passed validation
        - error_summary: Summary of any validation errors found
        
    Example Usage:
        validate_build_plan_for_bpms(
            "build_20241206_143022.json",
            test_bpms=[120, 135, 140]
        )
    """
    try:
        print(f"🧪 VALIDATING BUILD PLAN FOR MULTIPLE BPMs")
        
        # Load build plan
        plan_path = Path(build_plan_file)
        if not plan_path.is_absolute():
            plan_path = komposition_build_planner.build_cache_dir / build_plan_file
        
        if not plan_path.exists():
            return {
                "success": False,
                "error": f"Build plan file not found: {build_plan_file}"
            }
        
        # Load and parse build plan
        with open(plan_path, 'r') as f:
            build_plan_data = json.load(f)
        
        # Convert to BuildPlan object for validation
        from komposition_build_planner import BuildPlan, BeatTiming, SnippetExtraction
        
        # Reconstruct beat timing
        beat_timing_data = build_plan_data["beat_timing"]
        beat_timing = BeatTiming(
            bpm=beat_timing_data["bpm"],
            beats_per_measure=beat_timing_data["beats_per_measure"],
            start_beat=beat_timing_data["start_beat"],
            end_beat=beat_timing_data["end_beat"]
        )
        
        # Reconstruct snippet extractions
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
        
        # Create minimal BuildPlan for validation
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
        
        # Validate for multiple BPMs
        validation_results = komposition_build_planner.validate_build_plan_bpm(build_plan, test_bpms)
        
        # Check if all validations passed
        overall_valid = all(result["valid"] for result in validation_results.values())
        
        # Create error summary
        error_summary = []
        for bpm, result in validation_results.items():
            if not result["valid"]:
                error_summary.extend([f"BPM {bpm}: {error}" for error in result["extraction_errors"]])
        
        print(f"✅ VALIDATION COMPLETE: {len([r for r in validation_results.values() if r['valid']])}/{len(test_bpms)} BPMs passed")
        
        return {
            "success": True,
            "validation_results": validation_results,
            "overall_valid": overall_valid,
            "error_summary": error_summary,
            "tested_bpms": test_bpms
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to validate build plan: {str(e)}"
        }


@mcp.tool()
async def generate_and_build_from_description(
    description: str,
    title: str = "Generated Video",
    render_start_beat: Optional[int] = None,
    render_end_beat: Optional[int] = None,
    output_resolution: str = "1920x1080",
    validate_bpms: List[int] = [120, 135]
) -> Dict[str, Any]:
    """
    Complete workflow: Generate komposition from description and create build plan.
    
    This tool combines komposition generation and build planning into a single workflow:
    1. Parses natural language description
    2. Generates complete komposition.json
    3. Creates detailed build plan with dependencies
    4. Validates timing calculations for multiple BPMs
    5. Returns ready-to-execute build specifications
    
    Args:
        description: Natural language description of desired video
        title: Title for the composition
        render_start_beat: Override render start beat
        render_end_beat: Override render end beat  
        output_resolution: Target resolution like "600x800"
        validate_bpms: BPM values to validate (default: [120, 135])
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating complete workflow success
        - komposition: Generated komposition structure
        - build_plan: Complete build plan
        - validation_results: BPM validation results
        - files: Paths to generated komposition and build plan files
        - summary: Complete workflow summary
        
    Example Usage:
        generate_and_build_from_description(
            "Create a 135 BPM music video with lookin speech and panning action. Render from beat 32-48 in 600x800 portrait format with fade transitions.",
            title="Custom Portrait Video"
        )
    """
    try:
        print(f"🚀 COMPLETE WORKFLOW: DESCRIPTION → KOMPOSITION → BUILD PLAN")
        
        # Step 1: Generate komposition from description
        print(f"\n🤖 STEP 1: GENERATING KOMPOSITION")
        komposition_result = await generate_komposition_from_description(
            description=description,
            title=title,
            custom_resolution=output_resolution
        )
        
        if not komposition_result["success"]:
            return {
                "success": False,
                "error": f"Komposition generation failed: {komposition_result.get('error')}"
            }
        
        komposition_file = komposition_result["komposition_file"]
        
        # Step 2: Create build plan
        print(f"\n🏗️ STEP 2: CREATING BUILD PLAN")
        build_plan_result = await create_build_plan_from_komposition(
            komposition_path=komposition_file,
            render_start_beat=render_start_beat,
            render_end_beat=render_end_beat,
            output_resolution=output_resolution
        )
        
        if not build_plan_result["success"]:
            return {
                "success": False,
                "error": f"Build plan creation failed: {build_plan_result.get('error')}"
            }
        
        build_plan_file = build_plan_result["build_plan_file"]
        
        # Step 3: Validate build plan
        print(f"\n🧪 STEP 3: VALIDATING BUILD PLAN")
        validation_result = await validate_build_plan_for_bpms(
            build_plan_file=build_plan_file,
            test_bpms=validate_bpms
        )
        
        if not validation_result["success"]:
            print(f"   ⚠️ Validation failed, but continuing with build plan")
        
        # Compile complete results
        workflow_summary = {
            "komposition_segments": len(komposition_result["komposition"]["segments"]),
            "komposition_effects": len(komposition_result["komposition"]["effects_tree"]),
            "build_plan_operations": build_plan_result["summary"]["total_operations"],
            "estimated_processing_time": build_plan_result["summary"]["estimated_time"],
            "output_resolution": output_resolution,
            "validation_passed": validation_result.get("overall_valid", False),
            "validated_bpms": validate_bpms
        }
        
        print(f"\n🎉 COMPLETE WORKFLOW SUCCESSFUL!")
        print(f"   🎬 {workflow_summary['komposition_segments']} segments")
        print(f"   ✨ {workflow_summary['komposition_effects']} effects")
        print(f"   🔗 {workflow_summary['build_plan_operations']} operations")
        print(f"   ⏱️ Est. processing: {workflow_summary['estimated_processing_time']/60:.1f} minutes")
        print(f"   🧪 BPM validation: {'✅ PASSED' if workflow_summary['validation_passed'] else '⚠️ ISSUES'}")
        
        return {
            "success": True,
            "komposition": komposition_result["komposition"],
            "build_plan": build_plan_result["build_plan"],
            "validation_results": validation_result.get("validation_results", {}),
            "files": {
                "komposition_file": komposition_file,
                "build_plan_file": build_plan_file
            },
            "summary": workflow_summary
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Complete workflow failed: {str(e)}"
        }


@mcp.tool()
async def build_video_from_audio_manifest(
    manifest_file: str = "AUDIO_TIMING_MANIFEST.json",
    execution_strategy: str = "ffmpeg_direct"
) -> Dict[str, Any]:
    """🎵 AUDIO WORKFLOW - Build final video directly from audio timing manifest
    
    Perfect for converting AUDIO_TIMING_MANIFEST.json → final video with proper audio mixing.
    
    This tool handles complex audio timing scenarios:
    - Silent video + background music combination
    - Speech segment timing and volume control  
    - Multiple audio layer mixing
    - Precise timing based on beat synchronization
    
    Args:
        manifest_file: Path to AUDIO_TIMING_MANIFEST.json (default: searches temp directory)
        execution_strategy: "ffmpeg_direct" for direct ffmpeg, "mcp_batch" for MCP operations
    
    Perfect For:
        - Speech-synchronized music videos
        - Complex audio timing scenarios  
        - Multi-layer audio mixing
        - Beat-precise audio placement
    
    Example Manifest Structure:
        {
          "metadata": {
            "silentVideoFile": "/tmp/music/temp/SILENT_VIDEO.mp4",
            "backgroundMusic": "music.mp3"
          },
          "videoSegments": [...speech timing info...],
          "finalAssemblyInstructions": {...mixing steps...}
        }
    
    Next Steps:
        → get_file_info() - Check final video metadata
        → list_generated_files() - See what was created
        → cleanup_temp_files() - Clean up intermediate files
    
    Returns:
        Dictionary with success status, output file info, and processing details
    """
    try:
        print(f"🎵 BUILDING VIDEO FROM AUDIO TIMING MANIFEST")
        
        # Find manifest file
        manifest_path = None
        if manifest_file == "AUDIO_TIMING_MANIFEST.json":
            # Search in temp directory
            temp_dir = Path("/tmp/music/temp")
            manifest_path = temp_dir / manifest_file
            if not manifest_path.exists():
                # Search in metadata directory
                metadata_dir = Path("/tmp/music/metadata")
                manifest_path = metadata_dir / manifest_file
        else:
            manifest_path = Path(manifest_file)
        
        if not manifest_path.exists():
            return {
                "success": False,
                "error": f"Manifest file not found: {manifest_file}"
            }
        
        # Load manifest
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        print(f"📄 Loaded manifest: {manifest['metadata']['title']}")
        print(f"🎬 Duration: {manifest['metadata']['totalDuration']}s")
        
        # Get file paths
        silent_video = Path(manifest['metadata']['silentVideoFile'])
        background_music = Path(f"/tmp/music/source/{manifest['metadata']['backgroundMusic']}")
        
        if not silent_video.exists():
            return {
                "success": False,
                "error": f"Silent video not found: {silent_video}"
            }
        
        if not background_music.exists():
            return {
                "success": False,
                "error": f"Background music not found: {background_music}"
            }
        
        # Generate output filename
        output_file = Path("/tmp/music/temp") / "FINAL_FROM_AUDIO_MANIFEST.mp4"
        
        if execution_strategy == "ffmpeg_direct":
            # Use direct ffmpeg command as we successfully tested
            cmd = [
                "ffmpeg", "-y",
                "-i", str(silent_video),
                "-i", str(background_music),
                "-c:v", "copy",
                "-filter:a", "volume=0.5",
                "-shortest",
                str(output_file)
            ]
            
            # Execute ffmpeg
            result = await ffmpeg.execute_command(cmd)
            
            if result["success"]:
                # Register output file
                output_file_id = file_manager.register_file(output_file)
                
                return {
                    "success": True,
                    "message": f"Successfully built video from audio manifest",
                    "output_file": str(output_file),
                    "output_file_id": output_file_id,
                    "output_size_mb": round(output_file.stat().st_size / (1024*1024), 1),
                    "manifest_processed": str(manifest_path),
                    "execution_strategy": execution_strategy,
                    "processing_summary": {
                        "silent_video": str(silent_video),
                        "background_music": str(background_music),
                        "total_duration": manifest['metadata']['totalDuration'],
                        "segments_processed": len(manifest.get('videoSegments', []))
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"FFmpeg execution failed: {result.get('stderr', 'Unknown error')}"
                }
        
        else:  # mcp_batch strategy
            return {
                "success": False,
                "error": "mcp_batch strategy not yet implemented - use ffmpeg_direct"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to build video from audio manifest: {str(e)}"
        }


@mcp.tool()
async def create_video_from_description(
    description: str,
    title: str = "Generated Video",
    execution_mode: str = "full",  # "full", "plan_only", "preview"
    quality: str = "standard",     # "draft", "standard", "high"
    custom_bpm: Optional[int] = None,
    custom_resolution: Optional[str] = None
) -> Dict[str, Any]:
    """🎬 ATOMIC VIDEO CREATION - Complete video from text description in single call
    
    This is the ULTIMATE workflow tool - combines all steps into one atomic operation:
    1. Parse natural language description with enhanced NLP
    2. Match and analyze available source files
    3. Generate optimized komposition with musical structure recognition
    4. Create and validate build plan with dependency resolution
    5. Execute video processing (if execution_mode="full")
    
    Perfect for: 80% of video creation use cases, rapid prototyping, non-technical users
    
    Parameters:
        description: Natural language description of desired video
        title: Video title (default: "Generated Video")
        execution_mode: 
            - "full": Complete video processing (default)
            - "plan_only": Generate plan but don't process
            - "preview": Quick preview with draft quality
        quality: Processing quality level
            - "draft": Fast processing, lower quality
            - "standard": Balanced quality/speed (default)
            - "high": Maximum quality, slower processing
        custom_bpm: Override detected BPM
        custom_resolution: Override resolution (e.g., "600x800", "1920x1080")
    
    Examples:
        → create_video_from_description("134 BPM music video with smooth transitions")
        → create_video_from_description("Leica-style intro, verse and refrain", execution_mode="plan_only")
        → create_video_from_description("Portrait format dance video", custom_resolution="600x800")
    
    Reduces: 5 calls → 1 call (80% workflow simplification)
    
    Returns:
        Dictionary with complete workflow results, files created, and processing summary
    """
    try:
        
        workflow_start = asyncio.get_event_loop().time()
        workflow_results = {
            "success": True,
            "workflow_steps": [],
            "files_created": [],
            "processing_summary": {},
            "total_time": 0
        }
        
        # Step 1: Enhanced file discovery
        step_start = asyncio.get_event_loop().time()
        
        files_result = await mcp.call_tool('list_files', {})
        files_text = files_result[0].text if files_result and len(files_result) > 0 else '{}'
        files_data = json.loads(files_text)
        
        step_duration = asyncio.get_event_loop().time() - step_start
        workflow_results["workflow_steps"].append({
            "step": "file_discovery",
            "duration": step_duration,
            "files_found": len(files_data.get("files", [])),
            "status": "completed"
        })
        # Step 2: Enhanced komposition generation with musical structure
        step_start = asyncio.get_event_loop().time()
        
        komposition_result = await mcp.call_tool('generate_komposition_from_description', {
            'description': description,
            'title': title,
            'custom_bpm': custom_bpm,
            'custom_resolution': custom_resolution
        })
        
        komposition_text = komposition_result[0].text if komposition_result and len(komposition_result) > 0 else '{}'
        komposition_data = json.loads(komposition_text)
        
        if not komposition_data.get('success'):
            return {
                "success": False,
                "error": f"Komposition generation failed: {komposition_data.get('error')}",
                "workflow_results": workflow_results
            }
        
        komposition_file = komposition_data.get('komposition_file', '')
        workflow_results["files_created"].append(komposition_file)
        
        step_duration = asyncio.get_event_loop().time() - step_start
        workflow_results["workflow_steps"].append({
            "step": "komposition_generation",
            "duration": step_duration,
            "komposition_file": komposition_file,
            "segments": len(komposition_data.get("komposition", {}).get("segments", [])),
            "effects": len(komposition_data.get("komposition", {}).get("effects_tree", [])),
            "status": "completed"
        })
        # Step 3: Optimized build plan creation
        step_start = asyncio.get_event_loop().time()
        
        build_plan_result = await mcp.call_tool('create_build_plan_from_komposition', {
            'komposition_file': komposition_file
        })
        
        build_plan_text = build_plan_result[0].text if build_plan_result and len(build_plan_result) > 0 else '{}'
        build_plan_data = json.loads(build_plan_text)
        
        if not build_plan_data.get('success'):
            return {
                "success": False,
                "error": f"Build plan creation failed: {build_plan_data.get('error')}",
                "workflow_results": workflow_results
            }
        
        build_plan_file = build_plan_data.get('build_plan_file', '')
        workflow_results["files_created"].append(build_plan_file)
        
        step_duration = asyncio.get_event_loop().time() - step_start
        workflow_results["workflow_steps"].append({
            "step": "build_plan_creation",
            "duration": step_duration,
            "build_plan_file": build_plan_file,
            "operations": len(build_plan_data.get("build_plan", {}).get("effect_operations", [])),
            "extractions": len(build_plan_data.get("build_plan", {}).get("snippet_extractions", [])),
            "status": "completed"
        })
        # Step 4: Quick validation
        step_start = asyncio.get_event_loop().time()
        
        validation_result = await mcp.call_tool('validate_build_plan_for_bpms', {
            'build_plan_file': build_plan_file,
            'test_bpms': [120, 134, 140]  # Quick validation set
        })
        
        validation_text = validation_result[0].text if validation_result and len(validation_result) > 0 else '{}'
        validation_data = json.loads(validation_text)
        
        step_duration = asyncio.get_event_loop().time() - step_start
        workflow_results["workflow_steps"].append({
            "step": "validation",
            "duration": step_duration,
            "validation_passed": validation_data.get("overall_valid", False),
            "status": "completed"
        })
        # Step 5: Conditional execution based on mode
        if execution_mode == "full":
            step_start = asyncio.get_event_loop().time()
            
            # Process the komposition
            processing_result = await mcp.call_tool('process_komposition_file', {
                'komposition_path': komposition_file
            })
            
            processing_text = processing_result[0].text if processing_result and len(processing_result) > 0 else '{}'
            processing_data = json.loads(processing_text)
            
            step_duration = asyncio.get_event_loop().time() - step_start
            workflow_results["workflow_steps"].append({
                "step": "video_processing",
                "duration": step_duration,
                "status": "completed" if processing_data.get("success") else "failed",
                "output_files": processing_data.get("output_files", [])
            })
            
            if processing_data.get("success"):
                workflow_results["files_created"].extend(processing_data.get("output_files", []))
            else:
                workflow_results["success"] = False
        
        elif execution_mode == "plan_only":
            workflow_results["workflow_steps"].append({
                "step": "video_processing",
                "duration": 0,
                "status": "skipped",
                "reason": "plan_only mode"
            })
        
        elif execution_mode == "preview":
            # TODO: Implement quick preview processing
            workflow_results["workflow_steps"].append({
                "step": "video_processing",
                "duration": 0,
                "status": "not_implemented",
                "reason": "preview mode not yet implemented"
            })
        
        # Calculate total workflow time
        total_time = asyncio.get_event_loop().time() - workflow_start
        workflow_results["total_time"] = total_time
        
        # Generate processing summary
        workflow_results["processing_summary"] = {
            "description": description,
            "title": title,
            "execution_mode": execution_mode,
            "quality": quality,
            "total_steps": len(workflow_results["workflow_steps"]),
            "total_files_created": len(workflow_results["files_created"]),
            "total_processing_time": total_time,
            "komposition_segments": len(komposition_data.get("komposition", {}).get("segments", [])),
            "komposition_effects": len(komposition_data.get("komposition", {}).get("effects_tree", [])),
            "build_plan_operations": len(build_plan_data.get("build_plan", {}).get("effect_operations", [])),
            "validation_passed": validation_data.get("overall_valid", False)
        }
        
        return workflow_results
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Atomic video creation failed: {str(e)}",
            "workflow_results": workflow_results if 'workflow_results' in locals() else {}
        }


@mcp.tool()
async def get_available_video_effects(category: str = None, provider: str = None) -> Dict[str, Any]:
    """📹 VIDEO EFFECTS - List all available video effects with parameter discovery
    
    This tool provides comprehensive information about available video effects including:
    - Parameter specifications with types, ranges, and defaults
    - Performance estimates and provider information  
    - Category-based filtering for easy discovery
    - Parameter validation rules and constraints
    
    Args:
        category: Filter by effect category ("color", "stylistic", "blur", "distortion", "privacy")
        provider: Filter by provider ("ffmpeg", "opencv", "pil")
    
    Returns:
        Dictionary containing:
        - effects: Complete effect specifications with parameters
        - categories: Available effect categories
        - providers: Available effect providers  
        - effects_count: Total number of available effects
        
    Categories:
        🎨 color: Color grading, curves, film looks (vintage, noir)
        ✨ stylistic: Visual effects (VHS, vignette, neon glow)
        🌫️ blur: Gaussian blur, motion blur variants
        🔀 distortion: Chromatic aberration, glitch effects
        🔒 privacy: Face detection and blurring
        
    Providers:
        🎬 ffmpeg: High-performance native video filters
        👁️ opencv: AI-powered computer vision effects
        🖼️ pil: Image processing effects
        
    Example Usage:
        get_available_video_effects()  # All effects
        get_available_video_effects(category="color")  # Color effects only
        get_available_video_effects(provider="ffmpeg")  # FFmpeg effects only
    """
    try:
        return effect_processor.get_available_effects(category=category, provider=provider)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get available effects: {str(e)}"
        }


@mcp.tool()
async def apply_video_effect(file_id: str, effect_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """📹 VIDEO EFFECTS - Apply single video effect with parameter control
    
    Apply professional video effects to your videos with precise parameter control.
    Each effect preserves audio streams and provides performance estimates.
    
    Args:
        file_id: Source video file ID from list_files()
        effect_name: Effect name from get_available_video_effects()
        parameters: Effect-specific parameters (optional, uses defaults if not provided)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating processing completion
        - output_file_id: New file ID for the processed video
        - processing_time: Actual processing duration
        - effect_applied: Details of the effect and parameters used
        
    Popular Effects:
    
    🎨 Color Effects:
        - vintage_color: Warm nostalgic film look
          Parameters: intensity (0.0-2.0), warmth (-0.5-0.5), saturation (0.0-2.0)
        - film_noir: High contrast black and white  
          Parameters: contrast (1.0-3.0), brightness (-0.5-0.5)
    
    ✨ Stylistic Effects:
        - vhs_look: Retro VHS tape aesthetic
          Parameters: noise_level (0.0-20.0), blur_amount (0.0-2.0), saturation (0.0-2.0)
        - vignette: Dark edges for cinematic feel
          Parameters: angle (0.0-6.28), x0 (0.0-1.0), y0 (0.0-1.0), mode ("forward"/"backward")
    
    🌫️ Blur Effects:  
        - gaussian_blur: Smooth blur effect
          Parameters: sigma (0.1-20.0), steps (1-10)
    
    🔀 Distortion Effects:
        - chromatic_aberration: RGB channel separation
          Parameters: red_offset_x (-10-10), blue_offset_x (-10-10), intensity (0.0-2.0)
    
    🔒 Privacy Effects:
        - face_blur: Automatic face detection and blurring
          Parameters: blur_strength (5.0-50.0), detection_confidence (0.3-0.95)
          
    Example Usage:
        apply_video_effect(
            file_id="file_12345678",
            effect_name="vintage_color",
            parameters={"intensity": 1.2, "warmth": 0.3}
        )
        
        apply_video_effect(
            file_id="file_12345678", 
            effect_name="gaussian_blur",
            parameters={"sigma": 8.0}
        )
    """
    try:
        return await effect_processor.apply_effect(file_id, effect_name, parameters)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply video effect: {str(e)}"
        }


@mcp.tool()
async def apply_video_effect_chain(file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    """📹 VIDEO EFFECTS - Apply multiple effects in sequence with chaining
    
    Stack multiple video effects to create complex looks and styles. Effects are applied
    sequentially, with each effect processing the output of the previous effect.
    
    Args:
        file_id: Source video file ID from list_files()
        effects_chain: List of effect steps, each containing:
            - effect: Effect name from get_available_video_effects()
            - parameters: Effect-specific parameters (optional)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating complete chain processing
        - final_output_file_id: File ID of the final processed video
        - applied_effects: Details of each effect step with output file IDs
        - total_steps: Number of effects applied
        
    Effect Stacking Examples:
    
    🎬 Cinematic Grade:
        [
            {"effect": "vintage_color", "parameters": {"intensity": 0.8, "warmth": 0.2}},
            {"effect": "vignette", "parameters": {"angle": 1.57}},
            {"effect": "gaussian_blur", "parameters": {"sigma": 1.0}}
        ]
    
    📱 Social Media Ready:
        [
            {"effect": "vintage_color", "parameters": {"saturation": 1.3}},
            {"effect": "vhs_look", "parameters": {"noise_level": 3.0}}
        ]
        
    🔒 Privacy Protection:
        [
            {"effect": "face_blur", "parameters": {"blur_strength": 20.0}},
            {"effect": "vintage_color", "parameters": {"intensity": 0.5}}
        ]
        
    🎨 Film Emulation:
        [
            {"effect": "film_noir", "parameters": {"contrast": 1.5}},
            {"effect": "chromatic_aberration", "parameters": {"intensity": 0.3}}
        ]
    
    Performance Notes:
        - Each effect adds processing time (see get_available_video_effects for estimates)
        - Order matters: blur effects should typically come last
        - Color effects work well together when applied in sequence
        - Privacy effects (face_blur) should be applied early in the chain
        
    Example Usage:
        apply_video_effect_chain(
            file_id="file_12345678",
            effects_chain=[
                {"effect": "vintage_color", "parameters": {"intensity": 1.0}},
                {"effect": "vignette", "parameters": {"angle": 1.57}},
                {"effect": "gaussian_blur", "parameters": {"sigma": 2.0}}
            ]
        )
    """
    try:
        return await effect_processor.apply_effect_chain(file_id, effects_chain)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply video effect chain: {str(e)}"
        }


@mcp.tool()
async def suggest_efficient_workflow(goal_description: str, available_files: List[str] = None) -> Dict[str, Any]:
    """🎯 WORKFLOW OPTIMIZATION - Get optimized workflow suggestions to minimize function calls
    
    This tool analyzes your goal and suggests the most efficient combination of MCP tools to achieve it,
    reducing the number of function calls from 20+ down to 3-5 calls by using atomic operations and batch processing.
    
    Args:
        goal_description: What you want to create (e.g., "music video with effects", "batch convert videos")
        available_files: Optional list of file names/IDs you want to work with
    
    Returns:
        Dictionary containing:
        - recommended_workflow: Step-by-step optimized workflow
        - efficiency_score: Estimated function call reduction
        - atomic_functions: Single-call solutions when available
        - batch_operations: Multi-step operations in minimal calls
        - fallback_manual: Manual step-by-step if atomic functions fail
    
    Efficiency Examples:
        Instead of: 25+ individual calls
        Use: 3-5 optimized calls with batch_process() and atomic functions
        
        Instead of: apply_video_effect() → apply_video_effect() → apply_video_effect()
        Use: apply_video_effect_chain() - single call for multiple effects
        
        Instead of: Individual trim/resize/audio operations
        Use: batch_process() with OUTPUT_PREVIOUS chaining
    
    Goal Types Optimized:
        🎬 "Create music video" → create_video_from_description() (1 call)
        ✨ "Apply multiple effects" → apply_video_effect_chain() (1 call)  
        🔗 "Multi-step processing" → batch_process() (1 call)
        📱 "Social media format" → Optimized resize + effects batch
        🎵 "Add music to videos" → Audio workflow with minimal steps
    """
    try:
        goal = goal_description.lower()
        
        # Analyze goal and suggest optimal workflow
        if any(keyword in goal for keyword in ['music video', 'create video', 'video from']):
            return {
                "success": True,
                "recommended_workflow": "atomic_single_call",
                "efficiency_score": "95% reduction (25+ calls → 1 call)",
                "atomic_functions": [
                    {
                        "function": "create_video_from_description",
                        "description": "Single atomic call for complete video creation",
                        "parameters": {
                            "description": goal_description,
                            "title": "Generated Video",
                            "execution_mode": "full"
                        },
                        "why_efficient": "Combines file discovery, komposition generation, build planning, and processing in one call"
                    }
                ],
                "fallback_manual": [
                    "1. list_files() - discover available media",
                    "2. generate_komposition_from_description() - create structure", 
                    "3. process_komposition_file() - execute creation"
                ],
                "estimated_calls": 1,
                "efficiency_tips": [
                    "Use execution_mode='plan_only' to preview without processing",
                    "Add custom_resolution='600x800' for social media formats",
                    "Include BPM and effects in description for better results"
                ]
            }
            
        elif any(keyword in goal for keyword in ['effects', 'filter', 'apply', 'style']):
            return {
                "success": True,
                "recommended_workflow": "effect_chain_batch",
                "efficiency_score": "80% reduction (10+ calls → 2 calls)",
                "atomic_functions": [
                    {
                        "function": "get_available_video_effects",
                        "description": "Discover all effects and parameters",
                        "parameters": {},
                        "why_efficient": "Single call to see all 12 effects with parameter specs"
                    },
                    {
                        "function": "apply_video_effect_chain",
                        "description": "Apply multiple effects in one operation",
                        "parameters": {
                            "file_id": "target_file_id",
                            "effects_chain": [
                                {"effect": "vintage_color", "parameters": {"intensity": 1.0}},
                                {"effect": "vignette", "parameters": {"angle": 1.57}}
                            ]
                        },
                        "why_efficient": "Chains multiple effects without intermediate files"
                    }
                ],
                "batch_operations": [
                    {
                        "description": "If you need different effects on different files",
                        "use": "batch_process with video effects operations"
                    }
                ],
                "estimated_calls": 2,
                "popular_effect_chains": {
                    "cinematic": ["vintage_color", "vignette", "gaussian_blur"],
                    "social_media": ["social_media_pack", "warm_cinematic"],
                    "retro": ["vhs_look", "chromatic_aberration"],
                    "professional": ["film_noir", "dreamy_soft"]
                }
            }
            
        elif any(keyword in goal for keyword in ['batch', 'multiple', 'convert', 'resize']):
            return {
                "success": True,
                "recommended_workflow": "batch_processing",
                "efficiency_score": "90% reduction (20+ calls → 2-3 calls)",
                "atomic_functions": [
                    {
                        "function": "batch_process",
                        "description": "Process multiple operations with OUTPUT_PREVIOUS chaining",
                        "parameters": {
                            "operations": [
                                {"input_file_id": "file_123", "operation": "trim", "output_extension": "mp4", "params": "start=0 duration=10"},
                                {"input_file_id": "OUTPUT_PREVIOUS", "operation": "resize", "output_extension": "mp4", "params": "width=1920 height=1080"},
                                {"input_file_id": "OUTPUT_PREVIOUS", "operation": "to_mp3", "output_extension": "mp3"}
                            ]
                        },
                        "why_efficient": "Chains multiple operations atomically with proper file passing"
                    }
                ],
                "chaining_tips": [
                    "Use 'OUTPUT_PREVIOUS' as input_file_id to chain operations",
                    "Each operation processes the output of the previous one",
                    "Batch stops on first failure with detailed error reporting",
                    "Final output file_id returned for further processing"
                ],
                "estimated_calls": 1,
                "common_chains": {
                    "social_media_prep": ["trim", "resize", "to_mp3"],
                    "quality_improve": ["normalize_audio", "convert", "resize"],
                    "format_standardize": ["convert", "resize", "extract_audio"]
                }
            }
            
        else:
            # General workflow optimization
            return {
                "success": True,
                "recommended_workflow": "optimized_general",
                "efficiency_score": "70% reduction (15+ calls → 4-5 calls)",
                "general_principles": [
                    "1. Always start with list_files() to see available media and get smart suggestions",
                    "2. Use atomic functions when available (create_video_from_description, apply_video_effect_chain)",
                    "3. Use batch_process() for multi-step operations with OUTPUT_PREVIOUS chaining",
                    "4. Use list_generated_files() to track outputs and cleanup_temp_files() to clean up",
                    "5. Prefer single comprehensive calls over multiple individual operations"
                ],
                "atomic_first_strategy": [
                    "Try create_video_from_description() for video creation goals",
                    "Try apply_video_effect_chain() for multiple effects",
                    "Try batch_process() for multi-step workflows"
                ],
                "manual_fallback": [
                    "If atomic functions fail, use individual process_file() calls",
                    "Chain outputs manually: output_file_id from step 1 → input_file_id for step 2",
                    "Always verify success before proceeding to next step"
                ],
                "estimated_calls": "4-5 vs 15-25 manual calls"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate workflow suggestions: {str(e)}"
        }


@mcp.tool()
async def estimate_effect_processing_time(file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    """📹 VIDEO EFFECTS - Estimate processing time for effects chain
    
    Get accurate processing time estimates before applying effects. Helps with planning
    batch operations and understanding performance impact of different effect combinations.
    
    Args:
        file_id: Source video file ID to analyze
        effects_chain: List of effect steps to estimate (same format as apply_video_effect_chain)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating estimation completion
        - video_duration: Duration of source video in seconds
        - total_estimated_time: Total processing time estimate in seconds
        - effect_estimates: Per-effect processing estimates with performance tiers
        - time_per_effect: Average time per effect
        
    Performance Tiers:
        🚀 fast: Real-time or near real-time processing (< 1s per video second)
        ⚡ medium: Moderate processing time (1-5s per video second)  
        🐌 slow: Intensive processing (> 5s per video second)
        
    Estimation Factors:
        - Video duration and resolution
        - Effect complexity and provider (FFmpeg vs OpenCV vs PIL)
        - Hardware capabilities (CPU vs GPU acceleration where available)
        - Parameter settings (higher blur = longer processing)
        
    Use Cases:
        - Plan batch processing workflows
        - Compare different effect combinations
        - Estimate completion times for long videos
        - Optimize effect order for better performance
        
    Example Usage:
        estimate_effect_processing_time(
            file_id="file_12345678", 
            effects_chain=[
                {"effect": "vintage_color"},
                {"effect": "gaussian_blur", "parameters": {"sigma": 10.0}},
                {"effect": "face_blur"}
            ]
        )
    """
    try:
        return effect_processor.estimate_processing_time(file_id, effects_chain)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to estimate processing time: {str(e)}"
        }


@mcp.tool()
async def analyze_video_formats(file_ids: List[str]) -> Dict[str, Any]:
    """
    Analyze aspect ratios of multiple videos and suggest optimal target format.
    
    Args:
        file_ids: List of file IDs to analyze
        
    Returns:
        Dictionary with format analysis and recommendations
    """
    try:
        analyses = []
        for file_id in file_ids:
            file_path = file_manager.resolve_id(file_id)
            analysis = format_manager.analyze_video_format(file_path, file_id)
            analyses.append({
                "file_id": file_id,
                "resolution": f"{analysis.width}x{analysis.height}",
                "aspect_ratio": f"{analysis.aspect_ratio:.2f}",
                "orientation": analysis.orientation,
                "suggested_crop_mode": analysis.suggested_crop_mode.value,
                "crop_compatibility": analysis.crop_compatibility
            })
        
        # Get format suggestion
        video_analyses = [format_manager.analyze_video_format(file_manager.resolve_id(fid), fid) for fid in file_ids]
        suggested_format = format_manager.suggest_target_format(video_analyses)
        
        return {
            "success": True,
            "video_analyses": analyses,
            "suggested_format": {
                "aspect_ratio": suggested_format.aspect_ratio.display_name,
                "resolution": f"{suggested_format.width}x{suggested_format.height}",
                "orientation": suggested_format.orientation,
                "crop_mode": suggested_format.crop_mode.value
            },
            "common_presets": {name: {
                "aspect_ratio": preset.aspect_ratio.display_name,
                "resolution": f"{preset.width}x{preset.height}",
                "crop_mode": preset.crop_mode.value
            } for name, preset in COMMON_PRESETS.items()}
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to analyze video formats: {str(e)}"
        }


@mcp.tool()
async def preview_format_conversion(
    file_id: str, 
    target_format: str, 
    crop_mode: str = "center_crop",
    timestamp: float = 5.0
) -> Dict[str, Any]:
    """
    Generate preview image showing how video will be cropped/fitted to target format.
    
    Args:
        file_id: ID of the source video
        target_format: Target format preset name or "custom"
        crop_mode: Cropping strategy (center_crop, scale_letterbox, scale_blur_bg, etc.)
        timestamp: Time in seconds to extract preview frame
        
    Returns:
        Dictionary with preview image path and conversion details
    """
    try:
        from .format_manager import CropMode, FormatSpec, AspectRatio
    except ImportError:
        from format_manager import CropMode, FormatSpec, AspectRatio
        
        # Get target format specification
        if target_format in COMMON_PRESETS:
            format_spec = COMMON_PRESETS[target_format]
        else:
            # Default format
            format_spec = COMMON_PRESETS["youtube_landscape"]
        
        # Override crop mode if specified
        try:
            crop_mode_enum = CropMode(crop_mode)
            format_spec = FormatSpec(format_spec.aspect_ratio, format_spec.resolution, crop_mode_enum)
        except ValueError:
            pass  # Use default crop mode
        
        # Generate preview
        file_path = file_manager.resolve_id(file_id)
        preview_path = format_manager.generate_preview_frame(file_path, format_spec, timestamp)
        
        # Get conversion analysis
        analysis = format_manager.analyze_video_format(file_path, file_id)
        conversion_plan = format_manager.create_format_conversion_plan([analysis], format_spec)
        
        return {
            "success": True,
            "preview_image": preview_path,
            "conversion_details": conversion_plan["video_conversions"][0],
            "quality_estimate": conversion_plan["estimated_quality_loss"],
            "warnings": conversion_plan["warnings"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to generate preview: {str(e)}"
        }


@mcp.tool()
async def create_format_conversion_plan(
    file_ids: List[str],
    target_format: str = "auto",
    crop_mode: str = "auto"
) -> Dict[str, Any]:
    """
    Create detailed plan for converting multiple videos to consistent target format.
    
    Args:
        file_ids: List of video file IDs to convert
        target_format: Target format preset ("youtube_landscape", "instagram_square", etc.) or "auto"
        crop_mode: Cropping strategy or "auto" for intelligent selection
        
    Returns:
        Complete conversion plan with FFmpeg commands and quality estimates
    """
    try:
        from .format_manager import CropMode, FormatSpec
    except ImportError:
        from format_manager import CropMode, FormatSpec
        
        # Analyze all videos
        video_analyses = []
        for file_id in file_ids:
            file_path = file_manager.resolve_id(file_id)
            analysis = format_manager.analyze_video_format(file_path, file_id)
            video_analyses.append(analysis)
        
        # Determine target format
        if target_format == "auto":
            format_spec = format_manager.suggest_target_format(video_analyses)
        elif target_format in COMMON_PRESETS:
            format_spec = COMMON_PRESETS[target_format]
        else:
            format_spec = COMMON_PRESETS["youtube_landscape"]  # Fallback
        
        # Override crop mode if specified
        if crop_mode != "auto":
            try:
                crop_mode_enum = CropMode(crop_mode)
                format_spec = FormatSpec(format_spec.aspect_ratio, format_spec.resolution, crop_mode_enum)
            except ValueError:
                pass  # Use default crop mode
        
        # Create detailed conversion plan
        conversion_plan = format_manager.create_format_conversion_plan(video_analyses, format_spec)
        
        return {
            "success": True,
            "conversion_plan": conversion_plan,
            "execution_ready": True,
            "estimated_processing_time": len(file_ids) * 30  # Rough estimate
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create conversion plan: {str(e)}"
        }


@mcp.tool()
async def get_format_presets() -> Dict[str, Any]:
    """
    Get list of available format presets for different platforms and use cases.
    
    Returns:
        Dictionary of format presets with their specifications
    """
    try:
        presets = {}
        for name, preset in COMMON_PRESETS.items():
            presets[name] = {
                "name": name,
                "aspect_ratio": preset.aspect_ratio.display_name,
                "resolution": f"{preset.width}x{preset.height}",
                "orientation": preset.orientation,
                "crop_mode": preset.crop_mode.value,
                "description": {
                    "youtube_landscape": "Standard YouTube video format (16:9 landscape)",
                    "instagram_square": "Instagram square post format (1:1)",
                    "instagram_story": "Instagram Story/Reels format (9:16 portrait)",
                    "tiktok_vertical": "TikTok vertical video format (9:16 portrait)",
                    "twitter_landscape": "Twitter video format (16:9 landscape)",
                    "facebook_square": "Facebook square video format (1:1)",
                    "cinema_wide": "Cinematic widescreen format (21:9)"
                }.get(name, f"Format preset: {name}")
            }
        
        return {
            "success": True,
            "presets": presets,
            "crop_modes": {
                "center_crop": "Crop from center, losing edges (good for symmetric content)",
                "smart_crop": "AI-detected focal point cropping (best quality, slower)",
                "scale_letterbox": "Fit with black bars (preserves all content)",
                "scale_blur_bg": "Fit with blurred background (popular for social media)",
                "scale_stretch": "Stretch to fit (may distort, not recommended)",
                "top_crop": "Crop from top (good for portraits with people)",
                "bottom_crop": "Crop from bottom"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get format presets: {str(e)}"
        }


# Audio Effects Tools

@mcp.tool()
async def get_available_audio_effects(category: Optional[str] = None) -> Dict[str, Any]:
    """🎵 AUDIO EFFECTS - List all available audio effects with parameter discovery
    
    This tool provides comprehensive information about available audio effects including:
    - Parameter specifications with types, ranges, and defaults
    - Performance estimates and provider information  
    - Category-based filtering for easy discovery
    - Parameter validation rules and constraints
    
    Args:
        category: Filter by effect category ("eq", "dynamics", "loudness", "spatial", "filter")
    
    Returns:
        Dictionary containing:
        - effects: Complete effect specifications with parameters
        - categories: Available effect categories
        - effects_count: Total number of available effects
        
    Categories:
        🎛️ eq: Equalizers and frequency shaping
        🎚️ dynamics: Compressors, limiters, gates
        📊 loudness: LUFS normalization and metering
        🌊 spatial: Stereo width and positioning
        🔊 filter: High-pass, low-pass, band filters
        
    Example Usage:
        get_available_audio_effects()  # All effects
        get_available_audio_effects(category="dynamics")  # Compressors/limiters only
    """
    try:
        return audio_effect_processor.get_available_effects(category=category)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get available audio effects: {str(e)}"
        }


@mcp.tool()
async def apply_audio_effect(file_id: str, effect_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """🎵 AUDIO EFFECTS - Apply single audio effect with parameter control
    
    Apply professional audio effects to your audio files with precise parameter control.
    Each effect preserves original quality and provides performance estimates.
    
    Args:
        file_id: Source audio/video file ID from list_files()
        effect_name: Effect name from get_available_audio_effects()
        parameters: Effect-specific parameters (optional, uses defaults if not provided)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating processing completion
        - output_file_id: New file ID for the processed audio
        - processing_time: Actual processing duration
        - effect_applied: Details of the effect and parameters used
        
    Popular Audio Effects:
    
    🎛️ EQ Effects:
        - equalizer: Multi-band parametric EQ
          Parameters: bands [{"frequency": Hz, "gain": dB, "q": width}]
        - high_pass_filter: Remove low frequencies
          Parameters: frequency (10-1000 Hz), rolloff (6-48 dB/oct)
    
    🎚️ Dynamics:
        - compressor: Dynamic range control
          Parameters: threshold (-60-0 dB), ratio (1-20), attack/release (ms)
        - limiter: Peak limiting for output control
          Parameters: ceiling (-3-0 dBTP), release (1-1000 ms)
        - de_esser: Sibilance control
          Parameters: frequency (2000-12000 Hz), threshold, ratio
    
    📊 Loudness:
        - loudness_normalize: EBU R128 normalization
          Parameters: target_lufs (-30 to -6), true_peak (-3 to 0)
    
    🌊 Spatial:
        - stereo_widener: Stereo field control
          Parameters: width (0.0-2.0), frequency_range [low, high]
        - mono_bass: Make low frequencies mono
          Parameters: frequency (50-300 Hz)
          
    Example Usage:
        apply_audio_effect(
            file_id="file_12345678",
            effect_name="compressor",
            parameters={"threshold": -18, "ratio": 3.0, "attack": 20, "release": 150}
        )
        
        apply_audio_effect(
            file_id="file_12345678", 
            effect_name="loudness_normalize",
            parameters={"target_lufs": -16, "true_peak": -1.0}
        )
    """
    try:
        return await audio_effect_processor.apply_effect(file_id, effect_name, parameters)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply audio effect: {str(e)}"
        }


@mcp.tool()
async def apply_audio_effect_chain(file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
    """🎵 AUDIO EFFECTS - Apply multiple audio effects in sequence with chaining
    
    Stack multiple audio effects to create professional mastering chains. Effects are applied
    sequentially, with each effect processing the output of the previous effect.
    
    Args:
        file_id: Source audio/video file ID from list_files()
        effects_chain: List of effect steps, each containing:
            - effect: Effect name from get_available_audio_effects()
            - parameters: Effect-specific parameters (optional)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating complete chain processing
        - final_output_file_id: File ID of the final processed audio
        - applied_effects: Details of each effect step with output file IDs
        - total_steps: Number of effects applied
        
    Professional Mastering Chain Examples:
    
    🎸 Rock Mastering:
        [
            {"effect": "high_pass_filter", "parameters": {"frequency": 35}},
            {"effect": "equalizer", "parameters": {"bands": [
                {"frequency": 80, "gain": 1.5, "q": 0.8},
                {"frequency": 2500, "gain": 1.8, "q": 1.0}
            ]}},
            {"effect": "compressor", "parameters": {"threshold": -18, "ratio": 2.5}},
            {"effect": "loudness_normalize", "parameters": {"target_lufs": -9}}
        ]
    
    🎧 EDM Mastering:
        [
            {"effect": "mono_bass", "parameters": {"frequency": 120}},
            {"effect": "compressor", "parameters": {"threshold": -15, "ratio": 4.0}},
            {"effect": "stereo_widener", "parameters": {"width": 1.3}},
            {"effect": "limiter", "parameters": {"ceiling": -1.0}}
        ]
        
    🎤 Podcast Enhancement:
        [
            {"effect": "high_pass_filter", "parameters": {"frequency": 85}},
            {"effect": "de_esser", "parameters": {"frequency": 6500, "threshold": -25}},
            {"effect": "compressor", "parameters": {"threshold": -20, "ratio": 4.0}},
            {"effect": "loudness_normalize", "parameters": {"target_lufs": -16}}
        ]
    
    Performance Notes:
        - Each effect adds processing time (see get_available_audio_effects for estimates)
        - Order matters: filters → EQ → dynamics → loudness normalization
        - Loudness normalization should typically be the final step
        
    Example Usage:
        apply_audio_effect_chain(
            file_id="file_12345678",
            effects_chain=[
                {"effect": "high_pass_filter", "parameters": {"frequency": 80}},
                {"effect": "compressor", "parameters": {"threshold": -18, "ratio": 3.0}},
                {"effect": "loudness_normalize", "parameters": {"target_lufs": -14}}
            ]
        )
    """
    try:
        return await audio_effect_processor.apply_effect_chain(file_id, effects_chain)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply audio effect chain: {str(e)}"
        }


@mcp.tool()
async def apply_audio_template(file_id: str, template_name: str) -> Dict[str, Any]:
    """🎵 AUDIO TEMPLATES - Apply pre-defined or user-created audio effect templates
    
    Apply complete mastering chains using predefined templates for different genres
    and use cases. Templates include professional mastering chains optimized for
    streaming platforms.
    
    Args:
        file_id: Source audio/video file ID from list_files()
        template_name: Template name from list_audio_templates()
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating template application
        - final_output_file_id: File ID of the processed audio
        - template_applied: Template details and effects chain used
        - applied_effects: Details of each processing step
        
    Built-in Templates:
        🎸 rock_mastering: Professional rock mastering for streaming
        🎧 edm_mastering: High-impact EDM mastering with controlled low-end
        🎤 podcast_enhancement: Speech processing for podcasts
        
    Platform Optimization:
        - Templates include LUFS targets for major platforms
        - True peak limiting prevents transcoding distortion
        - Genre-specific EQ and dynamics for optimal sound
        
    Example Usage:
        apply_audio_template(
            file_id="file_12345678",
            template_name="rock_mastering"
        )
    """
    try:
        return await audio_effect_processor.apply_effect_template(file_id, template_name)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to apply audio template: {str(e)}"
        }


@mcp.tool()
async def list_audio_templates() -> Dict[str, Any]:
    """🎵 AUDIO TEMPLATES - List all available audio effect templates
    
    Get all available audio templates including predefined professional templates
    and user-created custom templates.
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating list generation
        - predefined: List of built-in professional templates
        - user: List of user-created custom templates
        - template_count: Total number of templates available
        
    Template Information:
        Each template includes:
        - name: Template display name
        - description: What the template does
        - category: Template type (mastering, speech, etc.)
        - genre: Target music genre or content type
        - target_platforms: Optimized platforms (Spotify, Apple Music, etc.)
        - effects_chain: Complete effects processing chain
        
    Template Locations:
        - Predefined: examples/effect-templates/audio/
        - User: /tmp/music/effect-templates/audio/
        
    Example Usage:
        list_audio_templates()
    """
    try:
        return {
            "success": True,
            **audio_effect_processor.list_effect_templates()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list audio templates: {str(e)}"
        }


@mcp.tool()
async def save_audio_template(template_name: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """🎵 AUDIO TEMPLATES - Save custom audio effect template
    
    Save a custom audio effect template to the user template directory for reuse.
    Templates can be created from successful effect chains or designed from scratch.
    
    Args:
        template_name: Name for the new template (no .yaml extension needed)
        template_data: Template structure with name, description, category, effects_chain
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating save completion
        - template_path: Path where template was saved
        - template_name: Name of the saved template
        
    Template Structure:
        {
            "name": "My Custom Template",
            "description": "Description of what this template does",
            "category": "mastering" or "speech" or "creative",
            "genre": "rock" or "edm" or "podcast" etc,
            "target_platforms": ["spotify", "apple_music"],
            "effects_chain": [
                {"effect": "effect_name", "parameters": {...}},
                ...
            ]
        }
        
    Example Usage:
        save_audio_template(
            template_name="my_vocal_chain",
            template_data={
                "name": "My Vocal Processing Chain",
                "description": "Custom vocal processing for my podcast",
                "category": "speech",
                "genre": "podcast",
                "target_platforms": ["spotify_podcasts"],
                "effects_chain": [
                    {"effect": "high_pass_filter", "parameters": {"frequency": 85}},
                    {"effect": "compressor", "parameters": {"threshold": -20, "ratio": 4.0}},
                    {"effect": "loudness_normalize", "parameters": {"target_lufs": -16}}
                ]
            }
        )
    """
    try:
        success = audio_effect_processor.save_effect_template(template_name, template_data)
        if success:
            template_path = audio_effect_processor.user_templates_dir / f"{template_name}.yaml"
            return {
                "success": True,
                "template_path": str(template_path),
                "template_name": template_name,
                "message": f"Template '{template_name}' saved successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to save template '{template_name}'"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save audio template: {str(e)}"
        }


# Video Comparison Tools

@mcp.tool()
async def create_video_comparison(
    file_id_1: str, 
    file_id_2: str, 
    comparison_type: str = "side_by_side",
    label_1: str = "Version A",
    label_2: str = "Version B",
    resolution: str = "1920x1080",
    sync_audio: bool = True,
    add_labels: bool = True
) -> Dict[str, Any]:
    """🎬 VIDEO COMPARISON - Create side-by-side video comparison for A/B testing
    
    Perfect for comparing two versions of the same video project to evaluate:
    - Different editing approaches
    - Effect applications
    - Audio mixing results
    - Resolution or quality differences
    
    Args:
        file_id_1: First video file ID from list_files()
        file_id_2: Second video file ID from list_files()
        comparison_type: Layout type ("side_by_side", "top_bottom") 
        label_1: Text label for first video (default: "Version A")
        label_2: Text label for second video (default: "Version B")
        resolution: Output resolution (default: "1920x1080")
        sync_audio: Whether to mix both audio tracks (default: True)
        add_labels: Whether to add text labels identifying each version (default: True)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating comparison creation success
        - output_file_id: File ID of the comparison video
        - comparison_type: Type of comparison layout used
        - configuration: Settings used for the comparison
        - processing_time: Time taken to create the comparison
        
    Perfect For:
        - Music video A/B testing
        - Before/after effect comparisons  
        - Different edit timeline comparisons
        - Quality assessment workflows
        
    Example Usage:
        create_video_comparison(
            file_id_1="file_12345678",
            file_id_2="file_87654321", 
            label_1="Original Cut",
            label_2="Director's Cut",
            sync_audio=False  # Use audio from first video only
        )
    """
    try:
        from .video_comparison_tool import ComparisonConfig
    except ImportError:
        from video_comparison_tool import ComparisonConfig
        
    config = ComparisonConfig(
        layout=comparison_type,
        sync_audio=sync_audio,
        add_labels=add_labels,
        resolution=resolution
    )
    
    return await video_comparison_tool.create_side_by_side_comparison(
        file_id_1, file_id_2, label_1, label_2, config
    )


@mcp.tool()
async def analyze_video_differences(file_id_1: str, file_id_2: str) -> Dict[str, Any]:
    """🔍 VIDEO ANALYSIS - Analyze technical and content differences between two videos
    
    Provides detailed analysis comparison between two videos including:
    - Scene count and structure differences
    - Duration and pacing analysis
    - Visual complexity comparison
    - Quality score differences
    - AI-generated recommendations
    
    Args:
        file_id_1: First video file ID from list_files()
        file_id_2: Second video file ID from list_files()
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating analysis completion
        - video_1: Analysis data for first video
        - video_2: Analysis data for second video
        - differences: Calculated differences in key metrics
        - recommendations: AI-generated suggestions based on comparison
        
    Analysis Metrics:
        - Scene count and distribution
        - Video duration differences
        - Visual complexity assessment
        - Quality scores (if available)
        - Content structure comparison
        
    Perfect For:
        - Understanding editing impact
        - Quantifying improvement between versions
        - Making data-driven editing decisions
        - Quality assessment workflows
        
    Example Usage:
        analyze_video_differences(
            file_id_1="file_12345678",  # Original version
            file_id_2="file_87654321"   # Edited version
        )
    """
    try:
        return await video_comparison_tool.create_analysis_comparison(
            file_id_1, file_id_2, analysis_type="comprehensive"
        )
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to analyze video differences: {str(e)}"
        }


@mcp.tool()
async def create_multi_video_comparison(
    file_ids: List[str],
    labels: List[str] = None,
    layout: str = "grid",
    resolution: str = "1920x1080",
    add_labels: bool = True
) -> Dict[str, Any]:
    """🎬 MULTI-VIDEO COMPARISON - Create 2x2 grid comparison of up to 4 videos
    
    Compare multiple video versions simultaneously in a grid layout.
    Perfect for extensive A/B testing and multi-option evaluation.
    
    Args:
        file_ids: List of 2-4 video file IDs from list_files()
        labels: Optional list of labels for each video (default: Version A, B, C, D)
        layout: Layout type ("grid" for 2x2, "horizontal" for side-by-side)
        resolution: Output resolution (default: "1920x1080")
        add_labels: Whether to add text labels identifying each version (default: True)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating comparison creation success
        - output_file_id: File ID of the multi-comparison video
        - comparison_type: Type of comparison layout used
        - input_files: List of input files with their labels
        - configuration: Settings used for the comparison
        - processing_time: Time taken to create the comparison
        
    Grid Layouts:
        - 2 videos: Side-by-side horizontal layout
        - 3 videos: Top row (2 videos) + bottom row (1 centered)
        - 4 videos: 2x2 grid layout
        
    Perfect For:
        - Multi-version comparison workflows
        - Effect variation testing
        - Timeline alternative evaluation
        - Client presentation materials
        
    Example Usage:
        create_multi_video_comparison(
            file_ids=["file_1", "file_2", "file_3", "file_4"],
            labels=["Original", "Color Graded", "With Effects", "Final Cut"],
            layout="grid"
        )
    """
    try:
        from .video_comparison_tool import ComparisonConfig
    except ImportError:
        from video_comparison_tool import ComparisonConfig
        
    if len(file_ids) < 2 or len(file_ids) > 4:
        return {
            "success": False,
            "error": "Multi-video comparison requires 2-4 videos"
        }
    
    config = ComparisonConfig(
        layout=layout,
        add_labels=add_labels,
        resolution=resolution
    )
    
    return await video_comparison_tool.create_four_way_comparison(
        file_ids, labels, config
    )


# Run the server
if __name__ == "__main__":
    import atexit
    
    # Register cleanup handler
    atexit.register(lambda: asyncio.run(cleanup_analytics()))
    
    mcp.run()
