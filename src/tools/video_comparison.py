"""Video comparison tools - A/B testing and multi-video comparison."""
from typing import Dict, List, Any, Optional

from ..server_deps import timing_decorator


def register(mcp, deps):
    file_manager = deps.file_manager
    video_comparison_tool = deps.video_comparison_tool

    @mcp.tool()
    @timing_decorator
    async def create_video_comparison(
        file_id_1: str,
        file_id_2: str,
        comparison_type: str = "side_by_side",
        label_1: str = "Version A",
        label_2: str = "Version B",
        resolution: str = "1920x1080",
        sync_audio: bool = True,
        add_labels: bool = True
    ) -> Dict[str, Any]:
        """Create side-by-side video comparison for A/B testing.

        Args:
            file_id_1: First video file ID
            file_id_2: Second video file ID
            comparison_type: Layout type ("side_by_side", "top_bottom")
            label_1: Text label for first video
            label_2: Text label for second video
            resolution: Output resolution
            sync_audio: Whether to mix both audio tracks
            add_labels: Whether to add text labels
        """
        try:
            from ..video_comparison_tool import ComparisonConfig
        except ImportError:
            from video_comparison_tool import ComparisonConfig

        config = ComparisonConfig(
            layout=comparison_type,
            sync_audio=sync_audio,
            add_labels=add_labels,
            resolution=resolution
        )

        return await video_comparison_tool.create_side_by_side_comparison(
            file_id_1, file_id_2, label_1, label_2, config
        )

    @mcp.tool()
    @timing_decorator
    async def analyze_video_differences(file_id_1: str, file_id_2: str) -> Dict[str, Any]:
        """Analyze technical and content differences between two videos.

        Args:
            file_id_1: First video file ID
            file_id_2: Second video file ID
        """
        try:
            return await video_comparison_tool.create_analysis_comparison(
                file_id_1, file_id_2, analysis_type="comprehensive"
            )
        except Exception as e:
            return {"success": False, "error": f"Failed to analyze video differences: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def create_multi_video_comparison(
        file_ids: List[str],
        labels: List[str] = None,
        layout: str = "grid",
        resolution: str = "1920x1080",
        add_labels: bool = True
    ) -> Dict[str, Any]:
        """Create 2x2 grid comparison of up to 4 videos.

        Args:
            file_ids: List of 2-4 video file IDs
            labels: Optional list of labels for each video
            layout: Layout type ("grid" for 2x2, "horizontal" for side-by-side)
            resolution: Output resolution
            add_labels: Whether to add text labels
        """
        try:
            from ..video_comparison_tool import ComparisonConfig
        except ImportError:
            from video_comparison_tool import ComparisonConfig

        if len(file_ids) < 2 or len(file_ids) > 4:
            return {"success": False, "error": "Multi-video comparison requires 2-4 videos"}

        config = ComparisonConfig(
            layout=layout,
            add_labels=add_labels,
            resolution=resolution
        )

        return await video_comparison_tool.create_four_way_comparison(
            file_ids, labels, config
        )

    @mcp.tool()
    @timing_decorator
    async def verify_music_video(
        file_id: str,
        expected_duration: Optional[float] = None,
        expected_resolution: Optional[str] = None,
        check_audio: bool = True,
        check_video: bool = True
    ) -> Dict[str, Any]:
        """Verify music video meets expected criteria.

        Args:
            file_id: Video file ID to verify
            expected_duration: Expected duration in seconds (tolerance +/-2s)
            expected_resolution: Expected resolution (e.g., "1920x1080")
            check_audio: Whether to verify audio track exists
            check_video: Whether to verify video track exists
        """
        try:
            info_result = await mcp.call_tool('get_file_info', {'file_id': file_id})
            import json
            info_data = json.loads(info_result[0].text) if info_result and len(info_result) > 0 else {}

            if not info_data.get('media_info', {}).get('success'):
                return {"success": False, "error": "Could not analyze video file", "verification_failed": True}

            video_props = info_data['media_info']['video_properties']
            basic_info = info_data['basic_info']

            verification = {
                "success": True,
                "file_id": file_id,
                "verification_passed": True,
                "checks_performed": [],
                "failures": [],
                "properties": {
                    "file_size_mb": basic_info.get('size', 0) / (1024 * 1024),
                    "duration": video_props.get('duration', 0),
                    "resolution": video_props.get('resolution'),
                    "has_video": video_props.get('has_video', False),
                    "has_audio": video_props.get('has_audio', False),
                    "codec": video_props.get('codec'),
                    "bitrate": video_props.get('bitrate'),
                    "fps": video_props.get('fps')
                }
            }

            if check_video:
                verification["checks_performed"].append("video_track_exists")
                if not video_props.get('has_video', False):
                    verification["failures"].append("No video track found")
                    verification["verification_passed"] = False

            if check_audio:
                verification["checks_performed"].append("audio_track_exists")
                if not video_props.get('has_audio', False):
                    verification["failures"].append("No audio track found")
                    verification["verification_passed"] = False

            if expected_duration is not None:
                verification["checks_performed"].append("duration_check")
                actual_duration = video_props.get('duration', 0)
                duration_diff = abs(actual_duration - expected_duration)
                if duration_diff > 2.0:
                    verification["failures"].append(
                        f"Duration mismatch: expected {expected_duration}s, got {actual_duration}s (diff: {duration_diff:.1f}s)"
                    )
                    verification["verification_passed"] = False
                else:
                    verification["duration_match"] = True

            if expected_resolution is not None:
                verification["checks_performed"].append("resolution_check")
                actual_resolution = video_props.get('resolution')
                if actual_resolution != expected_resolution:
                    verification["failures"].append(
                        f"Resolution mismatch: expected {expected_resolution}, got {actual_resolution}"
                    )
                    verification["verification_passed"] = False
                else:
                    verification["resolution_match"] = True

            verification["checks_performed"].append("quality_checks")
            quality_issues = []
            file_size_mb = verification["properties"]["file_size_mb"]
            if file_size_mb < 0.1:
                quality_issues.append("File size very small (< 0.1MB)")
            elif file_size_mb > 500:
                quality_issues.append(f"File size very large ({file_size_mb:.1f}MB)")

            codec = video_props.get('codec')
            if codec and 'h264' not in codec.lower() and 'h265' not in codec.lower():
                quality_issues.append(f"Unusual codec: {codec}")

            bitrate = video_props.get('bitrate')
            if bitrate and bitrate < 500:
                quality_issues.append(f"Low bitrate: {bitrate} kbps")

            verification["quality_issues"] = quality_issues
            if quality_issues:
                verification["has_quality_concerns"] = True

            verification["summary"] = {
                "total_checks": len(verification["checks_performed"]),
                "failed_checks": len(verification["failures"]),
                "quality_concerns": len(quality_issues),
                "overall_status": "PASS" if verification["verification_passed"] and not quality_issues else "FAIL"
            }

            return verification

        except Exception as e:
            return {"success": False, "error": f"Verification failed: {str(e)}", "verification_failed": True}
