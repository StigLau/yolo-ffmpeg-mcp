#!/usr/bin/env python3
"""
FFmpeg Processor for Cloud Music Video Creator
Connects komposition.md content to actual FFmpeg processing

Now includes Haiku MCP Bridge for cost-optimized FFmpeg operations.
"""

import asyncio
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import tempfile

try:
    from interaction_logger import get_interaction_logger
except ImportError:
    # Fallback for testing without full system
    def get_interaction_logger():
        return None

logger = logging.getLogger(__name__)


class HaikuMCPBridge:
    """
    Bridge to integrate Haiku MCP TypeScript server for FFmpeg operations.
    
    Provides cost-optimized video processing using specialized Haiku LLM
    with 75x cost reduction compared to Sonnet.
    """
    
    def __init__(self, haiku_server_path: Optional[str] = None):
        """Initialize Haiku MCP Bridge."""
        self.haiku_server_path = haiku_server_path or self._find_haiku_server()
        self.server_process = None
        self.is_initialized = False
        
    def _find_haiku_server(self) -> str:
        """Find Haiku MCP server path."""
        # Default path from project structure
        default_path = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/haiku-mcp-ts"
        
        if os.path.exists(os.path.join(default_path, "dist", "server.js")):
            return default_path
        elif os.path.exists(os.path.join(default_path, "src", "server.ts")):
            return default_path
        else:
            raise FileNotFoundError(f"Haiku MCP server not found at {default_path}")
    
    async def initialize(self) -> bool:
        """Initialize Haiku MCP server."""
        if self.is_initialized:
            return True
            
        try:
            # Check if server is built
            dist_path = os.path.join(self.haiku_server_path, "dist", "server.js")
            if not os.path.exists(dist_path):
                logger.info("Building Haiku MCP server...")
                await self._build_server()
            
            # Verify API keys are available
            if not os.getenv('ANTHROPIC_API_KEY'):
                logger.warning("ANTHROPIC_API_KEY not set - Haiku will use fallback mode")
            
            self.is_initialized = True
            logger.info("Haiku MCP Bridge initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Haiku MCP Bridge: {e}")
            return False
    
    async def _build_server(self):
        """Build the TypeScript Haiku server."""
        try:
            # Change to server directory and run build
            process = await asyncio.create_subprocess_exec(
                "npm", "run", "build",
                cwd=self.haiku_server_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Build failed: {stderr.decode()}")
                
            logger.info("Haiku MCP server built successfully")
            
        except Exception as e:
            logger.error(f"Failed to build Haiku server: {e}")
            raise
    
    async def create_music_video(self, video_file: str, audio_file: str, 
                                output_file: str, **params) -> Dict[str, Any]:
        """
        Create music video using Haiku MCP server.
        
        Args:
            video_file: Path to input video file
            audio_file: Path to input audio file  
            output_file: Path for output video file
            **params: Additional parameters (duration, start_time, etc.)
            
        Returns:
            Result dictionary with success status and details
        """
        if not await self.initialize():
            return {"success": False, "error": "Failed to initialize Haiku MCP Bridge"}
        
        try:
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "create_music_video",
                    "arguments": {
                        "video_file": video_file,
                        "audio_file": audio_file,
                        "output_file": output_file,
                        **params
                    }
                }
            }
            
            # Execute MCP call
            result = await self._execute_mcp_call(mcp_request)
            return result
            
        except Exception as e:
            logger.error(f"Failed to create music video: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_video_file(self, input_file: str, output_file: str, 
                                operation: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process video file with specified operation and creative direction.
        
        Args:
            input_file: Path to input video
            output_file: Path for output video
            operation: Video processing operation (resize, trim, convert, etc.)
            parameters: Additional operation parameters (may include haiku_creative_direction)
            
        Returns:
            Result dictionary with success status and details
        """
        if not await self.initialize():
            return {"success": False, "error": "Failed to initialize Haiku MCP Bridge"}
        
        try:
            # Extract creative direction for Haiku if provided
            enhanced_parameters = parameters.copy() if parameters else {}
            
            # Add creative context to parameters for Haiku
            if parameters and "haiku_creative_direction" in parameters:
                creative_direction = parameters["haiku_creative_direction"]
                enhanced_parameters["creative_instructions"] = f"CREATIVE DIRECTION: {creative_direction}"
                logger.info(f"Sending creative direction to Haiku: {creative_direction[:100]}...")
            
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "process_video_file",
                    "arguments": {
                        "input_file": input_file,
                        "output_file": output_file,
                        "operation": operation,
                        "parameters": enhanced_parameters
                    }
                }
            }
            
            result = await self._execute_mcp_call(mcp_request)
            return result
            
        except Exception as e:
            logger.error(f"Failed to process video: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_mcp_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP call to Haiku server."""
        try:
            # Start server process
            server_js = os.path.join(self.haiku_server_path, "dist", "server.js")
            
            process = await asyncio.create_subprocess_exec(
                "node", server_js,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.haiku_server_path
            )
            
            # Send MCP request
            request_json = json.dumps(request) + "\n"
            stdout, stderr = await process.communicate(request_json.encode())
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                return {"success": False, "error": f"Server error: {error_msg}"}
            
            # Parse response
            response_text = stdout.decode().strip()
            if not response_text:
                return {"success": False, "error": "Empty response from server"}
            
            try:
                response = json.loads(response_text)
                
                # Extract result from MCP response
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    result = json.loads(content)
                    return result
                else:
                    return {"success": False, "error": "Invalid MCP response format"}
                    
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Failed to parse response: {e}"}
            
        except Exception as e:
            logger.error(f"MCP call execution failed: {e}")
            return {"success": False, "error": str(e)}


@dataclass
class FFmpegCommand:
    """Represents an FFmpeg command with metadata"""
    command: str
    purpose: str
    estimated_duration: float
    input_files: List[str]
    output_file: str


@dataclass
class ProcessingResult:
    """Result of FFmpeg processing"""
    success: bool
    output_file: Optional[str]
    commands_executed: List[str]
    total_duration: float
    error_message: Optional[str]
    ffmpeg_logs: List[str]


class KompositionFFmpegProcessor:
    """
    Converts komposition.md specifications into FFmpeg commands and executes them.
    Now supports both legacy processing and Haiku MCP integration.
    """
    
    def __init__(self, use_haiku: bool = True):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="kompo_ffmpeg_"))
        self.use_haiku = use_haiku
        self.haiku_bridge = HaikuMCPBridge() if use_haiku else None
        logger.info(f"FFmpeg processor initialized with temp_dir: {self.temp_dir}, use_haiku: {use_haiku}")
    
    async def create_komposition_video_with_haiku(self, komposition: Dict[str, Any], 
                                                 output_path: str) -> Dict[str, Any]:
        """
        Create video from komposition using Haiku MCP processing.
        
        Args:
            komposition: YOLO-format komposition JSON
            output_path: Path for final video output
            
        Returns:
            Processing result with success status and details
        """
        if not self.haiku_bridge:
            return {"success": False, "error": "Haiku MCP Bridge not available"}
        
        try:
            # Extract segments for processing
            segments = komposition.get('segments', [])
            if not segments:
                return {"success": False, "error": "No segments found in komposition"}
            
            # Create temp directory for intermediate files
            with tempfile.TemporaryDirectory(prefix="kompo_") as temp_dir:
                processed_segments = []
                
                # Process each segment
                for i, segment in enumerate(segments):
                    segment_result = await self._process_segment_with_haiku(segment, temp_dir, i)
                    if segment_result["success"]:
                        processed_segments.append(segment_result["output_file"])
                    else:
                        logger.error(f"Failed to process segment {i}: {segment_result.get('error')}")
                        return {"success": False, "error": f"Segment {i} processing failed"}
                
                # Combine all segments into final video
                final_result = await self._combine_segments_with_haiku(processed_segments, output_path)
                return final_result
                
        except Exception as e:
            logger.error(f"Komposition video creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_segment_with_haiku(self, segment: Dict[str, Any], 
                                        temp_dir: str, segment_index: int, 
                                        komposition_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process individual segment using Haiku MCP with creative direction."""
        try:
            # Extract segment properties
            source_video = segment.get('source', {}).get('path')
            start_time = segment.get('start', 0)
            duration = segment.get('duration', 5)
            filters = segment.get('filters', [])
            
            if not source_video:
                return {"success": False, "error": f"No source video for segment {segment_index}"}
            
            # Generate output path for segment
            output_file = os.path.join(temp_dir, f"segment_{segment_index:03d}.mp4")
            
            # Build processing parameters
            parameters = {
                "start_time": start_time,
                "duration": duration,
                "filters": filters,
                "segment_index": segment_index
            }
            
            # Add creative direction from komposition metadata if available
            if komposition_metadata and "haiku_creative_direction" in komposition_metadata:
                parameters["haiku_creative_direction"] = komposition_metadata["haiku_creative_direction"]
            
            # Process segment using Haiku MCP
            result = await self.haiku_bridge.process_video_file(
                input_file=source_video,
                output_file=output_file,
                operation="segment_process",
                parameters=parameters
            )
            
            if result.get("success"):
                result["output_file"] = output_file
            
            return result
            
        except Exception as e:
            logger.error(f"Segment processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _combine_segments_with_haiku(self, segment_files: List[str], 
                                         output_path: str) -> Dict[str, Any]:
        """Combine processed segments into final video."""
        try:
            if len(segment_files) == 1:
                # Single segment - just copy
                import shutil
                shutil.copy2(segment_files[0], output_path)
                return {"success": True, "output_file": output_path}
            
            # Multiple segments - use Haiku MCP to concatenate
            result = await self.haiku_bridge.process_video_file(
                input_file=segment_files[0],  # Primary file
                output_file=output_path,
                operation="concatenate",
                parameters={"additional_files": segment_files[1:]}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Segment combination failed: {e}")
            return {"success": False, "error": str(e)}
    
    def parse_komposition(self, komposition_md: str) -> Dict[str, any]:
        """Parse komposition markdown to extract processing requirements"""
        
        # Simple parsing - in production this would be more sophisticated
        parsed = {
            "duration": 30,
            "bpm": 120,
            "resolution": "1920x1080",
            "format": "mp4",
            "segments": [],
            "effects": [],
            "style": "modern"
        }
        
        try:
            # Extract basic parameters
            if "Duration**: " in komposition_md:
                duration_match = re.search(r'Duration\*\*:\s*(\d+)', komposition_md)
                if duration_match:
                    parsed["duration"] = int(duration_match.group(1))
            
            if "BPM**: " in komposition_md:
                bpm_match = re.search(r'BPM\*\*:\s*(\d+)', komposition_md)
                if bpm_match:
                    parsed["bpm"] = int(bpm_match.group(1))
            
            # Extract style hints
            if any(word in komposition_md.lower() for word in ['vintage', 'retro', 'sepia']):
                parsed["style"] = "vintage"
            elif any(word in komposition_md.lower() for word in ['dreamy', 'blur', 'ethereal']):
                parsed["style"] = "dreamy"
            
            # Extract segments (simplified)
            segments = re.findall(r'### Segment \d+.*?\n(?:.*?\n)*?(?=### |## |$)', komposition_md, re.MULTILINE)
            for i, segment in enumerate(segments):
                segment_info = {
                    "index": i,
                    "content": segment,
                    "effects": self._extract_effects_from_segment(segment)
                }
                parsed["segments"].append(segment_info)
            
        except Exception as e:
            logger.error(f"Error parsing komposition: {e}")
        
        return parsed
    
    def _extract_effects_from_segment(self, segment_text: str) -> List[str]:
        """Extract visual effects from a segment description"""
        effects = []
        segment_lower = segment_text.lower()
        
        # Map komposition descriptions to FFmpeg effects
        effect_mapping = {
            'sepia': 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131',
            'film grain': 'noise=alls=20:allf=t',
            'vintage': 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,noise=alls=20:allf=t',
            'blur': 'gblur=sigma=3',
            'dreamy': 'gblur=sigma=2,eq=brightness=0.1',
            'ethereal': 'gblur=sigma=1.5,eq=brightness=0.15,curves=all="0/0 0.5/0.6 1/1"',
            'contrast': 'eq=contrast=1.2',
            'saturation': 'eq=saturation=1.3',
            'vignette': 'vignette=angle=PI/6'
        }
        
        for effect_name, ffmpeg_filter in effect_mapping.items():
            if effect_name in segment_lower:
                effects.append(ffmpeg_filter)
        
        return effects
    
    async def generate_ffmpeg_commands(self, komposition_md: str, session_id: str) -> List[FFmpegCommand]:
        """Generate FFmpeg commands from komposition specification"""
        
        logger_service = get_interaction_logger()
        if not logger_service:
            logger_service = type('DummyLogger', (), {
                'log_llm2_call': lambda *args, **kwargs: None,
                'log_llm2_response': lambda *args, **kwargs: None,
                'log_error': lambda *args, **kwargs: None,
                'log_ffmpeg_command': lambda *args, **kwargs: "dummy_id",
                'log_ffmpeg_output': lambda *args, **kwargs: None
            })()
        parsed = self.parse_komposition(komposition_md)
        commands = []
        
        try:
            # For this implementation, create a demo video based on the style
            output_file = self.temp_dir / f"komposition_video_{session_id}.mp4"
            
            if parsed["style"] == "vintage":
                # Vintage video generation
                command = self._generate_vintage_command(parsed, str(output_file))
                commands.append(FFmpegCommand(
                    command=command,
                    purpose="Generate vintage-style video from komposition",
                    estimated_duration=parsed["duration"] + 5,
                    input_files=[],  # Using lavfi test sources
                    output_file=str(output_file)
                ))
            
            elif parsed["style"] == "dreamy":
                # Dreamy video generation
                command = self._generate_dreamy_command(parsed, str(output_file))
                commands.append(FFmpegCommand(
                    command=command,
                    purpose="Generate dreamy-style video from komposition",
                    estimated_duration=parsed["duration"] + 5,
                    input_files=[],  # Using lavfi test sources
                    output_file=str(output_file)
                ))
            
            else:
                # Modern/default video generation
                command = self._generate_modern_command(parsed, str(output_file))
                commands.append(FFmpegCommand(
                    command=command,
                    purpose="Generate modern-style video from komposition",
                    estimated_duration=parsed["duration"] + 5,
                    input_files=[],  # Using lavfi test sources
                    output_file=str(output_file)
                ))
            
            # Log command generation
            logger_service.log_llm2_call(
                session_id=session_id,
                purpose="Generate FFmpeg commands from komposition",
                request=komposition_md[:500],  # Truncated for logging
                model="komposition_parser",
                metadata={"parsed_style": parsed["style"], "command_count": len(commands)}
            )
            
            command_strings = [cmd.command for cmd in commands]
            logger_service.log_llm2_response(
                session_id=session_id,
                call_id="komposition_parse",
                response=f"Generated {len(commands)} FFmpeg commands for {parsed['style']} style",
                commands_generated=command_strings
            )
            
        except Exception as e:
            logger.error(f"Error generating FFmpeg commands: {e}")
            logger_service.log_error(
                session_id=session_id,
                error_type="ffmpeg_command_generation_error",
                error_message=str(e)
            )
        
        return commands
    
    def _generate_vintage_command(self, parsed: Dict, output_file: str) -> str:
        """Generate vintage-style FFmpeg command"""
        duration = parsed["duration"]
        return f"ffmpeg -y -f lavfi -i testsrc2=duration={duration}:size=1920x1080:rate=25 -f lavfi -i sine=frequency=440:duration={duration} -filter_complex [0:v]colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,hue=s=0.6,noise=alls=20:allf=t,vignette=PI/6[v];[1:a]volume=0.7[a] -map [v] -map [a] -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -t {duration} {output_file}"
    
    def _generate_dreamy_command(self, parsed: Dict, output_file: str) -> str:
        """Generate dreamy-style FFmpeg command"""
        duration = parsed["duration"]
        return f"ffmpeg -y -f lavfi -i testsrc2=duration={duration}:size=1920x1080:rate=25 -f lavfi -i sine=frequency=220:duration={duration} -filter_complex [0:v]gblur=sigma=3:steps=1,eq=brightness=0.1:contrast=0.9,curves=all='0/0 0.3/0.4 0.7/0.7 1/0.9',fade=t=in:st=0:d=2,fade=t=out:st={duration-2}:d=2[v];[1:a]volume=0.5,afade=t=in:st=0:d=2,afade=t=out:st={duration-2}:d=2[a] -map [v] -map [a] -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -t {duration} {output_file}"
    
    def _generate_modern_command(self, parsed: Dict, output_file: str) -> str:
        """Generate modern-style FFmpeg command"""
        duration = parsed["duration"]
        return f"ffmpeg -y -f lavfi -i testsrc2=duration={duration}:size=1920x1080:rate=25 -f lavfi -i sine=frequency=880:duration={duration} -filter_complex [0:v]eq=contrast=1.2:saturation=1.1,unsharp=luma_msize_x=5:luma_msize_y=5:luma_amount=0.5[v];[1:a]volume=0.8[a] -map [v] -map [a] -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -t {duration} {output_file}"
    
    async def execute_commands(self, commands: List[FFmpegCommand], session_id: str) -> ProcessingResult:
        """Execute FFmpeg commands and return results"""
        
        logger_service = get_interaction_logger()
        if not logger_service:
            logger_service = type('DummyLogger', (), {
                'log_llm2_call': lambda *args, **kwargs: None,
                'log_llm2_response': lambda *args, **kwargs: None,
                'log_error': lambda *args, **kwargs: None,
                'log_ffmpeg_command': lambda *args, **kwargs: "dummy_id",
                'log_ffmpeg_output': lambda *args, **kwargs: None
            })()
        executed_commands = []
        ffmpeg_logs = []
        total_start_time = asyncio.get_event_loop().time()
        
        try:
            for cmd in commands:
                # Log command execution
                command_id = logger_service.log_ffmpeg_command(
                    session_id=session_id,
                    command=cmd.command,
                    purpose=cmd.purpose
                )
                
                # Execute command
                start_time = asyncio.get_event_loop().time()
                
                logger.info(f"Executing FFmpeg command: {cmd.purpose}")
                
                result = await self._run_ffmpeg_command(cmd.command)
                
                execution_time = asyncio.get_event_loop().time() - start_time
                executed_commands.append(cmd.command)
                
                # Log command output
                logger_service.log_ffmpeg_output(
                    session_id=session_id,
                    command_id=command_id,
                    stdout=result["stdout"],
                    stderr=result["stderr"],
                    return_code=result["return_code"],
                    execution_time=execution_time
                )
                
                if result["return_code"] != 0:
                    error_msg = f"FFmpeg command failed: {result['stderr']}"
                    logger.error(error_msg)
                    ffmpeg_logs.append(f"ERROR: {error_msg}")
                    
                    return ProcessingResult(
                        success=False,
                        output_file=None,
                        commands_executed=executed_commands,
                        total_duration=asyncio.get_event_loop().time() - total_start_time,
                        error_message=error_msg,
                        ffmpeg_logs=ffmpeg_logs
                    )
                
                ffmpeg_logs.append(f"SUCCESS: {cmd.purpose}")
                logger.info(f"Command completed successfully in {execution_time:.2f}s")
            
            # Find the output file
            output_file = commands[-1].output_file if commands else None
            
            total_duration = asyncio.get_event_loop().time() - total_start_time
            
            logger.info(f"All FFmpeg commands completed successfully in {total_duration:.2f}s")
            
            return ProcessingResult(
                success=True,
                output_file=output_file,
                commands_executed=executed_commands,
                total_duration=total_duration,
                error_message=None,
                ffmpeg_logs=ffmpeg_logs
            )
            
        except Exception as e:
            error_msg = f"FFmpeg processing exception: {str(e)}"
            logger.error(error_msg)
            
            logger_service.log_error(
                session_id=session_id,
                error_type="ffmpeg_processing_error",
                error_message=error_msg
            )
            
            return ProcessingResult(
                success=False,
                output_file=None,
                commands_executed=executed_commands,
                total_duration=asyncio.get_event_loop().time() - total_start_time,
                error_message=error_msg,
                ffmpeg_logs=ffmpeg_logs
            )
    
    async def _run_ffmpeg_command(self, command: str) -> Dict[str, any]:
        """Run a single FFmpeg command"""
        try:
            # Split command into parts (simple approach)
            cmd_parts = command.split()
            
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8') if stdout else "",
                "stderr": stderr.decode('utf-8') if stderr else ""
            }
            
        except Exception as e:
            return {
                "return_code": -1,
                "stdout": "",
                "stderr": f"Command execution failed: {str(e)}"
            }


# Global instance
ffmpeg_processor = None

def get_ffmpeg_processor(use_haiku: bool = True) -> KompositionFFmpegProcessor:
    """Get or create the global FFmpeg processor instance"""
    global ffmpeg_processor
    if ffmpeg_processor is None:
        ffmpeg_processor = KompositionFFmpegProcessor(use_haiku=use_haiku)
    return ffmpeg_processor

def create_haiku_ffmpeg_processor() -> KompositionFFmpegProcessor:
    """Create a new FFmpeg processor with Haiku MCP integration."""
    return KompositionFFmpegProcessor(use_haiku=True)