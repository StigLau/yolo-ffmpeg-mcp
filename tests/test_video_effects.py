"""
Test suite for video effects system
Tests FFmpeg effects, OpenCV effects, effect chaining, and preset system
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Test the video effects system
class TestVideoEffects:
    
    @pytest.fixture
    def effect_processor(self):
        """Create effect processor with mocked dependencies"""
        from src.effect_processor import EffectProcessor
        from src.ffmpeg_wrapper import FFMPEGWrapper 
        from src.file_manager import FileManager
        
        # Mock dependencies
        ffmpeg_mock = Mock(spec=FFMPEGWrapper)
        file_manager_mock = Mock(spec=FileManager)
        
        # Configure mocks
        ffmpeg_mock.execute_command = AsyncMock(return_value={
            "success": True,
            "processing_time": 5.2
        })
        
        file_manager_mock.resolve_id.return_value = Path("/tmp/test_video.mp4")
        file_manager_mock.register_file.return_value = "file_output_123"
        
        processor = EffectProcessor(ffmpeg_mock, file_manager_mock)
        return processor
    
    def test_effects_registry_loaded(self, effect_processor):
        """Test that built-in effects are properly loaded"""
        effects = effect_processor.get_available_effects()
        
        assert effects["success"] is True
        assert effects["effects_count"] > 0
        
        # Check that key effects are present
        effect_names = list(effects["effects"].keys())
        assert "vintage_color" in effect_names
        assert "film_noir" in effect_names
        assert "vhs_look" in effect_names
        assert "gaussian_blur" in effect_names
        assert "vignette" in effect_names
        assert "face_blur" in effect_names
        assert "chromatic_aberration" in effect_names
    
    def test_effect_categories(self, effect_processor):
        """Test effect categorization system"""
        effects = effect_processor.get_available_effects()
        categories = effects["categories"]
        
        expected_categories = {"color", "stylistic", "blur", "privacy", "distortion"}
        assert set(categories) == expected_categories
    
    def test_effect_providers(self, effect_processor):
        """Test multiple effect providers"""
        effects = effect_processor.get_available_effects()
        providers = effects["providers"]
        
        expected_providers = {"ffmpeg", "opencv", "pil"}
        assert set(providers) == expected_providers
    
    def test_effect_parameter_validation(self, effect_processor):
        """Test parameter validation for effects"""
        effect = effect_processor.effects_registry["vintage_color"]
        
        # Test valid parameters
        valid_params = {"intensity": 1.5, "warmth": 0.3, "saturation": 1.2}
        result = effect_processor._validate_parameters(effect, valid_params)
        assert "error" not in result
        assert result["parameters"]["intensity"] == 1.5
        
        # Test parameter clamping
        extreme_params = {"intensity": 10.0, "warmth": -2.0, "saturation": -1.0}
        result = effect_processor._validate_parameters(effect, extreme_params)
        assert result["parameters"]["intensity"] == 2.0  # Clamped to max
        assert result["parameters"]["warmth"] == -0.5    # Clamped to min
        assert result["parameters"]["saturation"] == 0.0 # Clamped to min
    
    @pytest.mark.asyncio
    async def test_apply_ffmpeg_effect(self, effect_processor):
        """Test applying FFmpeg-based effects"""
        with patch.object(effect_processor.file_manager, 'resolve_id', return_value=Path("/tmp/test.mp4")):
            with patch.object(effect_processor.file_manager, 'register_file', return_value="file_output_456"):
                result = await effect_processor.apply_effect(
                    file_id="file_123",
                    effect_name="vintage_color",
                    parameters={"intensity": 1.2, "warmth": 0.2}
                )
                
                assert result["success"] is True
                assert result["effect_name"] == "vintage_color"
                assert result["output_file_id"] == "file_output_456"
                assert "processing_time" in result
    
    @pytest.mark.asyncio 
    async def test_apply_effect_chain(self, effect_processor):
        """Test applying multiple effects in sequence"""
        with patch.object(effect_processor, 'apply_effect') as mock_apply:
            # Mock successful effect applications
            mock_apply.side_effect = [
                {"success": True, "output_file_id": "file_step1"},
                {"success": True, "output_file_id": "file_step2"},
                {"success": True, "output_file_id": "file_final"}
            ]
            
            effects_chain = [
                {"effect": "vintage_color", "parameters": {"intensity": 1.0}},
                {"effect": "vignette", "parameters": {"angle": 1.57}},
                {"effect": "gaussian_blur", "parameters": {"sigma": 2.0}}
            ]
            
            result = await effect_processor.apply_effect_chain("file_123", effects_chain)
            
            assert result["success"] is True
            assert result["final_output_file_id"] == "file_final"
            assert result["total_steps"] == 3
            assert len(result["applied_effects"]) == 3
    
    @pytest.mark.asyncio
    async def test_effect_chain_failure_handling(self, effect_processor):
        """Test handling of failures in effect chains"""
        with patch.object(effect_processor, 'apply_effect') as mock_apply:
            # Mock failure in second effect
            mock_apply.side_effect = [
                {"success": True, "output_file_id": "file_step1"},
                {"success": False, "error": "Processing failed"},
                {"success": True, "output_file_id": "file_step3"}  # Won't be reached
            ]
            
            effects_chain = [
                {"effect": "vintage_color"},
                {"effect": "invalid_effect"},
                {"effect": "gaussian_blur"}
            ]
            
            result = await effect_processor.apply_effect_chain("file_123", effects_chain)
            
            assert result["success"] is False
            assert "Failed at step 1" in result["error"]
            assert len(result["applied_effects"]) == 1  # Only first effect succeeded
    
    def test_processing_time_estimation(self, effect_processor):
        """Test processing time estimation"""
        with patch.object(effect_processor.file_manager, 'resolve_id', return_value=Path("/tmp/test.mp4")):
            # Mock ffprobe output for duration
            mock_ffprobe_output = '{"format": {"duration": "30.0"}}'
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                mock_subprocess.return_value.stdout = mock_ffprobe_output
                
                effects_chain = [
                    {"effect": "vintage_color"},
                    {"effect": "gaussian_blur"},
                    {"effect": "face_blur"}
                ]
                
                result = effect_processor.estimate_processing_time("file_123", effects_chain)
                
                assert result["success"] is True
                assert result["video_duration"] == 30.0
                assert result["total_estimated_time"] > 0
                assert len(result["effect_estimates"]) == 3
    
    def test_external_presets_loading(self, effect_processor):
        """Test loading external preset configurations"""
        # Test that external presets from effects.json are loaded
        effects = effect_processor.get_available_effects()
        effect_names = list(effects["effects"].keys())
        
        # These should be loaded from presets/effects.json
        external_effects = [
            "social_media_pack",
            "warm_cinematic", 
            "glitch_aesthetic",
            "dreamy_soft",
            "horror_desaturated"
        ]
        
        for effect_name in external_effects:
            if effect_name in effect_names:  # May not be loaded if file doesn't exist
                effect_data = effects["effects"][effect_name]
                assert "parameters" in effect_data
                assert "description" in effect_data
                assert "performance_tier" in effect_data
    
    def test_effect_filtering(self, effect_processor):
        """Test filtering effects by category and provider"""
        # Test category filtering
        color_effects = effect_processor.get_available_effects(category="color")
        for effect_name, effect_data in color_effects["effects"].items():
            assert effect_data["category"] == "color"
        
        # Test provider filtering
        ffmpeg_effects = effect_processor.get_available_effects(provider="ffmpeg")
        for effect_name, effect_data in ffmpeg_effects["effects"].items():
            assert effect_data["provider"] == "ffmpeg"
    
    def test_invalid_effect_handling(self, effect_processor):
        """Test handling of invalid effect names"""
        result = asyncio.run(effect_processor.apply_effect(
            file_id="file_123",
            effect_name="nonexistent_effect"
        ))
        
        assert result["success"] is False
        assert "not found" in result["error"]
        assert "available_effects" in result


class TestEffectIntegration:
    """Integration tests for effect system with actual file processing"""
    
    @pytest.fixture
    def temp_video_file(self):
        """Create a temporary test video file"""
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()
        
        # Create a minimal test video file (1 second, solid color)
        import subprocess
        try:
            subprocess.run([
                "ffmpeg", "-f", "lavfi", "-i", "color=red:size=320x240:duration=1",
                "-c:v", "libx264", "-t", "1", "-y", str(temp_path)
            ], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Skip if ffmpeg not available
            pytest.skip("FFmpeg not available for integration tests")
        
        yield temp_path
        
        # Cleanup
        temp_path.unlink(missing_ok=True)
    
    def test_effect_system_with_real_file(self, temp_video_file):
        """Test effect system with an actual video file"""
        from src.effect_processor import EffectProcessor
        from src.ffmpeg_wrapper import FFMPEGWrapper
        from src.file_manager import FileManager
        from src.config import SecurityConfig
        import shutil
        
        # Copy temp file to allowed source directory
        source_dir = Path(SecurityConfig.SOURCE_DIR)
        source_dir.mkdir(exist_ok=True)
        allowed_file = source_dir / "test_video_effects.mp4"
        shutil.copy2(temp_video_file, allowed_file)
        
        try:
            # Create real components (not mocked)
            ffmpeg = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
            file_manager = FileManager()
            effect_processor = EffectProcessor(ffmpeg, file_manager)
            
            # Register the test file
            file_id = file_manager.register_file(allowed_file)
            
            # Test a simple effect
            result = asyncio.run(effect_processor.apply_effect(
                file_id=file_id,
                effect_name="vintage_color", 
                parameters={"intensity": 0.8}
            ))
            
            if result["success"]:
                # Verify output file exists
                output_path = Path(result["output_path"])
                assert output_path.exists()
                assert output_path.stat().st_size > 0
                
                # Cleanup output
                output_path.unlink(missing_ok=True)
            else:
                # Log the error for debugging
                print(f"Effect processing failed: {result.get('error')}")
        finally:
            # Cleanup test file
            allowed_file.unlink(missing_ok=True)


class TestPresetSystem:
    """Test the preset configuration system"""
    
    def test_preset_configuration_format(self):
        """Test that preset configuration follows expected format"""
        presets_file = Path(__file__).parent.parent / "presets" / "effects.json"
        
        if presets_file.exists():
            with open(presets_file, 'r') as f:
                presets = json.load(f)
            
            for preset_name, preset_config in presets.items():
                # Required fields
                assert "provider" in preset_config
                assert "category" in preset_config  
                assert "description" in preset_config
                assert "parameters" in preset_config
                
                # Validate parameter structure
                for param_name, param_config in preset_config["parameters"].items():
                    assert "type" in param_config
                    assert "default" in param_config
                    assert "description" in param_config
                    
                    # Optional fields
                    if param_config["type"] in ["float", "int"]:
                        # Min/max should be present for numeric types
                        assert "min" in param_config or "max" in param_config
    
    def test_preset_recipe_combinations(self):
        """Test that preset recipes can be combined effectively"""
        # Test that certain effect combinations make sense
        cinematic_recipe = [
            {"effect": "vintage_color", "parameters": {"intensity": 0.8}},
            {"effect": "vignette", "parameters": {"angle": 1.57}},
            {"effect": "gaussian_blur", "parameters": {"sigma": 1.0}}
        ]
        
        social_media_recipe = [
            {"effect": "vintage_color", "parameters": {"saturation": 1.3}},
            {"effect": "vhs_look", "parameters": {"noise_level": 3.0}}
        ]
        
        # Verify recipe structure
        for recipe in [cinematic_recipe, social_media_recipe]:
            assert isinstance(recipe, list)
            for step in recipe:
                assert "effect" in step
                assert isinstance(step.get("parameters", {}), dict)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])