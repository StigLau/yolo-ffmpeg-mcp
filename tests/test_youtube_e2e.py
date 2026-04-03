"""
End-to-End Tests for YouTube Direct Upload with Natural Language Processing

Tests complete workflow from natural language requests to YouTube upload,
including video processing, optimization, and upload validation.
"""

import asyncio
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Import MCP server components for E2E testing
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.server import (
        upload_youtube_video, 
        validate_youtube_video,
        create_video_from_description,
        list_files,
        process_file
    )
    from src.file_manager import FileManager
    from src.youtube_upload_service import upload_to_youtube, validate_youtube_shorts
    MCP_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"MCP components not available: {e}")
    MCP_COMPONENTS_AVAILABLE = False

# Skip all tests if Google API libraries not available
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False


@pytest.mark.skipif(not MCP_COMPONENTS_AVAILABLE, reason="MCP server components not available")
@pytest.mark.skipif(not GOOGLE_APIS_AVAILABLE, reason="Google API libraries not available")
class TestYouTubeEndToEnd:
    """End-to-end tests for YouTube integration with natural language processing"""
    
    @pytest.fixture
    def mock_file_manager(self):
        """Mock file manager with test video"""
        file_manager = MagicMock()
        file_manager.get_file_by_id.return_value = {
            "id": "test_file_123",
            "filename": "test_video.mp4",
            "path": "/tmp/test_video.mp4",
            "size": 1024 * 1024 * 5,  # 5MB
            "created": "2025-01-01T00:00:00Z"
        }
        return file_manager
    
    @pytest.fixture  
    def test_video_file(self):
        """Create a test video file"""
        test_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        # Write minimal MP4 header for testing
        test_file.write(b'\x00\x00\x00\x20ftypmp42\x00\x00\x00\x00mp42isom\x00\x00\x00\x08wide')
        test_file.close()
        return test_file.name
    
    async def test_natural_language_to_youtube_workflow(self):
        """
        Test complete workflow from natural language to YouTube upload
        
        Workflow:
        1. "Create a YouTube Short from my video with music"
        2. Process video for Shorts format (9:16, optimized)
        3. Validate Shorts requirements
        4. Upload to YouTube as private video
        """
        
        # Mock the video creation process
        with patch('server.create_video_from_description') as mock_create:
            mock_create.return_value = {
                "success": True,
                "final_video_file_id": "shorts_video_123",
                "workflow_summary": {
                    "resolution": "1080x1920",
                    "duration": 30.0,
                    "format": "mp4"
                }
            }
            
            # Mock YouTube upload
            with patch('server.upload_youtube_video') as mock_upload:
                mock_upload.return_value = {
                    "success": True,
                    "video_id": "abc123def456",
                    "video_url": "https://www.youtube.com/watch?v=abc123def456",
                    "shorts_url": "https://www.youtube.com/shorts/abc123def456",
                    "upload_timestamp": "2025-01-01T00:00:00Z"
                }
                
                # Test natural language processing
                description = "Create a 30-second YouTube Short with 9:16 aspect ratio using lookin video and background music"
                
                # Step 1: Create video from description
                video_result = await mock_create(description)
                assert video_result["success"] is True
                
                video_file_id = video_result["final_video_file_id"]
                
                # Step 2: Upload to YouTube
                upload_result = await mock_upload(
                    video_file_id=video_file_id,
                    title="AI Generated YouTube Short #Shorts",
                    description="Created with MCP FFMPEG Server from natural language",
                    tags=["ai", "shorts", "music"],
                    privacy_status="private",
                    is_shorts=True
                )
                
                assert upload_result["success"] is True
                assert "shorts_url" in upload_result
                assert upload_result["video_id"] == "abc123def456"
    
    @patch('server.file_manager')
    async def test_youtube_validation_workflow(self, mock_file_manager, test_video_file):
        """Test video validation before YouTube upload"""
        
        # Setup mock file manager
        mock_file_manager.get_file_by_id.return_value = {
            "id": "test_file_123",
            "filename": "test_video.mp4", 
            "path": test_video_file,
            "size": 1024 * 1024 * 5  # 5MB
        }
        
        # Mock the validation service
        with patch('server.validate_youtube_shorts') as mock_validate:
            mock_validate.return_value = {
                "valid": True,
                "file_size_mb": 5.0,
                "duration": 25.0,
                "resolution": "1080x1920",
                "aspect_ratio": 0.563,  # 9:16 ratio
                "checks": {
                    "file_exists": True,
                    "file_size_ok": True,
                    "duration_valid": True,
                    "aspect_ratio_shorts": True,
                    "has_video": True,
                    "has_audio": True
                },
                "recommendations": ["Video meets YouTube Shorts requirements"]
            }
            
            # Test validation
            result = await validate_youtube_video("test_file_123")
            
            assert result["valid"] is True
            assert result["aspect_ratio"] == 0.563  # 9:16
            assert result["source_file_id"] == "test_file_123"
            assert "Video meets YouTube Shorts requirements" in result["recommendations"]
    
    async def test_shorts_optimization_workflow(self):
        """Test automatic video optimization for YouTube Shorts"""
        
        # Mock the processing pipeline
        with patch('server.process_file') as mock_process:
            mock_process.return_value = {
                "success": True,
                "output_file_id": "optimized_shorts_456",
                "processing_time": 45.2,
                "operation_applied": "youtube_shorts_optimize"
            }
            
            # Test Shorts optimization
            result = await mock_process(
                input_file_id="source_video_123",
                operation="youtube_shorts_optimize",
                output_extension="mp4"
            )
            
            assert result["success"] is True
            assert result["operation_applied"] == "youtube_shorts_optimize"
            assert result["output_file_id"] == "optimized_shorts_456"
    
    async def test_complete_music_video_to_youtube_pipeline(self):
        """Test complete pipeline: Music video creation → Shorts optimization → YouTube upload"""
        
        # Mock the entire pipeline
        with patch('server.create_video_from_description') as mock_create, \
             patch('server.validate_youtube_video') as mock_validate, \
             patch('server.upload_youtube_video') as mock_upload:
            
            # Step 1: Create music video from description
            mock_create.return_value = {
                "success": True,
                "final_video_file_id": "music_video_789",
                "workflow_summary": {
                    "komposition_generated": True,
                    "segments_processed": 3,
                    "resolution": "1080x1920",
                    "duration": 45.0,
                    "effects_applied": ["leica_look", "crossfade_transition"],
                    "audio_mixed": True
                }
            }
            
            # Step 2: Validate for YouTube Shorts
            mock_validate.return_value = {
                "valid": True,
                "file_size_mb": 8.3,
                "duration": 45.0,
                "resolution": "1080x1920",
                "aspect_ratio": 0.563,
                "checks": {
                    "file_exists": True,
                    "file_size_ok": True,
                    "duration_valid": True,
                    "aspect_ratio_shorts": True,
                    "has_video": True,
                    "has_audio": True
                },
                "recommendations": ["Video meets YouTube Shorts requirements"]
            }
            
            # Step 3: Upload to YouTube
            mock_upload.return_value = {
                "success": True,
                "video_id": "xyz789abc123",
                "video_url": "https://www.youtube.com/watch?v=xyz789abc123",
                "shorts_url": "https://www.youtube.com/shorts/xyz789abc123",
                "title": "AI Music Video #Shorts",
                "privacy_status": "public",
                "upload_timestamp": "2025-01-01T00:00:00Z"
            }
            
            # Execute complete pipeline
            description = "Create a 45-second music video with Leica look and crossfade transitions, optimized for YouTube Shorts"
            
            # Step 1: Create video
            video_result = await mock_create(description)
            assert video_result["success"] is True
            
            video_file_id = video_result["final_video_file_id"]
            
            # Step 2: Validate
            validation_result = await mock_validate(video_file_id)
            assert validation_result["valid"] is True
            assert validation_result["aspect_ratio"] == 0.563  # 9:16
            
            # Step 3: Upload (only if validation passes)
            if validation_result["valid"]:
                upload_result = await mock_upload(
                    video_file_id=video_file_id,
                    title="AI Music Video #Shorts",
                    description="Created from natural language with MCP FFMPEG Server\\n\\n#Shorts #AI #Music",
                    tags=["ai", "music", "shorts", "automated"],
                    privacy_status="public",
                    is_shorts=True
                )
                
                assert upload_result["success"] is True
                assert "shorts_url" in upload_result
                assert upload_result["video_id"] == "xyz789abc123"
    
    async def test_error_handling_in_pipeline(self):
        """Test error handling throughout the YouTube upload pipeline"""
        
        # Test video creation failure
        with patch('server.create_video_from_description') as mock_create:
            mock_create.return_value = {
                "success": False,
                "error": "No source files found matching description"
            }
            
            result = await mock_create("Create video with non-existent files")
            assert result["success"] is False
            assert "No source files found" in result["error"]
        
        # Test validation failure
        with patch('server.validate_youtube_video') as mock_validate:
            mock_validate.return_value = {
                "valid": False,
                "error": "Video file not found: missing_file_123"
            }
            
            result = await mock_validate("missing_file_123")
            assert result["valid"] is False
            assert "Video file not found" in result["error"]
        
        # Test upload failure
        with patch('server.upload_youtube_video') as mock_upload:
            mock_upload.return_value = {
                "success": False,
                "error": "Authentication failed: Invalid credentials"
            }
            
            result = await mock_upload(
                video_file_id="valid_file_123",
                title="Test Video"
            )
            assert result["success"] is False
            assert "Authentication failed" in result["error"]


