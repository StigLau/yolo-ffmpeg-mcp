#!/usr/bin/env python3
"""
Minimal FFMPEG MCP Server - Core functionality only
Tests Docker packaging and basic MCP functionality without video effects
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

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
mcp = FastMCP("FFMPEG MCP Server - Minimal")

# Initialize components (no video effects dependencies)
file_manager = FileManager()
ffmpeg_wrapper = FFMPEGWrapper()
security_config = SecurityConfig()

# Ensure temp directories exist
os.makedirs("/tmp/music/source", exist_ok=True)
os.makedirs("/tmp/music/temp", exist_ok=True)
os.makedirs("/tmp/music/finished", exist_ok=True)

@mcp.tool()
async def list_files() -> Dict[str, Any]:
    """List source files with secure IDs and smart suggestions"""
    return file_manager.list_files()

@mcp.tool()
async def get_file_info(file_id: str) -> Dict[str, Any]:
    """Get detailed metadata for a file by ID"""
    return await ffmpeg_wrapper.get_file_info(file_id, file_manager)

@mcp.tool()
async def get_available_operations() -> Dict[str, Any]:
    """Get list of available FFMPEG operations"""
    return ffmpeg_wrapper.get_available_operations()

@mcp.tool()
async def process_file(
    input_file_id: str,
    operation: str,
    output_extension: str = "mp4",
    params: str = ""
) -> Dict[str, Any]:
    """Process a file using FFMPEG with specified operation"""
    return await ffmpeg_wrapper.process_file(
        input_file_id, operation, output_extension, params, file_manager
    )

@mcp.tool()
async def list_generated_files() -> Dict[str, Any]:
    """List all generated/processed files in temp directory with metadata"""
    return file_manager.list_generated_files()

@mcp.tool()
async def cleanup_temp_files() -> Dict[str, Any]:
    """Clean up temporary files"""
    return file_manager.cleanup_temp_files()

if __name__ == "__main__":
    import sys
    
    # Check if running in Docker (has access to port 8000)
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run as HTTP server for Docker testing (via FastMCP)
        mcp.run()
    else:
        # Run as stdio for MCP protocol
        mcp.run(transport="stdio")