"""
YouTube Upload Service for MCP FFMPEG Server

This service handles uploading videos to YouTube using the YouTube Data API v3
with OAuth2 authentication. Specifically optimized for YouTube Shorts uploads.
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False
    logging.warning("Google API libraries not available. Install with: pip install google-api-python-client google-auth-oauthlib")

logger = logging.getLogger(__name__)

class YouTubeUploadService:
    """Service for uploading videos to YouTube with OAuth2 authentication"""
    
    # YouTube API scopes for uploading videos
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    def __init__(self, credentials_file: str = None, token_file: str = None):
        """
        Initialize YouTube upload service
        
        Args:
            credentials_file: Path to OAuth2 client credentials JSON file
            token_file: Path to store OAuth2 tokens (default: token.json)
        """
        if not GOOGLE_APIS_AVAILABLE:
            raise ImportError("Google API libraries not installed. Run: pip install google-api-python-client google-auth-oauthlib")
            
        self.credentials_file = credentials_file or os.getenv('YOUTUBE_CREDENTIALS_FILE')
        self.token_file = token_file or os.getenv('YOUTUBE_TOKEN_FILE', 'token.json')
        self.service = None
        
    async def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth2
        
        Returns:
            bool: True if authentication successful
        """
        try:
            creds = None
            
            # Load existing token if available
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Refresh existing token
                    creds.refresh(Request())
                    logger.info("🔄 Refreshed YouTube API access token")
                else:
                    # Run OAuth2 flow for new token
                    if not self.credentials_file or not os.path.exists(self.credentials_file):
                        logger.error("❌ YouTube credentials file not found. Download from Google Cloud Console.")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                    logger.info("✅ New YouTube API authentication completed")
                    
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                    
            # Build YouTube service
            self.service = build('youtube', 'v3', credentials=creds)
            logger.info("🔗 Connected to YouTube Data API v3")
            return True
            
        except Exception as e:
            logger.error(f"❌ YouTube authentication failed: {e}")
            return False
            
    async def upload_video(self, 
                          video_path: str, 
                          title: str,
                          description: str = "",
                          tags: list = None,
                          category_id: str = "22",  # People & Blogs
                          privacy_status: str = "private",
                          is_shorts: bool = True) -> Dict[str, Any]:
        """
        Upload video to YouTube
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID (22 = People & Blogs)
            privacy_status: private, public, unlisted
            is_shorts: Whether this is a YouTube Short
            
        Returns:
            Dict with upload results
        """
        if not self.service:
            auth_success = await self.authenticate()
            if not auth_success:
                return {"success": False, "error": "Authentication failed"}
                
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                return {"success": False, "error": f"Video file not found: {video_path}"}
                
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': self._format_description(description, is_shorts),
                    'tags': tags or [],
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Add Shorts-specific metadata
            if is_shorts:
                body['snippet']['description'] += "\\n\\n#Shorts #YouTubeShorts"
                
            # Prepare media upload
            media = MediaFileUpload(
                str(video_path),
                chunksize=-1,  # Upload entire file at once
                resumable=True,
                mimetype='video/mp4'
            )
            
            logger.info(f"🚀 Starting upload: {title}")
            logger.info(f"📁 File: {video_path} ({video_path.stat().st_size / (1024*1024):.1f} MB)")
            
            # Execute upload
            upload_request = self.service.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            # Handle resumable upload
            response = None
            error = None
            retry = 0
            
            while response is None:
                try:
                    status, response = upload_request.next_chunk()
                    if status:
                        logger.info(f"📤 Upload progress: {int(status.progress() * 100)}%")
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # Retry on server errors
                        retry += 1
                        if retry > 3:
                            error = f"Server error after {retry} retries: {e}"
                            break
                        logger.warning(f"⚠️ Server error, retrying ({retry}/3)...")
                        await asyncio.sleep(2 ** retry)  # Exponential backoff
                    else:
                        error = f"HTTP error: {e}"
                        break
                        
            if error:
                return {"success": False, "error": error}
                
            if response:
                video_id = response['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                shorts_url = f"https://www.youtube.com/shorts/{video_id}" if is_shorts else None
                
                logger.info(f"✅ Upload successful!")
                logger.info(f"🆔 Video ID: {video_id}")
                logger.info(f"🔗 URL: {video_url}")
                if shorts_url:
                    logger.info(f"📱 Shorts URL: {shorts_url}")
                    
                return {
                    "success": True,
                    "video_id": video_id,
                    "video_url": video_url,
                    "shorts_url": shorts_url,
                    "title": title,
                    "privacy_status": privacy_status,
                    "upload_timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Upload completed but no response received"}
                
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return {"success": False, "error": str(e)}
            
    def _format_description(self, description: str, is_shorts: bool) -> str:
        """Format video description with Shorts optimization"""
        formatted_desc = description
        
        if is_shorts:
            formatted_desc += "\\n\\n" if description else ""
            formatted_desc += "🎬 Created with MCP FFMPEG Server\\n"
            formatted_desc += "📱 Optimized for YouTube Shorts with seamless looping\\n"
            formatted_desc += "🎵 Music video with AI-powered scene selection"
            
        return formatted_desc
        
    async def get_upload_quota(self) -> Dict[str, Any]:
        """
        Get current API quota usage (if available)
        
        Returns:
            Dict with quota information
        """
        try:
            # Note: YouTube API doesn't provide quota usage directly
            # This would need to be tracked separately
            return {
                "daily_upload_limit": 50,  # YouTube's hard limit
                "note": "YouTube allows maximum 50 uploads per day per channel"
            }
        except Exception as e:
            return {"error": str(e)}
            
    async def validate_shorts_video(self, video_path: str) -> Dict[str, Any]:
        """
        Validate video meets YouTube Shorts requirements
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dict with validation results
        """
        try:
            video_path = Path(video_path)
            if not video_path.exists():
                return {"valid": False, "error": "File not found"}
                
            # Basic file checks
            file_size_mb = video_path.stat().st_size / (1024 * 1024)
            
            # Enhanced validation with ffprobe
            try:
                from .ffmpeg_wrapper import FFMPEGWrapper
                wrapper = FFMPEGWrapper()
                file_info = await wrapper.get_file_info(video_path)
                
                if file_info.get("success"):
                    props = file_info.get("video_properties", {})
                    duration = props.get("duration", 0)
                    resolution = props.get("resolution", "0x0")
                    has_video = props.get("has_video", False)
                    has_audio = props.get("has_audio", False)
                    
                    # Parse resolution
                    width, height = 0, 0
                    if resolution and "x" in resolution:
                        try:
                            width, height = map(int, resolution.split('x'))
                        except ValueError:
                            pass
                    
                    # Calculate aspect ratio
                    aspect_ratio = width / height if height > 0 else 0
                    is_shorts_ratio = abs(aspect_ratio - 9/16) < 0.1  # 9:16 with tolerance
                    is_square = abs(aspect_ratio - 1.0) < 0.1  # 1:1 square format
                    
                    # Validate Shorts requirements
                    checks = {
                        "file_exists": True,
                        "file_size_ok": file_size_mb <= 60,  # YouTube Shorts limit
                        "file_size_optimal": file_size_mb <= 10,  # Recommended size
                        "format": "mp4" if video_path.suffix.lower() == '.mp4' else "other",
                        "duration_valid": 15 <= duration <= 180,  # 15s to 3min
                        "has_video": has_video,
                        "has_audio": has_audio,
                        "resolution_hd": width >= 1080 and height >= 1920,
                        "aspect_ratio_shorts": is_shorts_ratio,
                        "aspect_ratio_square": is_square,
                    }
                    
                    # Overall validity
                    valid = (
                        checks["file_exists"] and 
                        checks["file_size_ok"] and
                        checks["format"] == "mp4" and
                        checks["duration_valid"] and
                        checks["has_video"] and
                        (checks["aspect_ratio_shorts"] or checks["aspect_ratio_square"])
                    )
                    
                    # Generate recommendations
                    recommendations = []
                    if not checks["aspect_ratio_shorts"] and not checks["aspect_ratio_square"]:
                        recommendations.append("Convert to 9:16 aspect ratio (1080x1920) for optimal Shorts display")
                    if not checks["file_size_optimal"]:
                        recommendations.append("Reduce file size to under 10MB for faster upload and processing")
                    if not checks["duration_valid"]:
                        if duration < 15:
                            recommendations.append("Extend duration to at least 15 seconds")
                        else:
                            recommendations.append("Reduce duration to 3 minutes or less")
                    if not checks["resolution_hd"]:
                        recommendations.append("Use 1080x1920 resolution for best quality")
                    if not checks["has_audio"]:
                        recommendations.append("Consider adding audio track for better engagement")
                    
                    return {
                        "valid": valid,
                        "file_size_mb": round(file_size_mb, 1),
                        "duration": duration,
                        "resolution": resolution,
                        "aspect_ratio": round(aspect_ratio, 3),
                        "checks": checks,
                        "recommendations": recommendations if recommendations else ["Video meets YouTube Shorts requirements"]
                    }
            except ImportError:
                pass
            
            # Fallback validation without detailed analysis
            basic_checks = {
                "file_exists": True,
                "file_size_ok": file_size_mb <= 60,
                "format": "mp4" if video_path.suffix.lower() == '.mp4' else "other"
            }
            
            return {
                "valid": basic_checks["file_exists"] and basic_checks["file_size_ok"] and basic_checks["format"] == "mp4",
                "file_size_mb": round(file_size_mb, 1),
                "checks": basic_checks,
                "recommendations": [
                    "Ensure 9:16 aspect ratio (1080x1920)",
                    "Duration should be 15 seconds to 3 minutes",
                    "Use H.264 codec with AAC audio",
                    "Keep file size under 10MB for optimal processing"
                ]
            }
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {"valid": False, "error": str(e)}


# Async wrapper functions for MCP integration
async def upload_to_youtube(video_path: str, 
                           title: str,
                           description: str = "",
                           tags: list = None,
                           privacy_status: str = "private") -> Dict[str, Any]:
    """
    Async function to upload video to YouTube
    
    Args:
        video_path: Path to video file
        title: Video title  
        description: Video description
        tags: List of tags
        privacy_status: private, public, unlisted
        
    Returns:
        Dict with upload results
    """
    try:
        service = YouTubeUploadService()
        result = await service.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
            is_shorts=True  # Default to Shorts for MCP integration
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def validate_youtube_shorts(video_path: str) -> Dict[str, Any]:
    """
    Validate video for YouTube Shorts upload
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dict with validation results
    """
    try:
        service = YouTubeUploadService()
        result = await service.validate_shorts_video(video_path)
        return result
    except Exception as e:
        return {"valid": False, "error": str(e)}