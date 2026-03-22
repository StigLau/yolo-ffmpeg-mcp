"""Komposition processing tools - beat-synchronized music video creation."""
import json
from pathlib import Path
from typing import Dict, Any

from ..server_deps import timing_decorator


def register(mcp, deps):
    file_manager = deps.file_manager
    komposition_processor = deps.komposition_processor
    transition_processor = deps.transition_processor
    speech_komposition_processor = deps.speech_komposition_processor

    @mcp.tool()
    @timing_decorator
    async def process_komposition_file(komposition_path: str) -> Dict[str, Any]:
        """Process a komposition JSON file to create beat-synchronized music video

        Args:
            komposition_path: Path to komposition JSON file (relative to project root)

        Returns:
            Result with output file ID and composition details
        """
        try:
            full_path = Path(komposition_path)
            if not full_path.is_absolute():
                project_root = Path(__file__).parent.parent.parent
                full_path = project_root / komposition_path

            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Komposition file not found: {komposition_path}"
                }

            komposition_data = await komposition_processor.load_komposition(str(full_path))
            result = await komposition_processor.process_komposition(komposition_data)

            if result.get("success") and result.get("output_file_id"):
                try:
                    compat_result = await mcp.call_tool('process_file', {
                        'input_file_id': result["output_file_id"],
                        'operation': 'youtube_recommended_encode',
                        'output_extension': 'mp4'
                    })

                    if compat_result and len(compat_result) > 0:
                        compat_data = json.loads(compat_result[0].text) if hasattr(compat_result[0], 'text') else compat_result[0]
                        if compat_data.get("success"):
                            result["output_file_id"] = compat_data["output_file_id"]
                            result["output_file"] = file_manager.resolve_id(compat_data["output_file_id"])
                            result["compatibility_encoding_applied"] = True

                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Compatibility encoding failed: {e}")
                    result["compatibility_encoding_applied"] = False

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process komposition: {str(e)}"
            }

    @mcp.tool()
    @timing_decorator
    async def process_transition_effects_komposition(komposition_path: str) -> Dict[str, Any]:
        """Process a komposition JSON file with advanced transition effects tree

        Args:
            komposition_path: Path to komposition JSON file with effects_tree (relative to project root)

        Returns:
            Result with output file ID and effects composition details
        """
        try:
            full_path = Path(komposition_path)
            if not full_path.is_absolute():
                project_root = Path(__file__).parent.parent.parent
                full_path = project_root / komposition_path

            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Transition effects komposition file not found: {komposition_path}"
                }

            komposition_data = await transition_processor.load_komposition_with_effects(str(full_path))
            result = await transition_processor.process_effects_tree(komposition_data)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process transition effects komposition: {str(e)}"
            }

    @mcp.tool()
    @timing_decorator
    async def process_speech_komposition(komposition_path: str) -> Dict[str, Any]:
        """Process a komposition JSON file with speech overlay capabilities

        This tool creates music videos that combine multiple video segments with intelligent
        speech detection and audio layering. It can detect speech in videos and layer the
        original speech over background music while maintaining perfect synchronization.

        Args:
            komposition_path: Path to komposition JSON file with speechOverlay settings (relative to project root)

        Returns:
            Result with output file ID and speech processing details
        """
        try:
            full_path = Path(komposition_path)
            if not full_path.is_absolute():
                project_root = Path(__file__).parent.parent.parent
                full_path = project_root / komposition_path

            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Speech komposition file not found: {komposition_path}"
                }

            result = await speech_komposition_processor.process_speech_komposition(str(full_path))

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process speech komposition: {str(e)}"
            }
