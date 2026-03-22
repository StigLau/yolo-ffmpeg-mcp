"""Video effects tools - apply and chain visual effects."""
from typing import Dict, List, Any

from ..server_deps import timing_decorator


def register(mcp, deps):
    effect_processor = deps.effect_processor

    @mcp.tool()
    @timing_decorator
    async def get_available_video_effects(category: str = None, provider: str = None) -> Dict[str, Any]:
        """List all available video effects with parameter discovery.

        Args:
            category: Filter by category ("color", "stylistic", "blur", "distortion", "privacy")
            provider: Filter by provider ("ffmpeg", "opencv", "pil")

        Returns:
            Dictionary with effects, categories, providers, and effects count
        """
        try:
            return effect_processor.get_available_effects(category=category, provider=provider)
        except Exception as e:
            return {"success": False, "error": f"Failed to get available effects: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def apply_video_effect(file_id: str, effect_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Apply single video effect with parameter control.

        Args:
            file_id: Source video file ID from list_files()
            effect_name: Effect name from get_available_video_effects()
            parameters: Effect-specific parameters (optional, uses defaults if not provided)

        Returns:
            Dictionary with output file ID, processing time, and effect details
        """
        try:
            return await effect_processor.apply_effect(file_id, effect_name, parameters)
        except Exception as e:
            return {"success": False, "error": f"Failed to apply video effect: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def apply_video_effect_chain(file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply multiple effects in sequence with chaining.

        Args:
            file_id: Source video file ID from list_files()
            effects_chain: List of effect steps with 'effect' and optional 'parameters'

        Returns:
            Dictionary with final output file ID and applied effects details
        """
        try:
            return await effect_processor.apply_effect_chain(file_id, effects_chain)
        except Exception as e:
            return {"success": False, "error": f"Failed to apply video effect chain: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def suggest_efficient_workflow(goal_description: str, available_files: List[str] = None) -> Dict[str, Any]:
        """Get optimized workflow suggestions to minimize function calls.

        Args:
            goal_description: What you want to create
            available_files: Optional list of file names/IDs to work with

        Returns:
            Dictionary with recommended workflow, efficiency score, and atomic functions
        """
        try:
            goal = goal_description.lower()

            if any(keyword in goal for keyword in ['music video', 'create video', 'video from']):
                return {
                    "success": True,
                    "recommended_workflow": "atomic_single_call",
                    "efficiency_score": "95% reduction (25+ calls -> 1 call)",
                    "atomic_functions": [{
                        "function": "create_video_from_description",
                        "description": "Single atomic call for complete video creation",
                        "parameters": {"description": goal_description, "title": "Generated Video", "execution_mode": "full"},
                        "why_efficient": "Combines file discovery, komposition generation, build planning, and processing in one call"
                    }],
                    "fallback_manual": [
                        "1. list_files() - discover available media",
                        "2. generate_komposition_from_description() - create structure",
                        "3. process_komposition_file() - execute creation"
                    ],
                    "estimated_calls": 1
                }
            elif any(keyword in goal for keyword in ['effects', 'filter', 'apply', 'style']):
                return {
                    "success": True,
                    "recommended_workflow": "effect_chain_batch",
                    "efficiency_score": "80% reduction (10+ calls -> 2 calls)",
                    "atomic_functions": [
                        {"function": "get_available_video_effects", "description": "Discover all effects and parameters"},
                        {"function": "apply_video_effect_chain", "description": "Apply multiple effects in one operation"}
                    ],
                    "estimated_calls": 2
                }
            elif any(keyword in goal for keyword in ['batch', 'multiple', 'convert', 'resize']):
                return {
                    "success": True,
                    "recommended_workflow": "batch_processing",
                    "efficiency_score": "90% reduction (20+ calls -> 2-3 calls)",
                    "atomic_functions": [{
                        "function": "batch_process",
                        "description": "Process multiple operations with OUTPUT_PREVIOUS chaining"
                    }],
                    "estimated_calls": 1
                }
            else:
                return {
                    "success": True,
                    "recommended_workflow": "optimized_general",
                    "efficiency_score": "70% reduction (15+ calls -> 4-5 calls)",
                    "general_principles": [
                        "1. Always start with list_files()",
                        "2. Use atomic functions when available",
                        "3. Use batch_process() for multi-step operations",
                        "4. Use list_generated_files() to track outputs"
                    ],
                    "estimated_calls": "4-5 vs 15-25 manual calls"
                }

        except Exception as e:
            return {"success": False, "error": f"Failed to generate workflow suggestions: {str(e)}"}

    @mcp.tool()
    @timing_decorator
    async def estimate_effect_processing_time(file_id: str, effects_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate processing time for effects chain.

        Args:
            file_id: Source video file ID to analyze
            effects_chain: List of effect steps to estimate

        Returns:
            Dictionary with estimated time, per-effect estimates, and performance tiers
        """
        try:
            return effect_processor.estimate_processing_time(file_id, effects_chain)
        except Exception as e:
            return {"success": False, "error": f"Failed to estimate processing time: {str(e)}"}
