"""Download and YouTube tools - video downloading, YouTube Shorts optimization, and upload."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..server_deps import timing_decorator


def register(mcp, deps):
    file_manager = deps.file_manager
    ffmpeg = deps.ffmpeg
    download_service = deps.download_service

    try:
        from ..content_analyzer import VideoContentAnalyzer
        from ..youtube_upload_service import upload_to_youtube, validate_youtube_shorts
    except ImportError:
        from content_analyzer import VideoContentAnalyzer
        from youtube_upload_service import upload_to_youtube, validate_youtube_shorts

    @mcp.tool()
    @timing_decorator
    async def download_youtube_video(
        url: str, quality: str = "best", max_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """Download YouTube video for music video creation.

        Args:
            url: YouTube video URL
            quality: Quality preference ("best", "worst", "720p", "1080p")
            max_duration: Maximum duration in seconds
        """
        if not download_service.is_available():
            return {"success": False, "error": "Download service not available"}

        try:
            result = await download_service.download_youtube_video(url, quality, max_duration)
            if result.success:
                return {
                    "success": True, "file_id": result.file_id, "file_path": result.file_path,
                    "download_info": {
                        "original_url": result.original_url, "duration": result.download_duration,
                        "file_size_mb": round(result.file_size_bytes / (1024 * 1024), 2),
                        "format": result.format, "resolution": result.resolution, "cache_hit": result.cache_hit
                    },
                    "metadata": result.metadata
                }
            else:
                return {"success": False, "error": result.error}
        except Exception as e:
            return {"success": False, "error": f"Download failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def download_from_url(
        url: str, source_type: str = "auto", quality: str = "best", format: str = "mp4"
    ) -> Dict[str, Any]:
        """Download content from any supported URL.

        Args:
            url: Source URL (YouTube, S3, HTTP, etc.)
            source_type: Source type ("auto", "youtube", "s3", "http", "local")
            quality: Quality preference
            format: Output format preference
        """
        if not download_service.is_available():
            return {"success": False, "error": "Download service not available"}

        try:
            result = await download_service.download_from_url(url, source_type, quality, format)
            if result.success:
                return {
                    "success": True, "file_id": result.file_id, "file_path": result.file_path,
                    "source_info": {
                        "original_url": result.original_url, "detected_source_type": source_type,
                        "duration": result.download_duration,
                        "file_size_mb": round(result.file_size_bytes / (1024 * 1024), 2),
                        "format": result.format, "resolution": result.resolution, "cache_hit": result.cache_hit
                    },
                    "metadata": result.metadata
                }
            else:
                return {"success": False, "error": result.error}
        except Exception as e:
            return {"success": False, "error": f"Download failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def batch_download_urls(
        urls: List[str], quality: str = "best", max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """Download multiple URLs concurrently.

        Args:
            urls: List of URLs to download
            quality: Quality preference for all downloads
            max_concurrent: Maximum concurrent downloads
        """
        if not download_service.is_available():
            return {"success": False, "error": "Download service not available"}
        if not urls:
            return {"success": False, "error": "No URLs provided"}

        try:
            results = await download_service.batch_download(urls, quality, max_concurrent)
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]

            return {
                "success": len(successful) > 0,
                "batch_summary": {
                    "total_urls": len(urls), "successful": len(successful),
                    "failed": len(failed), "success_rate": f"{len(successful)/len(urls)*100:.1f}%"
                },
                "successful_downloads": [{
                    "file_id": r.file_id, "original_url": r.original_url,
                    "file_size_mb": round(r.file_size_bytes / (1024 * 1024), 2),
                    "format": r.format, "resolution": r.resolution
                } for r in successful],
                "failed_downloads": [{"original_url": r.original_url, "error": r.error} for r in failed]
            }
        except Exception as e:
            return {"success": False, "error": f"Batch download failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def get_download_info(url: str) -> Dict[str, Any]:
        """Get information about downloadable content without downloading.

        Args:
            url: URL to analyze
        """
        if not download_service.is_available():
            return {"success": False, "error": "Download service not available"}
        try:
            return await download_service.get_download_info(url)
        except Exception as e:
            return {"success": False, "error": f"Failed to get download info: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def detect_loop_points(file_id: str, desired_duration: float = 10.0) -> Dict[str, Any]:
        """AI-powered loop point detection for YouTube Shorts.

        Args:
            file_id: Source video file ID
            desired_duration: Target loop duration in seconds
        """
        try:
            analyzer = VideoContentAnalyzer()
            return await analyzer.detect_loop_points(file_id, desired_duration)
        except Exception as e:
            return {"success": False, "error": f"Loop point detection failed: {str(e)}"}

    @mcp.tool()
    async def create_seamless_loop(
        file_id: str, start_time: float, duration: float, fade_duration: float = 0.5
    ) -> Dict[str, Any]:
        """Create seamless looping video with crossfade audio.

        Args:
            file_id: Source video file ID
            start_time: Loop start time in seconds
            duration: Loop duration in seconds
            fade_duration: Audio crossfade duration in seconds
        """
        try:
            file_info = file_manager.get_file_info(file_id)
            if not file_info:
                return {"success": False, "error": "File not found"}

            input_path = file_info["path"]
            output_path = file_manager.get_temp_path(f"seamless_loop_{file_id}_{int(start_time)}_{int(duration)}.mp4")
            overlap_start = max(0, duration - fade_duration)

            trim_path = file_manager.get_temp_path(f"trimmed_for_loop_{file_id}.mp4")
            trim_command = ffmpeg.build_command("trim", input_path, trim_path, start=start_time, duration=duration)
            trim_result = await ffmpeg.execute_command(trim_command)
            if not trim_result["success"]:
                return {"success": False, "error": f"Trim failed: {trim_result.get('stderr', 'Unknown error')}"}

            loop_command = ffmpeg.build_command("create_seamless_loop", trim_path, output_path,
                                                fade_duration=fade_duration, overlap_start=overlap_start)
            result = await ffmpeg.execute_command(loop_command)

            if result["success"]:
                output_file_id = file_manager.register_generated_file(output_path, f"seamless_loop_{file_id}")
                loop_info = await ffmpeg.get_file_info(output_path)
                return {
                    "success": True, "output_file_id": output_file_id, "output_path": str(output_path),
                    "loop_settings": {"source_start": start_time, "loop_duration": duration, "fade_duration": fade_duration},
                    "file_info": loop_info.get("info", {}), "processing_time": result.get("processing_time", 0)
                }
            else:
                return {"success": False, "error": f"Loop creation failed: {result.get('stderr', 'Unknown error')}"}

        except Exception as e:
            return {"success": False, "error": f"Seamless loop creation failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def youtube_shorts_optimize(file_id: str) -> Dict[str, Any]:
        """Optimize video for YouTube Shorts platform.

        Args:
            file_id: Source video file ID
        """
        try:
            file_info = file_manager.get_file_info(file_id)
            if not file_info:
                return {"success": False, "error": "File not found"}

            input_path = file_info["path"]
            output_path = file_manager.get_temp_path(f"youtube_shorts_{file_id}.mp4")

            command = ffmpeg.build_command("youtube_shorts_optimize", input_path, output_path)
            result = await ffmpeg.execute_command(command, timeout=600)

            if result["success"]:
                output_file_id = file_manager.register_generated_file(output_path, f"youtube_shorts_{file_id}")
                optimized_info = await ffmpeg.get_file_info(output_path)
                compliance_check = await _validate_youtube_shorts_compliance(optimized_info)

                return {
                    "success": True, "output_file_id": output_file_id, "output_path": str(output_path),
                    "optimization_applied": {
                        "aspect_ratio": "9:16 (1080x1920)", "video_codec": "H.264",
                        "audio_codec": "AAC 48kHz", "gop_optimized": True, "loop_ready": True
                    },
                    "compliance_check": compliance_check,
                    "file_info": optimized_info.get("info", {}),
                    "processing_time": result.get("processing_time", 0)
                }
            else:
                return {"success": False, "error": f"Optimization failed: {result.get('stderr', 'Unknown error')}"}

        except Exception as e:
            return {"success": False, "error": f"YouTube Shorts optimization failed: {str(e)}"}

    async def _validate_youtube_shorts_compliance(file_info):
        """Validate video meets YouTube Shorts requirements."""
        compliance = {"valid": True, "checks": {}, "warnings": []}
        try:
            if not file_info.get("success"):
                compliance["valid"] = False
                return compliance

            streams = file_info.get("info", {}).get("streams", [])
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

            if video_stream:
                width = video_stream.get("width", 0)
                height = video_stream.get("height", 0)
                compliance["checks"]["resolution"] = (width == 1080 and height == 1920)
                compliance["checks"]["aspect_ratio"] = abs(width / height - 9/16) < 0.01 if height > 0 else False
                compliance["checks"]["video_codec"] = video_stream.get("codec_name", "").lower() in ["h264", "libx264"]

            if audio_stream:
                compliance["checks"]["audio_codec"] = audio_stream.get("codec_name", "").lower() in ["aac", "mp4a"]
                compliance["checks"]["sample_rate"] = audio_stream.get("sample_rate", "0") == "48000"

            compliance["valid"] = all(compliance["checks"].values())
            compliance["score"] = sum(compliance["checks"].values()) / len(compliance["checks"]) if compliance["checks"] else 0
        except Exception as e:
            compliance["valid"] = False
            compliance["error"] = str(e)
        return compliance

    @mcp.tool()
    @timing_decorator
    async def upload_youtube_short(file_id: str, title: str, description: str = "",
                                   tags: str = "", privacy_status: str = "private") -> Dict[str, Any]:
        """Upload video as YouTube Short.

        Args:
            file_id: File ID of video to upload
            title: Video title
            description: Video description
            tags: Comma-separated tags
            privacy_status: "private", "public", or "unlisted"
        """
        try:
            file_path = file_manager.resolve_id(file_id)
            if not file_path:
                return {"success": False, "error": f"File ID {file_id} not found"}

            tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
            return await upload_to_youtube(
                video_path=str(file_path), title=title, description=description,
                tags=tags_list, privacy_status=privacy_status
            )
        except Exception as e:
            return {"success": False, "error": f"YouTube upload failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def validate_youtube_short(file_id: str) -> Dict[str, Any]:
        """Validate video meets YouTube Shorts requirements.

        Args:
            file_id: File ID of video to validate
        """
        try:
            file_path = file_manager.resolve_id(file_id)
            if not file_path:
                return {"valid": False, "error": f"File ID {file_id} not found"}

            result = await validate_youtube_shorts(str(file_path))

            try:
                video_info = await ffmpeg.get_file_info(file_path, file_manager, file_id)
                if video_info.get("success"):
                    props = video_info.get("video_properties", {})
                    result["video_info"] = {
                        "resolution": props.get("resolution"),
                        "duration": props.get("duration"),
                        "codec": props.get("codec"),
                        "has_audio": props.get("has_audio", False)
                    }
                    shorts_checks = {
                        "aspect_ratio_9_16": "1080x1920" in str(props.get("resolution", "")),
                        "duration_under_3min": props.get("duration", 0) <= 180,
                        "has_video": props.get("has_video", False),
                        "has_audio": props.get("has_audio", False)
                    }
                    result["shorts_compliance"] = shorts_checks
                    result["shorts_ready"] = all(shorts_checks.values())
            except Exception:
                pass

            return result
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def cleanup_download_cache(max_age_days: int = 7) -> Dict[str, Any]:
        """Clean up old downloaded files.

        Args:
            max_age_days: Maximum age in days
        """
        try:
            return download_service.cleanup_cache(max_age_days)
        except Exception as e:
            return {"success": False, "error": f"Cache cleanup failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def upload_youtube_video(
        video_file_id: str, title: str, description: str = "",
        tags: List[str] = None, privacy_status: str = "private", is_shorts: bool = True
    ) -> Dict[str, Any]:
        """Upload video to YouTube with OAuth2 authentication.

        Args:
            video_file_id: Video file ID
            title: Video title
            description: Video description
            tags: List of tags
            privacy_status: "private", "public", or "unlisted"
            is_shorts: Whether to optimize for YouTube Shorts
        """
        try:
            video_file = file_manager.get_file_by_id(video_file_id)
            if not video_file:
                return {"success": False, "error": f"Video file not found: {video_file_id}"}

            video_path = video_file["path"]
            if not Path(video_path).exists():
                return {"success": False, "error": f"Video file does not exist: {video_path}"}

            result = await upload_to_youtube(
                video_path=video_path, title=title, description=description,
                tags=tags or [], privacy_status=privacy_status
            )

            if result.get("success"):
                result["source_file_id"] = video_file_id
                result["source_filename"] = video_file["filename"]

            return result
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def validate_youtube_video(video_file_id: str) -> Dict[str, Any]:
        """Validate video file meets YouTube Shorts requirements.

        Args:
            video_file_id: Video file ID
        """
        try:
            video_file = file_manager.get_file_by_id(video_file_id)
            if not video_file:
                return {"valid": False, "error": f"Video file not found: {video_file_id}"}

            video_path = video_file["path"]
            if not Path(video_path).exists():
                return {"valid": False, "error": f"Video file does not exist: {video_path}"}

            result = await validate_youtube_shorts(video_path)
            result["source_file_id"] = video_file_id
            result["source_filename"] = video_file["filename"]
            return result
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}
