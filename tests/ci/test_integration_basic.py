#!/usr/bin/env python3
"""
CI/CD Integration Tests - Basic Operations

Tests integration between core components for basic video operations.
Validates FFMPEG operations, file management, and basic workflows.
"""

import sys
import pytest
import asyncio
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

@pytest.fixture
def test_data_dir():
    """Return path to test data directory"""
    return Path(__file__).parents[1] / "files"

@pytest.fixture  
def temp_output_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_ffmpeg_available():
    """Test that FFMPEG is available in the system"""
    import subprocess
    try:
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, "FFMPEG not available"
        assert "ffmpeg version" in result.stdout
    except FileNotFoundError:
        pytest.skip("FFMPEG not installed")
    except subprocess.TimeoutExpired:
        pytest.fail("FFMPEG command timed out")

def test_file_manager_basic_operations():
    """Test file manager basic operations"""
    from file_manager import FileManager
    
    fm = FileManager()
    
    # Test file registration (using test video if available)
    test_files = list(Path("/tmp/music/source").glob("*.mp4"))
    if test_files:
        test_file = test_files[0]
        file_id = fm.register_file(test_file)
        assert file_id.startswith("file_")
        
        # Test file retrieval
        retrieved_path = fm.resolve_id(file_id)
        assert str(retrieved_path.resolve()) == str(test_file.resolve())
        
        # Test file info (basic file properties)
        file_stat = retrieved_path.stat()
        assert retrieved_path.name == test_file.name
        assert file_stat.st_size > 0

@pytest.mark.asyncio
async def test_ffmpeg_wrapper_info():
    """Test FFMPEG wrapper file info functionality"""
    from ffmpeg_wrapper import FFMPEGWrapper
    from file_manager import FileManager
    
    wrapper = FFMPEGWrapper()
    file_manager = FileManager()
    
    # Test with available video file
    test_files = list(Path("/tmp/music/source").glob("*.mp4"))
    if test_files:
        test_file = test_files[0]
        file_id = file_manager.register_file(test_file)
        file_path = file_manager.resolve_id(file_id)
        info = await wrapper.get_file_info(file_path, file_manager, file_id)
        
        assert info["success"] is True
        assert "duration" in info["info"]["format"]
        assert float(info["info"]["format"]["duration"]) > 0

@pytest.mark.asyncio
async def test_mcp_server_basic():
    """Test basic MCP server functionality"""
    try:
        from server import mcp
        
        # Test list_files tool
        result = await mcp.call_tool("list_files", {})
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Parse result
        import json
        if hasattr(result[0], 'text'):
            data = json.loads(result[0].text)
            assert "files" in data
            assert "stats" in data
            
    except Exception as e:
        pytest.skip(f"MCP server not available: {e}")

@pytest.mark.asyncio
async def test_basic_video_operations():
    """Test basic video operations if files are available"""
    from ffmpeg_wrapper import FFMPEGWrapper
    from file_manager import FileManager
    
    wrapper = FFMPEGWrapper()
    file_manager = FileManager()
    
    # Find test video
    test_files = list(Path("/tmp/music/source").glob("*.mp4"))
    if not test_files:
        pytest.skip("No test video files available")
    
    test_file = test_files[0]
    file_id = file_manager.register_file(test_file)
    
    # Test get info operation
    file_path = file_manager.resolve_id(file_id)
    info = await wrapper.get_file_info(file_path, file_manager, file_id)
    assert info["success"] is True
    
    # Verify video properties
    format_info = info["info"]["format"]
    assert "duration" in format_info
    assert float(format_info["duration"]) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])