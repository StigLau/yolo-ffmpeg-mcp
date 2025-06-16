#!/usr/bin/env python3
"""
Test suite for FormatManager - aspect ratio and cropping management
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from format_manager import FormatManager, AspectRatio, CropMode, FormatSpec, COMMON_PRESETS


class TestFormatManager:
    """Test format management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.format_manager = FormatManager()
        self.test_files_dir = Path(__file__).parent / "files"
    
    def test_aspect_ratio_enum(self):
        """Test AspectRatio enum values"""
        assert AspectRatio.LANDSCAPE_16_9.display_name == "16:9"
        assert AspectRatio.PORTRAIT_9_16.display_name == "9:16"
        assert AspectRatio.SQUARE_1_1.display_name == "1:1"
        
        # Test numeric ratios
        assert abs(AspectRatio.LANDSCAPE_16_9.numeric_ratio - (16/9)) < 0.01
        assert abs(AspectRatio.SQUARE_1_1.numeric_ratio - 1.0) < 0.01
    
    def test_crop_mode_enum(self):
        """Test CropMode enum values"""
        assert CropMode.CENTER_CROP.value == "center_crop"
        assert CropMode.SCALE_LETTERBOX.value == "scale_letterbox"
        assert CropMode.SCALE_BLUR_BG.value == "scale_blur_bg"
    
    def test_format_spec_properties(self):
        """Test FormatSpec dataclass properties"""
        spec = FormatSpec(AspectRatio.LANDSCAPE_16_9, (1920, 1080), CropMode.CENTER_CROP)
        
        assert spec.width == 1920
        assert spec.height == 1080
        assert spec.orientation == "landscape"
        
        # Test portrait
        spec_portrait = FormatSpec(AspectRatio.PORTRAIT_9_16, (1080, 1920), CropMode.CENTER_CROP)
        assert spec_portrait.orientation == "portrait"
        
        # Test square
        spec_square = FormatSpec(AspectRatio.SQUARE_1_1, (1080, 1080), CropMode.CENTER_CROP)
        assert spec_square.orientation == "square"
    
    def test_common_presets(self):
        """Test that common presets are properly configured"""
        assert "youtube_landscape" in COMMON_PRESETS
        assert "instagram_square" in COMMON_PRESETS
        assert "tiktok_vertical" in COMMON_PRESETS
        
        youtube_preset = COMMON_PRESETS["youtube_landscape"]
        assert youtube_preset.aspect_ratio == AspectRatio.LANDSCAPE_16_9
        assert youtube_preset.resolution == (1920, 1080)
        
        instagram_preset = COMMON_PRESETS["instagram_square"]
        assert instagram_preset.aspect_ratio == AspectRatio.SQUARE_1_1
        assert instagram_preset.resolution == (1080, 1080)
    
    def test_suggest_crop_mode(self):
        """Test crop mode suggestion logic"""
        # Test very wide (landscape)
        suggested = self.format_manager._suggest_crop_mode(1920, 720, 1920/720)  # 2.67 ratio
        assert suggested == CropMode.CENTER_CROP
        
        # Test very tall (portrait)
        suggested = self.format_manager._suggest_crop_mode(720, 1920, 720/1920)  # 0.375 ratio
        assert suggested == CropMode.TOP_CROP
        
        # Test nearly square
        suggested = self.format_manager._suggest_crop_mode(1080, 1080, 1.0)
        assert suggested == CropMode.CENTER_CROP
        
        # Test moderate mismatch
        suggested = self.format_manager._suggest_crop_mode(1280, 1024, 1280/1024)  # 1.25 ratio
        assert suggested == CropMode.SMART_CROP
    
    def test_rate_crop_compatibility(self):
        """Test crop compatibility rating"""
        # Test landscape video
        ratings = self.format_manager._rate_crop_compatibility(1920, 1080, 1920/1080)
        
        assert "excellent" in ratings[CropMode.CENTER_CROP]
        assert "excellent" in ratings[CropMode.SCALE_LETTERBOX]
        assert ratings[CropMode.SCALE_STRETCH] in ["poor", "fair"]
        
        # Test portrait video
        ratings = self.format_manager._rate_crop_compatibility(1080, 1920, 1080/1920)
        assert "excellent" in ratings[CropMode.TOP_CROP]
    
    def test_generate_ffmpeg_filters(self):
        """Test FFmpeg filter generation"""
        from format_manager import VideoAnalysis
        
        # Create mock analysis
        analysis = VideoAnalysis(
            file_id="test",
            width=1920,
            height=1080,
            duration=10.0,
            fps=30.0,
            aspect_ratio=1920/1080,
            suggested_crop_mode=CropMode.CENTER_CROP,
            crop_compatibility={}
        )
        
        # Test center crop
        target_format = FormatSpec(AspectRatio.SQUARE_1_1, (1080, 1080), CropMode.CENTER_CROP)
        filters = self.format_manager._generate_ffmpeg_filters(analysis, target_format)
        
        assert len(filters) >= 2
        assert any("scale=" in f for f in filters)
        assert any("crop=" in f for f in filters)
        
        # Test letterbox
        target_format = FormatSpec(AspectRatio.SQUARE_1_1, (1080, 1080), CropMode.SCALE_LETTERBOX)
        filters = self.format_manager._generate_ffmpeg_filters(analysis, target_format)
        
        assert any("pad=" in f for f in filters)
        
        # Test blur background
        target_format = FormatSpec(AspectRatio.SQUARE_1_1, (1080, 1080), CropMode.SCALE_BLUR_BG)
        filters = self.format_manager._generate_ffmpeg_filters(analysis, target_format)
        
        assert any("gblur" in f for f in filters)
        assert any("overlay" in f for f in filters)
    
    def test_needs_conversion(self):
        """Test conversion requirement detection"""
        from format_manager import VideoAnalysis
        
        analysis = VideoAnalysis(
            file_id="test",
            width=1920,
            height=1080,
            duration=10.0,
            fps=30.0,
            aspect_ratio=1920/1080,
            suggested_crop_mode=CropMode.CENTER_CROP,
            crop_compatibility={}
        )
        
        # Same format - no conversion needed
        same_format = FormatSpec(AspectRatio.LANDSCAPE_16_9, (1920, 1080), CropMode.CENTER_CROP)
        assert not self.format_manager._needs_conversion(analysis, same_format)
        
        # Different resolution - conversion needed
        diff_format = FormatSpec(AspectRatio.SQUARE_1_1, (1080, 1080), CropMode.CENTER_CROP)
        assert self.format_manager._needs_conversion(analysis, diff_format)
    
    def test_suggest_target_format_empty(self):
        """Test target format suggestion with empty input"""
        result = self.format_manager.suggest_target_format([])
        
        # Should return default landscape format
        assert result.aspect_ratio == AspectRatio.LANDSCAPE_16_9
        assert result.resolution == (1920, 1080)
    
    def test_suggest_target_format_mixed_orientations(self):
        """Test target format suggestion with mixed orientations"""
        from format_manager import VideoAnalysis
        
        analyses = [
            VideoAnalysis("vid1", 1920, 1080, 10.0, 30.0, 1920/1080, CropMode.CENTER_CROP, {}),  # Landscape
            VideoAnalysis("vid2", 1080, 1920, 10.0, 30.0, 1080/1920, CropMode.TOP_CROP, {}),    # Portrait
            VideoAnalysis("vid3", 1080, 1080, 10.0, 30.0, 1.0, CropMode.CENTER_CROP, {})        # Square
        ]
        
        result = self.format_manager.suggest_target_format(analyses)
        
        # Should pick dominant orientation (landscape in this case if algorithm weights first)
        assert result.crop_mode == CropMode.SCALE_BLUR_BG  # Mixed orientations should use blur background


