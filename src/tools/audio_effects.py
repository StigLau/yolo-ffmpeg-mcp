"""Audio effects tools - professional audio processing and mastering."""
from typing import Dict, List, Any, Optional

from ..server_deps import timing_decorator


def register(mcp, deps):
    audio_effect_processor = deps.audio_effect_processor

    @mcp.tool()
    @timing_decorator
    async def get_available_audio_effects(category: Optional[str] = None) -> Dict[str, Any]:
        """List all available audio effects with parameter discovery.

        Args:
            category: Filter by category ("eq", "dynamics", "loudness", "spatial", "filter")
        """
        try:
            return audio_effect_processor.get_available_effects(category=category)
        except Exception as e:
            return {"success": False, "error": f"Failed to get available audio effects: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def apply_audio_effect(file_id: str, effect_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply single audio effect with parameter control.

        Args:
            file_id: Source audio/video file ID
            effect_name: Effect name from get_available_audio_effects()
            parameters: Effect-specific parameters (optional)
        """
        try:
            return await audio_effect_processor.apply_effect(file_id, effect_name, parameters)
        except Exception as e:
            return {"success": False, "error": f"Failed to apply audio effect: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def apply_audio_effect_chain(file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply multiple audio effects in sequence with chaining.

        Args:
            file_id: Source audio/video file ID
            effects_chain: List of effect steps with 'effect' and optional 'parameters'
        """
        try:
            return await audio_effect_processor.apply_effect_chain(file_id, effects_chain)
        except Exception as e:
            return {"success": False, "error": f"Failed to apply audio effect chain: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def apply_audio_template(file_id: str, template_name: str) -> Dict[str, Any]:
        """Apply pre-defined or user-created audio effect template.

        Args:
            file_id: Source audio/video file ID
            template_name: Template name from list_audio_templates()
        """
        try:
            return await audio_effect_processor.apply_effect_template(file_id, template_name)
        except Exception as e:
            return {"success": False, "error": f"Failed to apply audio template: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def list_audio_templates() -> Dict[str, Any]:
        """List all available audio effect templates."""
        try:
            return {"success": True, **audio_effect_processor.list_effect_templates()}
        except Exception as e:
            return {"success": False, "error": f"Failed to list audio templates: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def save_audio_template(template_name: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save custom audio effect template.

        Args:
            template_name: Name for the new template
            template_data: Template structure with name, description, category, effects_chain
        """
        try:
            success = audio_effect_processor.save_effect_template(template_name, template_data)
            if success:
                template_path = audio_effect_processor.user_templates_dir / f"{template_name}.yaml"
                return {
                    "success": True,
                    "template_path": str(template_path),
                    "template_name": template_name,
                    "message": f"Template '{template_name}' saved successfully"
                }
            else:
                return {"success": False, "error": f"Failed to save template '{template_name}'"}
        except Exception as e:
            return {"success": False, "error": f"Failed to save audio template: {str(e)}"}
