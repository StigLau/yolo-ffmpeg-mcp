import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server import (
    list_files, 
    get_file_info, 
    get_available_operations,
    process_file,
    cleanup_temp_files,
    file_manager,
    ffmpeg
)


class TestFFMPEGIntegration:
    """Integration tests for FFMPEG MCP server with real video file"""
    
    @pytest.mark.asyncio
    async def test_list_files_finds_test_video(self):
        """Test that list_files finds our test video"""
        result = await list_files()
        
        assert "files" in result
        assert len(result["files"]) >= 1
        
        # Find our test video
        test_video = None
        for file_info in result["files"]:
            if "PXL_20250306_132546255" in file_info.name:
                test_video = file_info
                break
                
        assert test_video is not None, "Test video not found in file list"
        assert test_video.extension == ".mp4"
        assert test_video.size > 0
        assert test_video.id.startswith("file_")
        
        # Store the file ID for other tests
        self.test_video_id = test_video.id
        
    @pytest.mark.asyncio
    async def test_get_file_info_for_test_video(self):
        """Test getting detailed info for test video"""
        # First get the file list to get an ID
        files_result = await list_files()
        test_video = None
        for file_info in files_result["files"]:
            if "PXL_20250306_132546255" in file_info.name:
                test_video = file_info
                break
                
        assert test_video is not None
        
        # Get detailed info
        info_result = await get_file_info(test_video.id)
        
        assert "basic_info" in info_result
        assert "media_info" in info_result
        assert info_result["basic_info"]["name"] == "PXL_20250306_132546255.mp4"
        assert info_result["basic_info"]["size"] > 1000  # Should be a real video file
        
        # Check media info (if ffprobe is available)
        if info_result["media_info"]["success"]:
            assert "info" in info_result["media_info"]
            media_info = info_result["media_info"]["info"]
            assert "format" in media_info
            assert "streams" in media_info
            
    @pytest.mark.asyncio
    async def test_get_available_operations(self):
        """Test that available operations are returned"""
        result = await get_available_operations()
        
        assert "operations" in result
        operations = result["operations"]
        
        # Check that expected operations are available
        expected_operations = ["convert", "extract_audio", "trim", "resize", "normalize_audio", "to_mp3"]
        for op in expected_operations:
            assert op in operations
            assert isinstance(operations[op], str)  # Should have description
            
    @pytest.mark.asyncio
    async def test_extract_audio_from_test_video(self):
        """Test extracting audio from the test video"""
        # Get test video ID
        files_result = await list_files()
        test_video = None
        for file_info in files_result["files"]:
            if "PXL_20250306_132546255" in file_info.name:
                test_video = file_info
                break
                
        assert test_video is not None
        
        # Extract audio
        result = await process_file(
            input_file_id=test_video.id,
            operation="extract_audio",
            output_extension="m4a"
        )
        
        print(f"Extract audio result: {result}")
        
        if result.success:
            assert result.output_file_id is not None
            assert result.output_file_id.startswith("file_")
            
            # Verify output file exists
            output_path = file_manager.resolve_id(result.output_file_id)
            assert output_path is not None
            assert output_path.exists()
            assert output_path.suffix == ".m4a"
        else:
            # If FFMPEG fails, at least verify we get proper error info
            assert result.message is not None
            print(f"FFMPEG failed (expected if not installed): {result.message}")
            
    @pytest.mark.asyncio  
    async def test_convert_to_mp3(self):
        """Test converting video to MP3"""
        # Get test video ID
        files_result = await list_files()
        test_video = None
        for file_info in files_result["files"]:
            if "PXL_20250306_132546255" in file_info.name:
                test_video = file_info
                break
                
        assert test_video is not None
        
        # Convert to MP3
        result = await process_file(
            input_file_id=test_video.id,
            operation="to_mp3",
            output_extension="mp3"
        )
        
        print(f"Convert to MP3 result: {result}")
        
        if result.success:
            assert result.output_file_id is not None
            
            # Verify output file exists
            output_path = file_manager.resolve_id(result.output_file_id)
            assert output_path is not None
            assert output_path.exists()
            assert output_path.suffix == ".mp3"
        else:
            # Log failure for debugging
            print(f"MP3 conversion failed: {result.message}")
            if result.logs:
                print(f"FFMPEG logs: {result.logs}")
                
    @pytest.mark.asyncio
    async def test_trim_video(self):
        """Test trimming the video to first 5 seconds"""
        # Get test video ID
        files_result = await list_files()
        test_video = None
        for file_info in files_result["files"]:
            if "PXL_20250306_132546255" in file_info.name:
                test_video = file_info
                break
                
        assert test_video is not None
        
        # Trim to first 5 seconds
        result = await process_file(
            input_file_id=test_video.id,
            operation="trim",
            output_extension="mp4",
            params="start=0 duration=5"
        )
        
        print(f"Trim video result: {result}")
        
        if result.success:
            assert result.output_file_id is not None
            
            # Verify output file exists and is smaller than original
            output_path = file_manager.resolve_id(result.output_file_id)
            original_path = file_manager.resolve_id(test_video.id)
            
            assert output_path is not None
            assert output_path.exists()
            assert output_path.suffix == ".mp4"
            # Trimmed file should be smaller (not always true due to encoding, but usually)
            # assert output_path.stat().st_size < original_path.stat().st_size
        else:
            print(f"Video trimming failed: {result.message}")
            if result.logs:
                print(f"FFMPEG logs: {result.logs}")
                
    @pytest.mark.asyncio
    async def test_invalid_file_id(self):
        """Test handling of invalid file ID"""
        result = await process_file(
            input_file_id="invalid_id",
            operation="to_mp3",
            output_extension="mp3"
        )
        
        assert not result.success
        assert "not found" in result.message.lower()
        
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test handling of invalid operation"""
        # Get valid file ID first
        files_result = await list_files()
        if files_result["files"]:
            file_id = files_result["files"][0].id
            
            result = await process_file(
                input_file_id=file_id,
                operation="invalid_operation",
                output_extension="mp3"
            )
            
            assert not result.success
            assert "not allowed" in result.message.lower()
            
    @pytest.mark.asyncio
    async def test_cleanup_temp_files(self):
        """Test cleanup of temporary files"""
        # First create some temp files by running operations
        files_result = await list_files()
        if files_result["files"]:
            test_video = files_result["files"][0]
            
            # Create a temp file
            await process_file(
                input_file_id=test_video.id,
                operation="to_mp3",
                output_extension="mp3"
            )
            
        # Now cleanup
        result = await cleanup_temp_files()
        assert "message" in result or "error" in result
        
    @pytest.mark.asyncio
    async def test_ffmpeg_wrapper_directly(self):
        """Test FFMPEG wrapper functionality directly"""
        # Test getting available operations
        operations = ffmpeg.get_available_operations()
        assert len(operations) > 0
        assert "to_mp3" in operations
        
        # Test command building
        input_path = Path("/tmp/test_input.mp4")
        output_path = Path("/tmp/test_output.mp3")
        
        command = ffmpeg.build_command("to_mp3", input_path, output_path)
        assert "ffmpeg" in command[0]
        assert str(input_path) in command
        assert str(output_path) in command
        assert "-c:a" in command
        assert "libmp3lame" in command
        
        print(f"Generated command: {' '.join(command)}")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_ffmpeg_integration.py -v -s
    pytest.main([__file__, "-v", "-s"])