@pytest.mark.skipif(not os.path.exists("/usr/bin/ffmpeg"), reason="FFmpeg not available")
class TestFormatManagerWithFFmpeg:
    """Tests that require FFmpeg to be installed"""
    
    def setup_method(self):
        """Set up test environment"""
        self.format_manager = FormatManager()
        self.test_files_dir = Path(__file__).parent / "files"
    
    def test_analyze_video_format_missing_file(self):
        """Test video format analysis with missing file"""
        with pytest.raises(RuntimeError):
            self.format_manager.analyze_video_format("/nonexistent/file.mp4", "test")
    
    @pytest.mark.skipif(True, reason="Requires actual test video file")
    def test_analyze_video_format_real_file(self):
        """Test video format analysis with real file (if available)"""
        # This test would need an actual video file in tests/files/
        test_video = self.test_files_dir / "test_video.mp4"
        if not test_video.exists():
            pytest.skip("No test video file available")
        
        analysis = self.format_manager.analyze_video_format(str(test_video), "test")
        
        assert analysis.file_id == "test"
        assert analysis.width > 0
        assert analysis.height > 0
        assert analysis.duration > 0
        assert analysis.fps > 0
        assert analysis.aspect_ratio > 0
        assert analysis.suggested_crop_mode in CropMode
        assert isinstance(analysis.crop_compatibility, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])