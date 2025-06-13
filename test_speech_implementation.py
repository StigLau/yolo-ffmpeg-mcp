#!/usr/bin/env python3
"""
Quick test script to verify speech detection implementation

This script tests the basic functionality of the speech detection module
without requiring the full Docker setup or complex dependencies.
"""

import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing basic imports...")
    
    try:
        from speech_detector import SpeechDetector, SileroVAD, SpeechDetectionError
        print("  ✅ speech_detector module imported successfully")
        
        detector = SpeechDetector()
        print("  ✅ SpeechDetector initialized")
        
        silero = SileroVAD()
        print("  ✅ SileroVAD initialized")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False

def test_speech_detector_configuration():
    """Test SpeechDetector configuration and fallback system"""
    print("\n🧪 Testing SpeechDetector configuration...")
    
    try:
        from speech_detector import SpeechDetector
        
        # Test default configuration
        detector = SpeechDetector()
        assert detector.primary_engine == "silero"
        assert "silero" in detector.engines
        assert "webrtc" in detector.engines
        print("  ✅ Default configuration correct")
        
        # Test custom configuration
        detector_custom = SpeechDetector(primary_engine="webrtc", fallback_engines=["silero"])
        assert detector_custom.primary_engine == "webrtc"
        print("  ✅ Custom configuration works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False

@patch('speech_detector.SPEECH_DEPS_AVAILABLE', True)
@patch('speech_detector.torch')
def test_silero_vad_mock_initialization(mock_torch):
    """Test SileroVAD initialization with mocked dependencies"""
    print("\n🧪 Testing SileroVAD with mocked dependencies...")
    
    try:
        from speech_detector import SileroVAD
        
        # Mock successful model loading
        mock_model = Mock()
        mock_utils = (Mock(), Mock(), Mock(), Mock(), Mock())
        mock_torch.hub.load.return_value = (mock_model, mock_utils)
        
        silero = SileroVAD()
        result = silero.initialize()
        
        assert result is True
        assert silero.model == mock_model
        print("  ✅ Mocked SileroVAD initialization successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mocked initialization failed: {e}")
        return False

async def test_speech_detection_workflow():
    """Test the complete speech detection workflow with mocks"""
    print("\n🧪 Testing speech detection workflow...")
    
    try:
        from speech_detector import SpeechDetector
        
        detector = SpeechDetector()
        test_path = Path("/tmp/test_audio.wav")
        
        # Mock the _detect_with_engine method
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
        
        with patch.object(detector, '_detect_with_engine', return_value=mock_segments):
            with patch.object(detector, '_extract_audio_if_needed', return_value=test_path):
                result = await detector.detect_speech_segments(test_path)
                
                assert result["success"] is True
                assert result["has_speech"] is True
                assert len(result["speech_segments"]) == 1
                assert result["total_speech_duration"] == 2.0
                
        print("  ✅ Speech detection workflow completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Workflow test failed: {e}")
        return False

def test_mcp_tool_signatures():
    """Test that MCP tools have correct signatures"""
    print("\n🧪 Testing MCP tool signatures...")
    
    try:
        from server import detect_speech_segments, get_speech_insights
        import inspect
        
        # Check detect_speech_segments signature
        sig = inspect.signature(detect_speech_segments)
        params = list(sig.parameters.keys())
        assert 'file_id' in params
        assert 'force_reanalysis' in params
        assert 'threshold' in params
        print("  ✅ detect_speech_segments signature correct")
        
        # Check get_speech_insights signature
        sig = inspect.signature(get_speech_insights)
        params = list(sig.parameters.keys())
        assert 'file_id' in params
        print("  ✅ get_speech_insights signature correct")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MCP tool signature test failed: {e}")
        return False

def test_caching_functionality():
    """Test caching functionality"""
    print("\n🧪 Testing caching functionality...")
    
    try:
        from speech_detector import SpeechDetector
        import tempfile
        import json
        
        detector = SpeechDetector()
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            test_path = Path(f.name)
        
        # Test caching
        mock_result = {
            "success": True,
            "speech_segments": [],
            "analysis_metadata": {"processing_time": 1640995200.0}
        }
        
        detector._cache_analysis(test_path, mock_result)
        cached_result = detector._load_cached_analysis(test_path)
        
        assert cached_result is not None
        assert cached_result["success"] is True
        
        # Cleanup
        test_path.unlink()
        
        print("  ✅ Caching functionality works")
        return True
        
    except Exception as e:
        print(f"  ❌ Caching test failed: {e}")
        return False

def test_insights_generation():
    """Test speech insights generation"""
    print("\n🧪 Testing insights generation...")
    
    try:
        from speech_detector import SpeechDetector
        
        detector = SpeechDetector()
        
        # Test quality distribution analysis
        segments = [
            {'duration': 2.0, 'audio_quality': 'clear'},
            {'duration': 1.5, 'audio_quality': 'moderate'},
            {'duration': 3.0, 'audio_quality': 'clear'}
        ]
        
        quality_dist = detector._analyze_quality_distribution(segments)
        assert quality_dist['clear'] == 2
        assert quality_dist['moderate'] == 1
        print("  ✅ Quality distribution analysis works")
        
        # Test editing suggestions
        suggestions = detector._generate_editing_suggestions(segments)
        assert isinstance(suggestions, list)
        print("  ✅ Editing suggestions generation works")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Insights generation test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🎤 Speech Detection Implementation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_basic_imports),
        ("SpeechDetector Configuration", test_speech_detector_configuration),
        ("SileroVAD Mock Initialization", test_silero_vad_mock_initialization),
        ("Speech Detection Workflow", test_speech_detection_workflow),
        ("MCP Tool Signatures", test_mcp_tool_signatures),
        ("Caching Functionality", test_caching_functionality),
        ("Insights Generation", test_insights_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎉 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Speech detection implementation is ready.")
        print("\n🚀 Next steps:")
        print("  1. Build Docker image: ./build-docker.sh rebuild")
        print("  2. Run integration tests: ./build-docker.sh test")
        print("  3. Start development server: ./build-docker.sh dev")
    else:
        print("⚠️  Some tests failed. Review the implementation before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)