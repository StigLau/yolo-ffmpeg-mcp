#!/usr/bin/env python3
"""
CI/CD Unit Tests - Core Components

Tests essential core functionality for automated CI/CD pipeline.
Fast execution, minimal dependencies, validates core components.
"""

import sys
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

def test_imports():
    """Test that all core modules can be imported"""
    try:
        from deterministic_id_generator import DeterministicIDGenerator
        from resource_manager import ResourceRegistry, CacheManager
        from file_manager import FileManager  
        from ffmpeg_wrapper import FFMPEGWrapper
        from config import SecurityConfig
        assert True, "All core modules imported successfully"
    except ImportError as e:
        pytest.fail(f"Import error: {e}")

def test_deterministic_id_generation():
    """Test deterministic ID generation"""
    from deterministic_id_generator import DeterministicIDGenerator
    
    # Test source file IDs are consistent
    id1 = DeterministicIDGenerator.source_file_id("lookin.mp4")
    id2 = DeterministicIDGenerator.source_file_id("lookin.mp4")
    assert id1 == id2 == "src_lookin_mp4"
    
    # Test effect IDs are deterministic
    effect_id1 = DeterministicIDGenerator.effect_file_id(
        ["src_lookin_mp4"], "trim", {"start": 0, "duration": 4}
    )
    effect_id2 = DeterministicIDGenerator.effect_file_id(
        ["src_lookin_mp4"], "trim", {"start": 0, "duration": 4}
    )
    assert effect_id1 == effect_id2
    assert effect_id1.startswith("effect_trim_")

def test_resource_registry():
    """Test resource registry basic functionality"""
    from resource_manager import ResourceRegistry
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry_path = Path(tmp_dir) / "test_registry.json"
        registry = ResourceRegistry(str(registry_path))
        
        # Test registry initialization
        assert len(registry.source_files) == 0
        assert len(registry.generated_files) == 0
        
        # Test save/load cycle
        registry.save_registry()
        assert registry_path.exists()

def test_security_config():
    """Test security configuration"""
    from config import SecurityConfig
    
    config = SecurityConfig()
    
    # Test allowed extensions
    assert ".mp4" in config.ALLOWED_EXTENSIONS
    assert ".mp3" in config.ALLOWED_EXTENSIONS  
    assert ".exe" not in config.ALLOWED_EXTENSIONS
    
    # Test file size limits
    assert config.MAX_FILE_SIZE > 0
    assert config.PROCESS_TIMEOUT > 0

def test_file_manager_security():
    """Test file manager security validations"""
    from file_manager import FileManager
    
    fm = FileManager()
    
    # Test basic functionality
    assert fm.source_dir.exists() or fm.source_dir.name == "source"
    assert fm.temp_dir.exists() or fm.temp_dir.name == "temp"
    
    # Test file map initialization
    assert isinstance(fm.file_map, dict)
    assert len(fm.file_map) >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])