from pathlib import Path
from typing import Dict, List, Any
import asyncio
import os
import re
import shutil


class FFMPEGWrapper:
    ALLOWED_OPERATIONS = {
        "convert": {
            "args": ["-c:v", "libx264", "-c:a", "aac"],
            "description": "Convert video/audio format"
        },
        "extract_audio": {
            "args": ["-vn", "-acodec", "copy"],
            "description": "Extract audio from video"
        },
        "trim": {
            "args": ["-ss", "{start}", "-t", "{duration}"],
            "description": "Trim video/audio (requires start and duration)"
        },
        "resize": {
            "args": ["-vf", "scale={width}:{height}"],
            "description": "Resize video (requires width and height)"
        },
        "normalize_audio": {
            "args": ["-af", "loudnorm"],
            "description": "Normalize audio levels"
        },
        "to_mp3": {
            "args": ["-c:a", "libmp3lame", "-b:a", "192k"],
            "description": "Convert to MP3 format"
        },
        "replace_audio": {
            "args": ["-i", "{audio_file}", "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-shortest"],
            "description": "Replace video audio with another audio file (requires audio_file)"
        },
        "trim_and_replace_audio": {
            "args": ["-ss", "{start}", "-t", "{duration}", "-i", "{audio_file}", "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-shortest"],
            "description": "Trim video and replace audio (requires start, duration, audio_file)"
        },
        "concatenate_simple": {
            "args": ["-i", "{second_video}", "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[outv];[0:a][1:a]concat=n=2:v=0:a=1[outa]", "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-c:a", "aac"],
            "description": "Smart concatenate two videos with automatic resolution/audio handling (requires second_video)"
        },
        "image_to_video": {
            "args": ["-r", "25", "-c:v", "libx264", "-pix_fmt", "yuv420p"],
            "pre_input_args": ["-loop", "1", "-t", "{duration}"],
            "description": "Convert image to video clip (requires duration in seconds)"
        },
        "reverse": {
            "args": ["-vf", "reverse", "-af", "areverse"],
            "description": "Reverse video and audio playback"
        },
        "gradient_wipe": {
            "args": ["-i", "{second_video}", "-filter_complex", 
                     "[0:v]scale=1280:720,setsar=1:1[v0];[1:v]scale=1280:720,setsar=1:1[v1];[v0][v1]xfade=transition=wiperight:duration={duration}:offset={offset}[outv]",
                     "-map", "[outv]", "-c:v", "libx264"],
            "description": "Gradient wipe transition between two videos (requires second_video, duration, offset)"
        },
        "crossfade_transition": {
            "args": ["-i", "{second_video}", "-filter_complex",
                     "[0:v]scale=1280:720,setsar=1:1[v0];[1:v]scale=1280:720,setsar=1:1[v1];[v0][v1]xfade=transition=fade:duration={duration}:offset={offset}[outv]", 
                     "-map", "[outv]", "-c:v", "libx264"],
            "description": "Crossfade transition between two videos (requires second_video, duration, offset)"
        },
        "opacity_transition": {
            "args": ["-i", "{second_video}", "-filter_complex",
                     "[1:v]format=yuva420p,colorchannelmixer=aa={opacity}[overlay];[0:v][overlay]overlay[outv];[0:a][1:a]amix=duration=shortest[outa]",
                     "-map", "[outv]", "-map", "[outa]", "-c:v", "libx264", "-c:a", "aac"],
            "description": "Opacity-based transition with transparency control (requires second_video, opacity 0.0-1.0)"
        },
        "leica_look": {
            "args": ["-vf", "curves=vintage,eq=contrast=1.1:brightness=0.05:saturation=0.9:gamma=1.05,colorbalance=rs=0.1:gs=-0.05:bs=-0.1:rm=0.05:gm=0:bm=-0.05:rh=-0.05:gh=0.05:bh=0.1,unsharp=5:5:0.8:3:3:0.4"],
            "description": "Apply Leica-style color grading with vintage curves, contrast, and color balance"
        },
        "leica_look_enhanced": {
            "args": ["-vf", "curves=vintage,eq=contrast=1.15:brightness=0.08:saturation=0.85:gamma=1.08,colorbalance=rs=0.15:gs=-0.08:bs=-0.15:rm=0.08:gm=0:bm=-0.08:rh=-0.08:gh=0.08:bh=0.15,unsharp=5:5:1.0:3:3:0.6,vignette=angle=PI/4:mode=backward"],
            "description": "Enhanced Leica-style look with stronger vintage characteristics and vignetting"
        },
        "apply_leica_and_trim": {
            "args": ["-ss", "{start}", "-t", "{duration}", "-vf", "curves=vintage,eq=contrast=1.1:brightness=0.05:saturation=0.9:gamma=1.05,colorbalance=rs=0.1:gs=-0.05:bs=-0.1:rm=0.05:gm=0:bm=-0.05:rh=-0.05:gh=0.05:bh=0.1,unsharp=5:5:0.8:3:3:0.4"],
            "description": "Trim video segment and apply Leica look in one operation (requires start, duration)"
        }
    }

    def __init__(self, ffmpeg_path: str = None):
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg_path() or "ffmpeg"
        
    def build_command(self, operation: str, input_path: Path, output_path: Path, **params) -> List[str]:
        """Build safe FFMPEG command"""
        if operation not in self.ALLOWED_OPERATIONS:
            raise ValueError(f"Operation '{operation}' not allowed. Available: {list(self.ALLOWED_OPERATIONS.keys())}")
            
        operation_config = self.ALLOWED_OPERATIONS[operation]
        args = operation_config["args"].copy()
        pre_input_args = operation_config.get("pre_input_args", []).copy()
        
        # Replace parameter placeholders in main args
        for i, arg in enumerate(args):
            if isinstance(arg, str) and "{" in arg:
                for param_name, param_value in params.items():
                    placeholder = f"{{{param_name}}}"
                    if placeholder in arg:
                        args[i] = arg.replace(placeholder, str(param_value))
        
        # Replace parameter placeholders in pre-input args
        for i, arg in enumerate(pre_input_args):
            if isinstance(arg, str) and "{" in arg:
                for param_name, param_value in params.items():
                    placeholder = f"{{{param_name}}}"
                    if placeholder in arg:
                        pre_input_args[i] = arg.replace(placeholder, str(param_value))
        
        # Validate that all placeholders were replaced in both arg lists
        all_args = args + pre_input_args
        for arg in all_args:
            if isinstance(arg, str) and re.search(r'\{[^}]+\}', arg):
                missing_params = re.findall(r'\{([^}]+)\}', arg)
                raise ValueError(f"Missing required parameters: {missing_params}")
        
        # Build complete command with pre-input args before -i
        command = [
            self.ffmpeg_path,
            *pre_input_args,
            "-i", str(input_path),
            *args,
            str(output_path),
            "-y"  # Overwrite output file
        ]
        
        return command
    
    def _find_ffmpeg_path(self) -> str:
        """Find FFmpeg executable in various locations"""
        # Check environment variable first
        env_path = os.getenv("FFMPEG_PATH")
        if env_path and Path(env_path).exists():
            return env_path
        
        # Try PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        
        # Try common locations
        common_paths = [
            "/opt/homebrew/bin/ffmpeg",  # Homebrew on Apple Silicon
            "/usr/local/bin/ffmpeg",     # Homebrew on Intel Mac / Linux
            "/usr/bin/ffmpeg",           # System package on Linux
            "/snap/bin/ffmpeg",          # Snap package on Linux
            "/usr/local/opt/ffmpeg/bin/ffmpeg",  # Homebrew alternative
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        return None
        
    async def has_audio_stream(self, file_path: Path, file_manager=None, file_id: str = None) -> bool:
        """Check if a video file has an audio stream (with caching)"""
        info = await self.get_file_info(file_path, file_manager, file_id)
        if not info.get("success"):
            return False
            
        # Use cached video properties if available
        video_props = info.get("video_properties", {})
        if video_props:
            return video_props.get("has_audio", False)
            
        # Fallback to streams analysis
        streams = info.get("info", {}).get("streams", [])
        return any(stream.get("codec_type") == "audio" for stream in streams)
    
    async def get_video_resolution(self, file_path: Path, file_manager=None, file_id: str = None) -> tuple:
        """Get video resolution as (width, height) (with caching)"""
        info = await self.get_file_info(file_path, file_manager, file_id)
        if not info.get("success"):
            return None
            
        # Use cached video properties if available
        video_props = info.get("video_properties", {})
        if video_props and video_props.get("resolution"):
            resolution_str = video_props["resolution"]
            try:
                width, height = map(int, resolution_str.split('x'))
                return (width, height)
            except (ValueError, AttributeError):
                pass
                
        # Fallback to streams analysis
        streams = info.get("info", {}).get("streams", [])
        for stream in streams:
            if stream.get("codec_type") == "video":
                width = stream.get("width")
                height = stream.get("height")
                if width and height:
                    return (width, height)
        return None

    async def build_smart_concat_command(self, input_path: Path, second_video_path: Path, output_path: Path, file_manager=None) -> List[str]:
        """Build concatenation command that handles videos with different properties"""
        # Check audio streams
        has_audio_1 = await self.has_audio_stream(input_path)
        has_audio_2 = await self.has_audio_stream(second_video_path)
        
        # Check video resolutions
        res1 = await self.get_video_resolution(input_path)
        res2 = await self.get_video_resolution(second_video_path)
        
        # Determine if we need to scale videos to match
        need_scaling = res1 != res2 and res1 is not None and res2 is not None
        
        if need_scaling:
            # Smart orientation handling: choose consistent orientation
            w1, h1 = res1
            w2, h2 = res2
            
            # Detect orientations
            is_portrait_1 = h1 > w1
            is_portrait_2 = h2 > w2
            
            # If orientations differ, normalize to landscape (wider format for music videos)
            if is_portrait_1 != is_portrait_2:
                # Choose landscape orientation for consistency
                if is_portrait_1:
                    target_width, target_height = max(w1, h1), min(w1, h1)  # Landscape from portrait
                else:
                    target_width, target_height = w1, h1  # Keep landscape
            else:
                # Same orientation, use first video resolution
                target_width, target_height = res1
            
            if has_audio_1 and has_audio_2:
                # Both have audio, scale second video to match first and fix SAR
                filter_complex = f"[0:v]scale={target_width}:{target_height},setsar=1:1[v0norm];[1:v]scale={target_width}:{target_height},setsar=1:1[v1norm];[v0norm][v1norm]concat=n=2:v=1:a=0[outv];[0:a][1:a]concat=n=2:v=0:a=1[outa]"
                maps = ["-map", "[outv]", "-map", "[outa]"]
                codecs = ["-c:v", "libx264", "-c:a", "aac"]
            else:
                # No audio or mixed audio - video only with scaling and SAR fix
                filter_complex = f"[0:v]scale={target_width}:{target_height},setsar=1:1[v0norm];[1:v]scale={target_width}:{target_height},setsar=1:1[v1norm];[v0norm][v1norm]concat=n=2:v=1:a=0[outv]"
                maps = ["-map", "[outv]"]
                codecs = ["-c:v", "libx264"]
        else:
            # Same resolution but normalize SAR to avoid issues
            if has_audio_1 and has_audio_2:
                # Both have audio - normalize SAR and concatenate
                filter_complex = "[0:v]setsar=1:1[v0norm];[1:v]setsar=1:1[v1norm];[v0norm][v1norm]concat=n=2:v=1:a=0[outv];[0:a][1:a]concat=n=2:v=0:a=1[outa]"
                maps = ["-map", "[outv]", "-map", "[outa]"]
                codecs = ["-c:v", "libx264", "-c:a", "aac"]
            else:
                # No audio or mixed audio - normalize SAR and video-only concatenation
                filter_complex = "[0:v]setsar=1:1[v0norm];[1:v]setsar=1:1[v1norm];[v0norm][v1norm]concat=n=2:v=1:a=0[outv]"
                maps = ["-map", "[outv]"]
                codecs = ["-c:v", "libx264"]
        
        command = [
            self.ffmpeg_path,
            "-i", str(input_path),
            "-i", str(second_video_path),
            "-filter_complex", filter_complex,
            *maps,
            *codecs,
            str(output_path),
            "-y"
        ]
        
        return command

    async def execute_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Execute FFMPEG command with timeout"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": ' '.join(command)
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": ' '.join(command)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": ' '.join(command)
            }
            
    def get_available_operations(self) -> Dict[str, str]:
        """Get list of available operations with descriptions"""
        return {
            name: config["description"] 
            for name, config in self.ALLOWED_OPERATIONS.items()
        }
        
    async def get_file_info(self, file_path: Path, file_manager=None, file_id: str = None) -> Dict[str, Any]:
        """Get file information using ffprobe with caching support"""
        
        # Try cache first if file_manager and file_id provided
        if file_manager and file_id:
            cached = file_manager.get_cached_properties(file_id)
            if cached:
                return cached
        ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
        
        command = [
            ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(file_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                raw_info = json.loads(stdout.decode('utf-8'))
                
                # Extract music video relevant properties
                result = {
                    "success": True,
                    "info": raw_info,
                    "video_properties": self._extract_video_properties(raw_info)
                }
                
                # Cache the result if possible
                if file_manager and file_id:
                    file_manager.cache_file_properties(file_id, result)
                
                return result
            else:
                return {
                    "success": False,
                    "error": stderr.decode('utf-8', errors='ignore')
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
    def _extract_video_properties(self, ffprobe_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract video-specific properties for music video workflows"""
        properties = {
            "has_video": False,
            "has_audio": False,
            "resolution": None,
            "duration": None,
            "framerate": None,
            "codec": None,
            "sar": None  # Sample Aspect Ratio
        }
        
        try:
            streams = ffprobe_info.get("streams", [])
            format_info = ffprobe_info.get("format", {})
            
            # Extract duration
            if "duration" in format_info:
                properties["duration"] = float(format_info["duration"])
            
            # Analyze streams
            for stream in streams:
                if stream.get("codec_type") == "video":
                    properties["has_video"] = True
                    properties["resolution"] = f"{stream.get('width', 0)}x{stream.get('height', 0)}"
                    properties["codec"] = stream.get("codec_name")
                    properties["sar"] = stream.get("sample_aspect_ratio", "1:1")
                    
                    # Extract framerate
                    if "r_frame_rate" in stream:
                        properties["framerate"] = stream["r_frame_rate"]
                        
                elif stream.get("codec_type") == "audio":
                    properties["has_audio"] = True
                    
        except Exception:
            # If extraction fails, return basic properties
            pass
            
        return properties
