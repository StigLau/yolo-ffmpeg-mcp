"""Shared server dependencies for tool modules."""
import time
import logging
from collections import namedtuple
from functools import wraps

logger = logging.getLogger(__name__)

ServerDeps = namedtuple('ServerDeps', [
    'file_manager', 'ffmpeg', 'content_analyzer', 'komposition_processor',
    'transition_processor', 'speech_detector', 'speech_komposition_processor',
    'enhanced_speech_analyzer', 'composition_planner', 'komposition_build_planner',
    'komposition_generator', 'effect_processor', 'audio_effect_processor',
    'download_service', 'format_manager', 'video_comparison_tool', 'haiku_agent',
    'config', 'timeout_manager', 'mcp_instance'
])

# Global tracking for context intelligence
_operation_history = []
_performance_stats = {}


def timing_decorator(func):
    """Decorator to add timing logs to MCP operations"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        logger.info(f"⏱️  Starting MCP operation: {operation_name}")
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"✅ MCP operation {operation_name} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ MCP operation {operation_name} failed after {duration:.2f}s: {e}")
            raise
    return wrapper
