import asyncio
import os
from pathlib import Path
from typing import Dict, List, Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

try:
    from .file_manager import FileManager
    from .ffmpeg_wrapper import FFMPEGWrapper
    from .config import SecurityConfig
    from .content_analyzer import VideoContentAnalyzer
except ImportError:
    from file_manager import FileManager
    from ffmpeg_wrapper import FFMPEGWrapper
    from config import SecurityConfig
    from content_analyzer import VideoContentAnalyzer


# Initialize MCP server
mcp = FastMCP("ffmpeg-mcp")

# Initialize components
file_manager = FileManager()
ffmpeg = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
content_analyzer = VideoContentAnalyzer()


class FileInfo(BaseModel):
    id: str
    name: str
    size: int
    extension: str


class ProcessResult(BaseModel):
    success: bool
    message: str
    output_file_id: str = None
    logs: str = None


@mcp.tool()
async def list_files() -> Dict[str, Any]:
    """List available source files with smart suggestions and quick actions"""
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
            
    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}", "files": [], "suggestions": [], "quick_actions": []}
        
    return {
        "files": files,
        "suggestions": suggestions,
        "quick_actions": quick_actions,
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
    operation: str,
    output_extension: str = "mp4",
    params: str = ""
) -> ProcessResult:
    """Process a file using FFMPEG with specified operation"""
    
    # Resolve input file
    input_path = file_manager.resolve_id(input_file_id)
    if not input_path:
        return ProcessResult(
            success=False,
            message=f"Input file ID '{input_file_id}' not found"
        )
        
    if not input_path.exists():
        return ProcessResult(
            success=False,
            message=f"Input file no longer exists: {input_path.name}"
        )
    
    # Validate file size
    if not SecurityConfig.validate_file_size(input_path):
        return ProcessResult(
            success=False,
            message=f"File too large (max {SecurityConfig.MAX_FILE_SIZE} bytes)"
        )
    
    try:
        # Validate operation requirements
        required_params = {
            'trim': ['start', 'duration'],
            'resize': ['width', 'height'],
            'replace_audio': ['audio_file'],
            'concatenate_simple': ['second_video'],
            'trim_and_replace_audio': ['start', 'duration', 'audio_file'],
            'image_to_video': ['duration']
        }
        
        # Parse params string into dict
        parsed_params = {}
        if params:
            for param in params.split():
                if '=' in param:
                    key, value = param.split('=', 1)
                    # If the value looks like a file ID, resolve it to a path
                    if value.startswith('file_') and key in ['audio_file', 'second_video']:
                        file_path = file_manager.resolve_id(value)
                        if file_path and file_path.exists():
                            parsed_params[key] = str(file_path)
                        else:
                            return ProcessResult(
                                success=False,
                                message=f"File ID '{value}' not found"
                            )
                    else:
                        parsed_params[key] = value
        
        # Check for required parameters
        if operation in required_params:
            missing = [p for p in required_params[operation] if p not in parsed_params]
            if missing:
                examples = {
                    'trim': 'start=10 duration=15',
                    'resize': 'width=1280 height=720', 
                    'replace_audio': 'audio_file=file_12345678',
                    'concatenate_simple': 'second_video=file_87654321',
                    'trim_and_replace_audio': 'start=10 duration=15 audio_file=file_12345678',
                    'image_to_video': 'duration=2'
                }
                return ProcessResult(
                    success=False,
                    message=f"Missing required parameters: {missing}. Example: {examples.get(operation, '')}"
                )
        
        # Create output file
        output_file_id, output_path = file_manager.create_temp_file(output_extension)
        
        # Build and execute command
        if operation == 'concatenate_simple':
            # Use smart concatenation that handles videos with/without audio
            second_video_path = Path(parsed_params['second_video'])
            command = await ffmpeg.build_smart_concat_command(input_path, second_video_path, output_path, file_manager)
        else:
            command = ffmpeg.build_command(operation, input_path, output_path, **parsed_params)
        result = await ffmpeg.execute_command(command, SecurityConfig.PROCESS_TIMEOUT)
        
        if result["success"]:
            return ProcessResult(
                success=True,
                message=f"Successfully processed {input_path.name}",
                output_file_id=output_file_id,
                logs=result.get("stderr", "")
            )
        else:
            return ProcessResult(
                success=False,
                message=f"FFMPEG failed: {result.get('error', 'Unknown error')}",
                logs=result.get("stderr", "")
            )
            
    except ValueError as e:
        return ProcessResult(
            success=False,
            message=f"Invalid operation or parameters: {str(e)}"
        )
    except Exception as e:
        return ProcessResult(
            success=False,
            message=f"Unexpected error: {str(e)}"
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


# Run the server
if __name__ == "__main__":
    mcp.run()