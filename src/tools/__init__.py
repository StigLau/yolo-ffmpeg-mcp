"""Tool modules for the FFMPEG MCP server.

Each module exposes a register(mcp, deps) function that registers
MCP tools/prompts using @mcp.tool() / @mcp.prompt() decorators.
"""

import logging

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

logger = logging.getLogger(__name__)

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
    """Register all tool modules with the MCP server.

    Each module is registered independently so that one broken module
    does not take down the entire server. Failures are logged and skipped.
    """
    registered = []
    failed = []
    for module in ALL_MODULES:
        try:
            module.register(mcp, deps)
            registered.append(module.__name__)
        except Exception as e:
            module_name = module.__name__
            failed.append(module_name)
            logger.error("Failed to register tool module %s: %s", module_name, e)
    if failed:
        logger.warning(
            "Server started with %d/%d modules. Failed: %s",
            len(registered), len(ALL_MODULES), ", ".join(failed),
        )
    else:
        logger.info("All %d tool modules registered successfully.", len(registered))
