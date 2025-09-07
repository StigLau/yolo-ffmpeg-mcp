#!/usr/bin/env python3
"""
Markdown-Native FFmpeg Processor for Cloud Music Video Creator
Processes komposition markdown directly with Haiku MCP integration.

This approach aligns better with Haiku's natural language understanding
and avoids complex markdown→JSON conversion issues.
"""

import asyncio
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess

try:
    from interaction_logger import get_interaction_logger
except ImportError:
    def get_interaction_logger():
        return None

logger = logging.getLogger(__name__)


class MarkdownHaikuProcessor:
    """
    Processes komposition markdown files directly using Haiku MCP.
    
    This processor sends the raw markdown komposition to Haiku and lets
    Haiku's natural language understanding extract media files, timing,
    effects, and generate appropriate FFmpeg commands.
    """
    
    def __init__(self, haiku_server_path: Optional[str] = None):
        """Initialize markdown-native Haiku processor."""
        self.haiku_server_path = haiku_server_path or self._find_haiku_server()
        self.interaction_logger = get_interaction_logger()
        
    def _find_haiku_server(self) -> str:
        """Find Haiku MCP server path."""
        default_path = "/Users/stiglau/utvikling/privat/lm-ai/mcp/yolo-ffmpeg-mcp/haiku-mcp-ts"
        
        if os.path.exists(os.path.join(default_path, "dist", "server.js")):
            return default_path
        
        # Fallback search
        possible_paths = [
            "../haiku-mcp-ts",
            "../../haiku-mcp-ts",
            os.path.expanduser("~/haiku-mcp-ts")
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "dist", "server.js")):
                return os.path.abspath(path)
        
        raise FileNotFoundError("Haiku MCP server not found")
    
    async def process_komposition_markdown(self, komposition_md: str, 
                                         output_path: str, 
                                         creative_direction: str = None,
                                         session_id: str = None) -> Dict[str, Any]:
        """
        Process komposition markdown directly with Haiku MCP.
        
        Args:
            komposition_md: Full komposition markdown content
            output_path: Path for final video output
            creative_direction: Optional creative instructions for Haiku
            
        Returns:
            Processing result with success status and details
        """
        try:
            # Enhance komposition with creative direction if provided
            enhanced_markdown = self._enhance_markdown_with_creative_direction(
                komposition_md, creative_direction
            )
            
            # Log the enhanced komposition being sent to Haiku
            if self.interaction_logger:
                self.interaction_logger.log_llm2_call(
                    purpose="Generate FFmpeg commands from komposition markdown",
                    request=enhanced_markdown,
                    model="haiku_markdown_processor",
                    session_id=session_id or "unknown"
                )
            
            # Send markdown directly to Haiku MCP
            result = await self._process_with_haiku_mcp(enhanced_markdown, output_path)
            
            # Log Haiku's response
            if self.interaction_logger and result.get("success"):
                commands = result.get("ffmpeg_commands", [])
                self.interaction_logger.log_llm2_response(
                    session_id=getattr(self, 'session_id', 'unknown'),
                    call_id="markdown_komposition_process", 
                    response=f"Generated {len(commands)} FFmpeg commands for markdown komposition",
                    commands_generated=commands
                )
                
                # Log each command execution
                for cmd in commands:
                    self.interaction_logger.log_ffmpeg_command(
                        command=cmd,
                        purpose="Process komposition from markdown"
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process markdown komposition: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Markdown komposition processing failed"
            }
    
    def _enhance_markdown_with_creative_direction(self, komposition_md: str, 
                                                creative_direction: str = None) -> str:
        """Enhance komposition markdown with creative direction for Haiku."""
        enhanced = komposition_md
        
        if creative_direction:
            enhanced += f"\n\n## Creative Direction\n{creative_direction}\n"
        
        # Add processing instructions for Haiku
        enhanced += """

## Processing Instructions for Haiku

Please generate FFmpeg commands to create this music video based on the komposition above:

1. **Extract Media Sources**: Look for media file references (like "media_001 (filename.mp4)") and use the actual file paths
2. **File Path Resolution**: Convert media references to full paths in /tmp/music/source/
3. **Apply Creative Effects**: Implement the creative direction and effects specified
4. **Timing and Duration**: Respect the BPM, segment timing, and total duration
5. **Output Format**: Create a single final video file in MP4 format

Return the generated FFmpeg commands as a JSON array.
"""
        
        return enhanced
    
    async def _process_with_haiku_mcp(self, enhanced_markdown: str, 
                                    output_path: str) -> Dict[str, Any]:
        """Send enhanced markdown to Haiku MCP for processing."""
        try:
            # Extract media files first to understand what we're working with
            media_files = self.extract_media_files_from_markdown(enhanced_markdown)
            
            if not media_files:
                return {
                    "success": False, 
                    "error": "No media files found in komposition markdown",
                    "validation_blocked": True
                }
            
            # Check if we have video + audio or just video files
            video_files = [f for f in media_files if f["extension"].lower() in ["mp4", "avi", "mov", "mkv"]]
            audio_files = [f for f in media_files if f["extension"].lower() in ["mp3", "wav", "flac", "m4a"]]
            
            if video_files and audio_files:
                # Use create_music_video tool for video + audio combination
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "create_music_video",
                        "arguments": {
                            "video_file": video_files[0]["full_path"],
                            "audio_file": audio_files[0]["full_path"],
                            "output_file": output_path,
                            "duration": 30  # Default duration from komposition examples
                        }
                    }
                }
            elif video_files:
                # Use process_video_file tool for video-only processing
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "process_video_file",
                        "arguments": {
                            "input_file": video_files[0]["full_path"],
                            "output_file": output_path,
                            "operation": "create_music_video_from_markdown",
                            "parameters": {
                                "komposition_markdown": enhanced_markdown,
                                "duration": 30
                            }
                        }
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No valid video files found for processing",
                    "validation_blocked": True
                }
            
            # Execute MCP call
            result = await self._execute_mcp_call(mcp_request)
            return result
            
        except Exception as e:
            logger.error(f"Haiku MCP processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_mcp_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP call to Haiku server."""
        try:
            server_js = os.path.join(self.haiku_server_path, "dist", "server.js")
            
            # Start Haiku MCP server
            process = await asyncio.create_subprocess_exec(
                "node", server_js,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.haiku_server_path
            )
            
            # Send request
            request_json = json.dumps(request) + "\n"
            stdout, stderr = await process.communicate(request_json.encode())
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Haiku MCP server error: {error_msg}")
                return {"success": False, "error": f"Server error: {error_msg}"}
            
            # Parse response
            response_text = stdout.decode().strip()
            if not response_text:
                return {"success": False, "error": "Empty response from Haiku MCP"}
            
            try:
                response = json.loads(response_text)
                
                # Extract result from MCP response
                if "result" in response and "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    try:
                        # Try to parse as JSON first (structured response)
                        result = json.loads(content)
                        if isinstance(result, dict):
                            # If it's already a proper result dict, return it
                            if "success" in result:
                                return result
                            else:
                                # Wrap in success format
                                return {
                                    "success": True,
                                    "haiku_result": result,
                                    "ffmpeg_commands": result.get("commands", [])
                                }
                        else:
                            # If it's not a dict, treat as message
                            return {
                                "success": True, 
                                "message": str(result),
                                "haiku_response": content
                            }
                    except json.JSONDecodeError:
                        # If content is not JSON, treat as plain text response
                        return {
                            "success": True,
                            "message": content,
                            "haiku_response": content
                        }
                elif "error" in response:
                    return {"success": False, "error": response["error"]["message"]}
                else:
                    return {"success": False, "error": "Invalid MCP response format"}
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Haiku response: {response_text}")
                return {"success": False, "error": f"Invalid JSON response: {e}"}
                
        except Exception as e:
            logger.error(f"MCP call execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def extract_media_files_from_markdown(self, komposition_md: str) -> List[Dict[str, str]]:
        """Extract media file references from komposition markdown."""
        media_files = []
        
        # Pattern to match media references like "media_001 (filename.mp4)"
        media_pattern = r'media_(\w+)\s*\(([^)]+\.(mp4|avi|mov|mkv|mp3|wav|flac|m4a))\)'
        
        matches = re.findall(media_pattern, komposition_md, re.IGNORECASE)
        
        for media_id, filename, ext in matches:
            media_files.append({
                "media_id": f"media_{media_id}",
                "filename": filename,
                "extension": ext,
                "full_path": f"/tmp/music/source/{filename}"
            })
        
        return media_files
    
    def validate_media_availability(self, media_files: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate that referenced media files are available."""
        validation_result = {
            "all_available": True,
            "available_files": [],
            "missing_files": [],
            "total_files": len(media_files)
        }
        
        for media_file in media_files:
            file_path = media_file["full_path"]
            if os.path.exists(file_path):
                validation_result["available_files"].append(media_file)
            else:
                validation_result["missing_files"].append(media_file)
                validation_result["all_available"] = False
        
        return validation_result


def create_markdown_haiku_processor() -> MarkdownHaikuProcessor:
    """Factory function to create markdown Haiku processor."""
    return MarkdownHaikuProcessor()


# For testing
async def test_markdown_processing():
    """Test markdown komposition processing."""
    processor = create_markdown_haiku_processor()
    
    test_komposition = """# Test Music Video Komposition

## Basic Parameters
- **Title**: Test Markdown Processing
- **Duration**: 30 seconds
- **BPM**: 120
- **Style**: Vintage with smooth transitions

## Segments

### Segment 1: Intro (0-10s)
- **Source**: media_001 (JJVtt947FfI_136.mp4)
- **Effects**: Vintage filter, slight grain
- **Duration**: 10 seconds

### Segment 2: Main (10-30s)
- **Source**: media_001 (JJVtt947FfI_136.mp4)
- **Effects**: Contrast boost, fast cuts
- **Duration**: 20 seconds
"""
    
    # Extract media files
    media_files = processor.extract_media_files_from_markdown(test_komposition)
    print(f"Found media files: {media_files}")
    
    # Validate availability
    validation = processor.validate_media_availability(media_files)
    print(f"Media validation: {validation}")
    
    # Test processing (would need actual Haiku MCP server)
    # result = await processor.process_komposition_markdown(
    #     test_komposition, 
    #     "/tmp/test_output.mp4",
    #     "Apply vintage effects with smooth transitions"
    # )
    # print(f"Processing result: {result}")


if __name__ == "__main__":
    asyncio.run(test_markdown_processing())