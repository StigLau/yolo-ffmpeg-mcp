"""
Test Speech Detection Functionality

Tests the speech detection module and MCP tools with both
successful detection scenarios and fallback behavior.
"""

import pytest
import asyncio
from pathlib import Path
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from speech_detector import SpeechDetector, SileroVAD, SpeechDetectionError
from server import detect_speech_segments, get_speech_insights
import file_manager

class TestSpeechDetector:
    """Test the SpeechDetector class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.detector = SpeechDetector()
        
    def test_speech_detector_initialization(self):
        """Test SpeechDetector initializes correctly"""
        assert self.detector.primary_engine == "silero"
        assert "silero" in self.detector.engines
        assert "webrtc" in self.detector.engines
        assert self.detector.active_engine is None
        
    def test_cache_directory_creation(self):
        """Test cache directory is created"""
        assert self.detector.cache_dir.exists()
        assert self.detector.cache_dir == Path("/tmp/music/metadata")

class TestSileroVAD:
    """Test Silero VAD implementation"""
    
    def setup_method(self):
        """Setup for each test"""
        self.silero_vad = SileroVAD()
        
    def test_silero_vad_initialization(self):
        """Test SileroVAD initializes with correct parameters"""
        assert self.silero_vad.model is None
        assert self.silero_vad.sample_rate == 16000
        assert self.silero_vad.chunk_size == 512
        
    @patch('speech_detector.SPEECH_DEPS_AVAILABLE', False)
    def test_silero_vad_missing_dependencies(self):
        """Test SileroVAD handles missing dependencies gracefully"""
        silero_vad = SileroVAD()
        
        with pytest.raises(SpeechDetectionError, match="Speech detection dependencies not available"):
            silero_vad.initialize()
    
    @patch('speech_detector.torch')
    def test_silero_vad_model_loading_failure(self, mock_torch):
        """Test SileroVAD handles model loading failure"""
        mock_torch.hub.load.side_effect = Exception("Model loading failed")
        
        silero_vad = SileroVAD()
        
        with pytest.raises(SpeechDetectionError, match="Model initialization failed"):
            silero_vad.initialize()
    
    @patch('speech_detector.SPEECH_DEPS_AVAILABLE', True)
    @patch('speech_detector.torch')
    def test_silero_vad_successful_initialization(self, mock_torch):
        """Test SileroVAD successful initialization"""
        # Mock torch.hub.load to return model and utils
        mock_model = Mock()
        mock_utils = (Mock(), Mock(), Mock(), Mock(), Mock())  # 5 utility functions
        mock_torch.hub.load.return_value = (mock_model, mock_utils)
        
        silero_vad = SileroVAD()
        result = silero_vad.initialize()
        
        assert result is True
        assert silero_vad.model == mock_model
        mock_torch.hub.load.assert_called_once_with(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )

class TestSpeechDetectionIntegration:
    """Integration tests for speech detection workflow"""
    
    def setup_method(self):
        """Setup for each test"""
        self.detector = SpeechDetector()
        
        # Create temporary test audio file
        self.test_audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.test_audio_path = Path(self.test_audio_file.name)
        self.test_audio_file.close()
        
        # Create temporary video file
        self.test_video_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        self.test_video_path = Path(self.test_video_file.name)
        self.test_video_file.close()
        
    def teardown_method(self):
        """Cleanup after each test"""
        if self.test_audio_path.exists():
            self.test_audio_path.unlink()
        if self.test_video_path.exists():
            self.test_video_path.unlink()
    
    @pytest.mark.asyncio
    async def test_audio_file_detection(self):
        """Test speech detection on audio file (mock)"""
        with patch.object(self.detector, '_detect_with_engine') as mock_detect:
            mock_segments = [
                {
                    'segment_id': 0,
                    'start_time': 1.0,
                    'end_time': 3.0,
                    'duration': 2.0,
                    'confidence': 0.8,
                    'audio_quality': 'clear'
                }
            ]
            mock_detect.return_value = mock_segments
            
            result = await self.detector.detect_speech_segments(self.test_audio_path)
            
            assert result["success"] is True
            assert result["has_speech"] is True
            assert len(result["speech_segments"]) == 1
            assert result["total_speech_duration"] == 2.0
            assert result["analysis_metadata"]["engine_used"] == "silero"
    
    @pytest.mark.asyncio
    async def test_video_file_audio_extraction(self):
        """Test audio extraction from video file"""
        with patch.object(self.detector, '_extract_audio_if_needed') as mock_extract:
            with patch.object(self.detector, '_detect_with_engine') as mock_detect:
                # Mock audio extraction returning a temporary audio file
                mock_audio_path = Path("/tmp/extracted_audio.wav")
                mock_extract.return_value = mock_audio_path
                mock_detect.return_value = []
                
                result = await self.detector.detect_speech_segments(self.test_video_path)
                
                mock_extract.assert_called_once_with(self.test_video_path)
                assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_engine_fallback_behavior(self):
        """Test fallback to secondary engine when primary fails"""
        with patch.object(self.detector, '_detect_with_engine') as mock_detect:
            # Primary engine fails, secondary succeeds
            mock_detect.side_effect = [
                Exception("Primary engine failed"),  # First call (silero)
                [{'segment_id': 0, 'start_time': 1.0, 'end_time': 2.0, 'duration': 1.0, 'confidence': 0.5, 'audio_quality': 'moderate'}]  # Second call (webrtc)
            ]
            
            result = await self.detector.detect_speech_segments(self.test_audio_path)
            
            assert result["success"] is True
            assert result["analysis_metadata"]["engine_used"] == "webrtc"
            assert mock_detect.call_count == 2
    
    @pytest.mark.asyncio
    async def test_all_engines_fail(self):
        """Test behavior when all engines fail"""
        with patch.object(self.detector, '_detect_with_engine') as mock_detect:
            mock_detect.side_effect = Exception("Engine failed")
            
            with pytest.raises(SpeechDetectionError, match="All speech detection engines failed"):
                await self.detector.detect_speech_segments(self.test_audio_path)
    
    def test_caching_functionality(self):
        """Test caching of speech analysis results"""
        # Create mock analysis result
        mock_result = {
            "success": True,
            "speech_segments": [],
            "analysis_metadata": {"processing_time": 1640995200.0}
        }
        
        # Test caching
        self.detector._cache_analysis(self.test_audio_path, mock_result)
        
        # Test loading from cache
        cached_result = self.detector._load_cached_analysis(self.test_audio_path)
        
        assert cached_result is not None
        assert cached_result["success"] is True
    
    def test_speech_insights_generation(self):
        """Test speech insights generation from cached data"""
        # Create mock cached data
        segments = [
            {'duration': 2.0, 'audio_quality': 'clear', 'start_time': 1.0, 'end_time': 3.0},
            {'duration': 1.5, 'audio_quality': 'moderate', 'start_time': 5.0, 'end_time': 6.5},
            {'duration': 3.0, 'audio_quality': 'clear', 'start_time': 8.0, 'end_time': 11.0}
        ]
        
        cached_data = {
            "success": True,
            "speech_segments": segments,
            "total_speech_duration": 6.5,
            "analysis_metadata": {"engine_used": "silero"}
        }
        
        # Cache the data
        self.detector._cache_analysis(self.test_audio_path, cached_data)
        
        # Get insights
        insights = self.detector.get_speech_insights(self.test_audio_path)
        
        assert insights["success"] is True
        assert insights["summary"]["total_segments"] == 3
        assert insights["summary"]["total_speech_duration"] == 6.5
        assert insights["quality_distribution"]["clear"] == 2
        assert insights["quality_distribution"]["moderate"] == 1
        
        # Check for quality improvement suggestion
        suggestions = insights["editing_suggestions"]
        quality_suggestions = [s for s in suggestions if s["type"] == "quality_improvement"]
        assert len(quality_suggestions) > 0

class TestMCPTools:
    """Test MCP tool endpoints"""
    
    def setup_method(self):
        """Setup for each test"""
        # Mock file manager
        self.mock_file_manager = Mock()
        
    @pytest.mark.asyncio
    async def test_detect_speech_segments_mcp_tool(self):
        """Test detect_speech_segments MCP tool"""
        test_file_path = Path("/tmp/test_video.mp4")
        
        with patch('server.file_manager') as mock_fm:
            with patch('server.speech_detector') as mock_detector:
                # Setup mocks
                mock_fm.get_file_path.return_value = test_file_path
                mock_detector.detect_speech_segments.return_value = {
                    "success": True,
                    "speech_segments": [],
                    "total_speech_duration": 0
                }
                
                # Call MCP tool
                result = await detect_speech_segments("file_12345678")
                
                assert result["success"] is True
                mock_fm.get_file_path.assert_called_once_with("file_12345678")
                mock_detector.detect_speech_segments.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_detect_speech_segments_file_not_found(self):
        """Test detect_speech_segments with non-existent file"""
        with patch('server.file_manager') as mock_fm:
            mock_fm.get_file_path.return_value = None
            
            result = await detect_speech_segments("invalid_file_id")
            
            assert result["success"] is False
            assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_speech_insights_mcp_tool(self):
        """Test get_speech_insights MCP tool"""
        test_file_path = Path("/tmp/test_video.mp4")
        
        with patch('server.file_manager') as mock_fm:
            with patch('server.speech_detector') as mock_detector:
                # Setup mocks
                mock_fm.get_file_path.return_value = test_file_path
                mock_detector.get_speech_insights.return_value = {
                    "success": True,
                    "summary": {"total_segments": 2}
                }
                
                # Call MCP tool
                result = await get_speech_insights("file_12345678")
                
                assert result["success"] is True
                assert "summary" in result
                mock_detector.get_speech_insights.assert_called_once_with(test_file_path)
    
    @pytest.mark.asyncio
    async def test_get_speech_insights_no_cached_data(self):
        """Test get_speech_insights when no cached data exists"""
        test_file_path = Path("/tmp/test_video.mp4")
        
        with patch('server.file_manager') as mock_fm:
            with patch('server.speech_detector') as mock_detector:
                # Setup mocks
                mock_fm.get_file_path.return_value = test_file_path
                mock_detector.get_speech_insights.return_value = {
                    "success": False,
                    "error": "No cached analysis found"
                }
                
                # Call MCP tool
                result = await get_speech_insights("file_12345678")
                
                assert result["success"] is False
                assert "cached analysis" in result["error"]

class TestSpeechDetectionErrorHandling:
    """Test error handling and edge cases"""
    
    def test_quality_assessment_edge_cases(self):
        """Test audio quality assessment with edge cases"""
        silero_vad = SileroVAD()
        
        # Test with minimal mock data
        import torch
        wav_data = torch.zeros(1000)  # Silent audio
        segment = {'start': 0, 'end': 500}
        
        quality = silero_vad._assess_quality(wav_data, segment)
        assert quality in ['clear', 'moderate', 'low', 'unknown']
    
    def test_timing_analysis_empty_segments(self):
        """Test timing analysis with empty segments"""
        detector = SpeechDetector()
        
        timing_analysis = detector._analyze_timing_patterns([])
        assert timing_analysis == {}
    
    def test_editing_suggestions_no_speech(self):
        """Test editing suggestions when no speech is detected"""
        detector = SpeechDetector()
        
        suggestions = detector._generate_editing_suggestions([])
        
        assert len(suggestions) == 1
        assert suggestions[0]["type"] == "no_speech"
        assert suggestions[0]["priority"] == "medium"
    
    def test_editing_suggestions_short_segments(self):
        """Test editing suggestions for short segments"""
        detector = SpeechDetector()
        
        # Create multiple short segments
        segments = [
            {'duration': 0.5, 'audio_quality': 'clear'},
            {'duration': 0.3, 'audio_quality': 'clear'},
            {'duration': 0.8, 'audio_quality': 'clear'}
        ]
        
        suggestions = detector._generate_editing_suggestions(segments)
        
        # Should suggest combining short segments
        combination_suggestions = [s for s in suggestions if s["type"] == "segment_combination"]
        assert len(combination_suggestions) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])