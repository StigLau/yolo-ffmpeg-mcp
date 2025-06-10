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
except ImportError:
    from file_manager import FileManager
    from ffmpeg_wrapper import FFMPEGWrapper
    from config import SecurityConfig


# Initialize MCP server
mcp = FastMCP("ffmpeg-mcp")

# Initialize components
file_manager = FileManager()
ffmpeg = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)


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
async def list_files() -> Dict[str, List[FileInfo]]:
    """List available source files"""
    files = []
    
    try:
        source_dir = SecurityConfig.SOURCE_DIR
        if not source_dir.exists():
            source_dir.mkdir(parents=True, exist_ok=True)
            
        for file_path in source_dir.glob("*"):
            if file_path.is_file() and SecurityConfig.validate_extension(file_path):
                try:
                    file_id = file_manager.register_file(file_path)
                    files.append(FileInfo(
                        id=file_id,
                        name=file_path.name,
                        size=file_path.stat().st_size,
                        extension=file_path.suffix.lower()
                    ))
                except Exception:
                    continue
                    
    except Exception as e:
        return {"error": f"Failed to list files: {str(e)}", "files": []}
        
    return {"files": files}


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
    
    # Get detailed media info using ffprobe
    media_info = await ffmpeg.get_file_info(file_path)
    
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
    **params
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
        # Create output file
        output_file_id, output_path = file_manager.create_temp_file(output_extension)
        
        # Build and execute command
        command = ffmpeg.build_command(operation, input_path, output_path, **params)
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
async def cleanup_temp_files() -> Dict[str, str]:
    """Clean up temporary files"""
    try:
        file_manager.cleanup_temp_files()
        return {"message": "Temporary files cleaned up successfully"}
    except Exception as e:
        return {"error": f"Failed to cleanup temp files: {str(e)}"}


# Run the server
if __name__ == "__main__":
    mcp.run()