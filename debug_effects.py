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
        
        # Check if we can find any files
        source_dir = Path("/tmp/music/source")
        if source_dir.exists():
            files = list(source_dir.glob("*.mp4"))
            if files:
                # Register a file manually
                file_id = file_manager.register_file(files[0])
                print(f"Testing with file: {file_id} ({files[0].name})")
                
                # Try to apply effect
                result = await effect_processor.apply_effect(
                    file_id=file_id,
                    effect_name="vintage_color",
                    parameters={"intensity": 0.8}
                )
                
                # If failed, try to get more detailed error
                if not result.get("success"):
                    print("Effect failed, trying direct FFmpeg test...")
                    # Test FFmpeg directly
                    source_path = file_manager.resolve_id(file_id)
                    print(f"Source path: {source_path}")
                    
                    # Test basic FFmpeg command
                    test_cmd = [
                        str(ffmpeg.ffmpeg_path),
                        "-i", str(source_path),
                        "-t", "1",  # Just 1 second for test
                        "-y",
                        "/tmp/music/temp/test_output.mp4"
                    ]
                    print(f"Test command: {' '.join(test_cmd)}")
                    
                    ffmpeg_result = await ffmpeg.execute_command(test_cmd)
                    print(f"Direct FFmpeg test result: {ffmpeg_result}")
            else:
                print("No MP4 files found in source directory")
                return
        else:
            print("Source directory not found")
            return
        
        print("Result:", result)
        
    except Exception as e:
        print("Error occurred:")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_effect())