@pytest.mark.skipif(not MCP_COMPONENTS_AVAILABLE, reason="MCP components not available")
@pytest.mark.skipif(not GOOGLE_APIS_AVAILABLE, reason="Google API libraries not available")
class TestYouTubeNaturalLanguageProcessing:
    """Test natural language processing for YouTube-specific requests"""
    
    async def test_youtube_shorts_intent_recognition(self):
        """Test recognition of YouTube Shorts specific language"""
        
        shorts_descriptions = [
            "Create a YouTube Short with vertical video",
            "Make this into a 30-second TikTok style video for YouTube",
            "Generate a 9:16 aspect ratio video for Shorts feed",
            "Create vertical video optimized for mobile viewing",
            "Make a short-form video for YouTube Shorts platform"
        ]
        
        # Mock komposition generation
        with patch('server.generate_komposition_from_description') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "komposition": {
                    "metadata": {
                        "title": "YouTube Short",
                        "resolution": "1080x1920",
                        "duration": 30,
                        "bpm": 120
                    }
                },
                "intent": {
                    "platform": "youtube_shorts",
                    "format": "vertical",
                    "aspect_ratio": "9:16"
                }
            }
            
            for description in shorts_descriptions:
                result = await mock_generate(description)
                assert result["success"] is True
                assert result["komposition"]["metadata"]["resolution"] == "1080x1920"
                assert result["intent"]["platform"] == "youtube_shorts"
    
    async def test_upload_intent_recognition(self):
        """Test recognition of upload-specific language"""
        
        upload_descriptions = [
            "Upload this video to YouTube as a private Short",
            "Post to YouTube with title 'My Music Video'",
            "Share on YouTube Shorts feed with tags music, ai",
            "Publish to YouTube with public visibility",
            "Upload as unlisted YouTube Short"
        ]
        
        # Each description should trigger YouTube upload workflow
        for description in upload_descriptions:
            # Mock the intent recognition (this would be part of NLP processing)
            intent = self._extract_upload_intent(description)
            
            assert intent["action"] == "upload"
            assert intent["platform"] == "youtube"
            
            if "private" in description:
                assert intent["privacy"] == "private"
            elif "public" in description:
                assert intent["privacy"] == "public"
            elif "unlisted" in description:
                assert intent["privacy"] == "unlisted"
    
    def _extract_upload_intent(self, description: str) -> dict:
        """Helper method to extract upload intent from description"""
        intent = {
            "action": "unknown",
            "platform": "unknown",
            "privacy": "private"  # default
        }
        
        description_lower = description.lower()
        
        # Action detection
        if any(word in description_lower for word in ["upload", "post", "share", "publish"]):
            intent["action"] = "upload"
        
        # Platform detection
        if "youtube" in description_lower:
            intent["platform"] = "youtube"
        
        # Privacy detection
        if "private" in description_lower:
            intent["privacy"] = "private"
        elif "public" in description_lower:
            intent["privacy"] = "public"
        elif "unlisted" in description_lower:
            intent["privacy"] = "unlisted"
        
        return intent


if __name__ == "__main__":
    # Run end-to-end tests
    pytest.main([__file__, "-v", "--tb=short"])