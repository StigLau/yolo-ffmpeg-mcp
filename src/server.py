"""FFMPEG MCP Server - Intelligent Video Processing

Thin orchestrator that initializes components and delegates tool registration
to modular tool files under src/tools/.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .file_manager import FileManager
from .ffmpeg_wrapper import FFMPEGWrapper
from .config import SecurityConfig
from .content_analyzer import VideoContentAnalyzer
from .komposition_processor import KompositionProcessor
from .transition_processor import TransitionProcessor
from .speech_detector import SpeechDetector
from .speech_komposition_processor import SpeechKompositionProcessor
from .enhanced_speech_analyzer import EnhancedSpeechAnalyzer
from .composition_planner import CompositionPlanner
from .komposition_build_planner import KompositionBuildPlanner
from .komposition_generator import KompositionGenerator
from .effect_processor import EffectProcessor
from .download_service import get_download_service
from .audio_effect_processor import AudioEffectProcessor
from .format_manager import FormatManager
from .video_comparison_tool import VideoComparisonTool
from .timeout_manager import timeout_manager
from .haiku_subagent import HaikuSubagent, CostLimits

try:
    from .analytics_service import configure_analytics, cleanup_analytics
except ImportError:
    configure_analytics = None
    cleanup_analytics = None

from .server_deps import ServerDeps
from .tools import register_all

logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("ffmpeg-mcp")

# Configure analytics
firebase_endpoint = os.getenv("FIREBASE_ANALYTICS_ENDPOINT")
firebase_api_key = os.getenv("FIREBASE_API_KEY")
analytics_enabled = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"
if configure_analytics:
    configure_analytics(firebase_endpoint, analytics_enabled, firebase_api_key)

# Register Komposteur integration
try:
    integration_path = Path(__file__).parent.parent / "integration" / "komposteur" / "tools"
    sys.path.insert(0, str(integration_path.parent))
    from tools.mcp_tools import register_komposteur_tools
    komposteur_tools = register_komposteur_tools(mcp)
    print(f"✅ Registered {len(komposteur_tools)} Komposteur tools: {komposteur_tools}")
except Exception as e:
    print(f"⚠️  Komposteur integration failed: {e}")

# Initialize components
file_manager = FileManager()
ffmpeg = FFMPEGWrapper(SecurityConfig.FFMPEG_PATH)
content_analyzer = VideoContentAnalyzer()
komposition_processor = KompositionProcessor()
transition_processor = TransitionProcessor(file_manager, ffmpeg)
speech_detector = SpeechDetector()
speech_komposition_processor = SpeechKompositionProcessor()
enhanced_speech_analyzer = EnhancedSpeechAnalyzer()
composition_planner = CompositionPlanner()
komposition_build_planner = KompositionBuildPlanner()
komposition_generator = KompositionGenerator()
effect_processor = EffectProcessor(ffmpeg, file_manager)
audio_effect_processor = AudioEffectProcessor(ffmpeg, file_manager)
download_service = get_download_service(file_manager)
format_manager = FormatManager()
video_comparison_tool = VideoComparisonTool(ffmpeg, file_manager, content_analyzer)

# Initialize Haiku Subagent
haiku_api_key = os.getenv("ANTHROPIC_API_KEY")
cost_limits = CostLimits(daily_limit=5.0, per_analysis_limit=0.10)
haiku_agent = HaikuSubagent(
    anthropic_api_key=haiku_api_key,
    cost_limits=cost_limits,
    fallback_enabled=True
)
logger.info(f"🧠 Haiku subagent initialized (AI: {haiku_api_key is not None})")

# Bundle all dependencies
deps = ServerDeps(
    file_manager=file_manager,
    ffmpeg=ffmpeg,
    content_analyzer=content_analyzer,
    komposition_processor=komposition_processor,
    transition_processor=transition_processor,
    speech_detector=speech_detector,
    speech_komposition_processor=speech_komposition_processor,
    enhanced_speech_analyzer=enhanced_speech_analyzer,
    composition_planner=composition_planner,
    komposition_build_planner=komposition_build_planner,
    komposition_generator=komposition_generator,
    effect_processor=effect_processor,
    audio_effect_processor=audio_effect_processor,
    download_service=download_service,
    format_manager=format_manager,
    video_comparison_tool=video_comparison_tool,
    haiku_agent=haiku_agent,
    config=SecurityConfig,
    timeout_manager=timeout_manager,
    mcp_instance=mcp
)

# Register all tool modules
register_all(mcp, deps)

# Run the server
if __name__ == "__main__":
    import atexit

    if cleanup_analytics:
        atexit.register(lambda: asyncio.run(cleanup_analytics()))

    mcp.run()
