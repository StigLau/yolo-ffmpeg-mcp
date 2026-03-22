"""Speech detection and analysis tools."""
from typing import Dict, Any

from ..server_deps import timing_decorator


def register(mcp, deps):
    file_manager = deps.file_manager
    speech_detector = deps.speech_detector

    @mcp.tool()
    @timing_decorator
    async def detect_speech_segments(file_id: str, force_reanalysis: bool = False, threshold: float = 0.5,
                                    min_speech_duration: int = 250, min_silence_duration: int = 100) -> Dict[str, Any]:
        """Detect speech segments in video/audio file using AI-powered voice activity detection.

        Args:
            file_id: ID of the source video/audio file
            force_reanalysis: Skip cache and reanalyze (default: False)
            threshold: Speech detection sensitivity 0.1-0.9 (default: 0.5)
            min_speech_duration: Minimum speech segment duration in ms (default: 250)
            min_silence_duration: Minimum silence gap to separate segments in ms (default: 100)

        Returns:
            Dictionary with speech segments, timing, and quality assessment
        """
        try:
            input_path = file_manager.resolve_id(file_id)
            if not input_path:
                return {
                    "success": False,
                    "error": f"File with ID '{file_id}' not found"
                }

            result = await speech_detector.detect_speech_segments(
                input_path,
                force_reanalysis=force_reanalysis,
                threshold=threshold,
                min_speech_duration=min_speech_duration,
                min_silence_duration=min_silence_duration
            )

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Speech detection failed: {str(e)}"
            }

    @mcp.tool()
    @timing_decorator
    async def get_speech_insights(file_id: str) -> Dict[str, Any]:
        """Get detailed insights and analysis from cached speech detection results.

        Must be called after detect_speech_segments() to have cached data available.

        Args:
            file_id: ID of the analyzed video/audio file

        Returns:
            Dictionary with summary, quality distribution, timing analysis, and editing suggestions
        """
        try:
            input_path = file_manager.resolve_id(file_id)
            if not input_path:
                return {
                    "success": False,
                    "error": f"File with ID '{file_id}' not found"
                }

            insights = speech_detector.get_speech_insights(input_path)

            return insights

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get speech insights: {str(e)}"
            }
