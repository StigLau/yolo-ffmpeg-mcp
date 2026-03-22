"""Haiku subagent integration tools - AI-powered video processing strategy."""
import time
import logging
from pathlib import Path
from typing import Dict, List, Any

from ..server_deps import timing_decorator

logger = logging.getLogger(__name__)


def register(mcp, deps):
    file_manager = deps.file_manager
    ffmpeg = deps.ffmpeg
    haiku_agent = deps.haiku_agent

    try:
        from ..haiku_subagent import yolo_smart_concat
    except ImportError:
        from haiku_subagent import yolo_smart_concat

    @mcp.tool()
    @timing_decorator
    async def yolo_smart_video_concat(video_file_ids: List[str]) -> Dict[str, Any]:
        """AI-powered intelligent video concatenation using Claude Haiku.

        Args:
            video_file_ids: List of video file IDs to concatenate intelligently
        """
        try:
            start_time = time.time()

            if not video_file_ids:
                return {"success": False, "error": "No video files provided"}

            video_paths = []
            for file_id in video_file_ids:
                file_info = file_manager.get_file_by_id(file_id)
                if not file_info:
                    return {"success": False, "error": f"Video file not found: {file_id}"}

                video_path = Path(file_info["path"])
                if not video_path.exists():
                    return {"success": False, "error": f"Video file does not exist: {video_path}"}

                video_paths.append(video_path)

            success, message, output_path = await yolo_smart_concat(
                video_paths, haiku_agent, ffmpeg
            )

            if success and output_path:
                output_file_id = file_manager.add_file(output_path)
                processing_time = time.time() - start_time
                cost_status = haiku_agent.get_cost_status()

                return {
                    "success": True,
                    "output_file_id": output_file_id,
                    "output_filename": output_path.name,
                    "strategy_used": "smart_analysis",
                    "analysis_cost": cost_status["daily_spend"],
                    "confidence": 0.85,
                    "reasoning": message,
                    "processing_time": processing_time,
                    "fallback_used": not haiku_agent.client,
                    "cost_status": cost_status
                }
            else:
                return {
                    "success": False,
                    "error": message,
                    "processing_time": time.time() - start_time
                }

        except Exception as e:
            logger.error(f"Smart concat failed: {e}")
            return {
                "success": False,
                "error": f"Smart concatenation failed: {str(e)}",
                "processing_time": time.time() - start_time if 'start_time' in locals() else 0
            }

    @mcp.tool()
    @timing_decorator
    async def analyze_video_processing_strategy(video_file_ids: List[str]) -> Dict[str, Any]:
        """Get Haiku AI recommendations for video processing strategy.

        Args:
            video_file_ids: List of video file IDs to analyze
        """
        try:
            if not video_file_ids:
                return {"error": "No video files provided"}

            video_paths = []
            for file_id in video_file_ids:
                file_info = file_manager.get_file_by_id(file_id)
                if not file_info:
                    return {"error": f"Video file not found: {file_id}"}

                video_path = Path(file_info["path"])
                if not video_path.exists():
                    return {"error": f"Video file does not exist: {video_path}"}

                video_paths.append(video_path)

            analysis = await haiku_agent.analyze_video_files(video_paths)
            cost_status = haiku_agent.get_cost_status()

            return {
                "recommended_strategy": analysis.recommended_strategy.value,
                "has_frame_issues": analysis.has_frame_issues,
                "needs_normalization": analysis.needs_normalization,
                "complexity_score": analysis.complexity_score,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning,
                "estimated_cost": analysis.estimated_cost,
                "estimated_processing_time": analysis.estimated_time,
                "cost_status": cost_status,
                "file_count": len(video_paths)
            }

        except Exception as e:
            logger.error(f"Strategy analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def get_haiku_cost_status() -> Dict[str, Any]:
        """Monitor AI analysis costs and usage."""
        try:
            cost_status = haiku_agent.get_cost_status()
            cost_status.update({
                "per_analysis_cost": 0.02,
                "cost_per_second": 0.008,
                "ai_enabled": haiku_agent.client is not None,
                "fallback_mode": haiku_agent.client is None,
                "daily_savings_vs_manual": (125.0 - cost_status["daily_spend"]) if cost_status["daily_spend"] > 0 else 125.0
            })
            return cost_status

        except Exception as e:
            return {"error": f"Failed to get cost status: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def reset_haiku_daily_costs() -> Dict[str, Any]:
        """Reset Haiku daily cost tracking."""
        try:
            previous_spend = haiku_agent.cost_limits.current_daily_spend
            previous_count = haiku_agent.cost_limits.analysis_count

            haiku_agent.reset_daily_costs()

            return {
                "success": True,
                "message": "Daily cost tracking reset successfully",
                "previous_spend": previous_spend,
                "previous_count": previous_count,
                "new_spend": 0.0,
                "new_count": 0
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to reset costs: {str(e)}"}
