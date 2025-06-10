from pathlib import Path
from typing import Dict, List, Any
import asyncio
import os
import re


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
            "description": "Simple concatenate two videos (requires second_video)"
        }
    }

    def __init__(self, ffmpeg_path: str = None):
        self.ffmpeg_path = ffmpeg_path or os.getenv("FFMPEG_PATH", "ffmpeg")
        
    def build_command(self, operation: str, input_path: Path, output_path: Path, **params) -> List[str]:
        """Build safe FFMPEG command"""
        if operation not in self.ALLOWED_OPERATIONS:
            raise ValueError(f"Operation '{operation}' not allowed. Available: {list(self.ALLOWED_OPERATIONS.keys())}")
            
        operation_config = self.ALLOWED_OPERATIONS[operation]
        args = operation_config["args"].copy()
        
        # Replace parameter placeholders
        for i, arg in enumerate(args):
            if isinstance(arg, str) and "{" in arg:
                for param_name, param_value in params.items():
                    placeholder = f"{{{param_name}}}"
                    if placeholder in arg:
                        args[i] = arg.replace(placeholder, str(param_value))
        
        # Validate that all placeholders were replaced
        for arg in args:
            if isinstance(arg, str) and re.search(r'\{[^}]+\}', arg):
                missing_params = re.findall(r'\{([^}]+)\}', arg)
                raise ValueError(f"Missing required parameters: {missing_params}")
        
        # Build complete command
        command = [
            self.ffmpeg_path,
            "-i", str(input_path),
            *args,
            str(output_path),
            "-y"  # Overwrite output file
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
        
    async def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information using ffprobe"""
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
                info = json.loads(stdout.decode('utf-8'))
                return {
                    "success": True,
                    "info": info
                }
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