"""Tool modules for the FFMPEG MCP server.

Each module exposes a register(mcp, deps) function that registers
MCP tools/prompts using @mcp.tool() / @mcp.prompt() decorators.
"""

from . import (
    file_management,
    prompts,
    komposition,
    speech,
    composition,
    komposition_generation,
    process_monitoring,
    video_effects,
    format_management,
    audio_effects,
    video_comparison,
    download_youtube,
    haiku_integration,
)

ALL_MODULES = [
    file_management,
    prompts,
    komposition,
    speech,
    composition,
    komposition_generation,
    process_monitoring,
    video_effects,
    format_management,
    audio_effects,
    video_comparison,
    download_youtube,
    haiku_integration,
]


def register_all(mcp, deps):
    """Register all tool modules with the MCP server."""
    for module in ALL_MODULES:
        module.register(mcp, deps)
