#!/usr/bin/env python3
"""
Debug script to test video effects directly
"""

import asyncio
import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ffmpeg_wrapper import FFMPEGWrapper
from file_manager import FileManager
from effect_processor import EffectProcessor

async def test_effect():
    try:
        # Create components
        ffmpeg = FFMPEGWrapper()
        file_manager = FileManager()
        effect_processor = EffectProcessor(ffmpeg, file_manager)
        
        print("Created effect processor successfully")
        
        # Use a test file ID that we know exists
        file_id = "file_169e6350"  # From the MCP response we saw earlier
        print(f"Testing with file: {file_id}")
        
        # Try to apply effect
        result = await effect_processor.apply_effect(
            file_id=file_id,
            effect_name="vintage_color",
            parameters={"intensity": 0.8}
        )
        
        print("Result:", result)
        
    except Exception as e:
        print("Error occurred:")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_effect())