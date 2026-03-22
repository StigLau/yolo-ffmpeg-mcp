"""Format management tools - aspect ratio and format conversion."""
from typing import Dict, List, Any

from ..server_deps import timing_decorator


def register(mcp, deps):
    file_manager = deps.file_manager
    format_manager = deps.format_manager

    # Import COMMON_PRESETS at registration time
    try:
        from ..format_manager import COMMON_PRESETS
    except ImportError:
        from format_manager import COMMON_PRESETS

    @mcp.tool()
    @timing_decorator
    async def analyze_video_formats(file_ids: List[str]) -> Dict[str, Any]:
        """Analyze aspect ratios of multiple videos and suggest optimal target format.

        Args:
            file_ids: List of file IDs to analyze

        Returns:
            Dictionary with format analysis and recommendations
        """
        try:
            analyses = []
            for file_id in file_ids:
                file_path = file_manager.resolve_id(file_id)
                analysis = format_manager.analyze_video_format(file_path, file_id)
                analyses.append({
                    "file_id": file_id,
                    "resolution": f"{analysis.width}x{analysis.height}",
                    "aspect_ratio": f"{analysis.aspect_ratio:.2f}",
                    "orientation": analysis.orientation,
                    "suggested_crop_mode": analysis.suggested_crop_mode.value,
                    "crop_compatibility": analysis.crop_compatibility
                })

            video_analyses = [format_manager.analyze_video_format(file_manager.resolve_id(fid), fid) for fid in file_ids]
            suggested_format = format_manager.suggest_target_format(video_analyses)

            return {
                "success": True,
                "video_analyses": analyses,
                "suggested_format": {
                    "aspect_ratio": suggested_format.aspect_ratio.display_name,
                    "resolution": f"{suggested_format.width}x{suggested_format.height}",
                    "orientation": suggested_format.orientation,
                    "crop_mode": suggested_format.crop_mode.value
                },
                "common_presets": {name: {
                    "aspect_ratio": preset.aspect_ratio.display_name,
                    "resolution": f"{preset.width}x{preset.height}",
                    "crop_mode": preset.crop_mode.value
                } for name, preset in COMMON_PRESETS.items()}
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to analyze video formats: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def preview_format_conversion(
        file_id: str,
        target_format: str,
        crop_mode: str = "center_crop",
        timestamp: float = 5.0
    ) -> Dict[str, Any]:
        """Generate preview image showing how video will be cropped/fitted to target format.

        Args:
            file_id: ID of the source video
            target_format: Target format preset name or "custom"
            crop_mode: Cropping strategy
            timestamp: Time in seconds to extract preview frame
        """
        try:
            from ..format_manager import CropMode, FormatSpec, AspectRatio
        except ImportError:
            from format_manager import CropMode, FormatSpec, AspectRatio

        try:
            if target_format in COMMON_PRESETS:
                format_spec = COMMON_PRESETS[target_format]
            else:
                format_spec = COMMON_PRESETS["youtube_landscape"]

            try:
                crop_mode_enum = CropMode(crop_mode)
                format_spec = FormatSpec(format_spec.aspect_ratio, format_spec.resolution, crop_mode_enum)
            except ValueError:
                pass

            file_path = file_manager.resolve_id(file_id)
            preview_path = format_manager.generate_preview_frame(file_path, format_spec, timestamp)

            analysis = format_manager.analyze_video_format(file_path, file_id)
            conversion_plan = format_manager.create_format_conversion_plan([analysis], format_spec)

            return {
                "success": True,
                "preview_image": preview_path,
                "conversion_details": conversion_plan["video_conversions"][0],
                "quality_estimate": conversion_plan["estimated_quality_loss"],
                "warnings": conversion_plan["warnings"]
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to generate preview: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def create_format_conversion_plan(
        file_ids: List[str],
        target_format: str = "auto",
        crop_mode: str = "auto"
    ) -> Dict[str, Any]:
        """Create detailed plan for converting multiple videos to consistent target format.

        Args:
            file_ids: List of video file IDs to convert
            target_format: Target format preset or "auto"
            crop_mode: Cropping strategy or "auto" for intelligent selection
        """
        try:
            from ..format_manager import CropMode, FormatSpec
        except ImportError:
            from format_manager import CropMode, FormatSpec

        try:
            video_analyses = []
            for file_id in file_ids:
                file_path = file_manager.resolve_id(file_id)
                analysis = format_manager.analyze_video_format(file_path, file_id)
                video_analyses.append(analysis)

            if target_format == "auto":
                format_spec = format_manager.suggest_target_format(video_analyses)
            elif target_format in COMMON_PRESETS:
                format_spec = COMMON_PRESETS[target_format]
            else:
                format_spec = COMMON_PRESETS["youtube_landscape"]

            if crop_mode != "auto":
                try:
                    crop_mode_enum = CropMode(crop_mode)
                    format_spec = FormatSpec(format_spec.aspect_ratio, format_spec.resolution, crop_mode_enum)
                except ValueError:
                    pass

            conversion_plan = format_manager.create_format_conversion_plan(video_analyses, format_spec)

            return {
                "success": True,
                "conversion_plan": conversion_plan,
                "execution_ready": True,
                "estimated_processing_time": len(file_ids) * 30
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to create conversion plan: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def get_format_presets() -> Dict[str, Any]:
        """Get list of available format presets for different platforms and use cases."""
        try:
            presets = {}
            descriptions = {
                "youtube_landscape": "Standard YouTube video format (16:9 landscape)",
                "instagram_square": "Instagram square post format (1:1)",
                "instagram_story": "Instagram Story/Reels format (9:16 portrait)",
                "tiktok_vertical": "TikTok vertical video format (9:16 portrait)",
                "twitter_landscape": "Twitter video format (16:9 landscape)",
                "facebook_square": "Facebook square video format (1:1)",
                "cinema_wide": "Cinematic widescreen format (21:9)"
            }
            for name, preset in COMMON_PRESETS.items():
                presets[name] = {
                    "name": name,
                    "aspect_ratio": preset.aspect_ratio.display_name,
                    "resolution": f"{preset.width}x{preset.height}",
                    "orientation": preset.orientation,
                    "crop_mode": preset.crop_mode.value,
                    "description": descriptions.get(name, f"Format preset: {name}")
                }

            return {
                "success": True,
                "presets": presets,
                "crop_modes": {
                    "center_crop": "Crop from center, losing edges",
                    "smart_crop": "AI-detected focal point cropping",
                    "scale_letterbox": "Fit with black bars",
                    "scale_blur_bg": "Fit with blurred background",
                    "scale_stretch": "Stretch to fit (may distort)",
                    "top_crop": "Crop from top",
                    "bottom_crop": "Crop from bottom"
                }
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to get format presets: {str(e)}"}
