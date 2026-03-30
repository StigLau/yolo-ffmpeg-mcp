#!/usr/bin/env python3
"""
Startup script for Cloud Music Video Creator
Handles environment setup and application initialization
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import get_settings
from src.mcp.server import CloudMusicVideoMCP


async def setup_application():
    """Setup application environment and dependencies"""
    settings = get_settings()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting Cloud Music Video Creator in {settings.environment} mode")
    
    # Setup directories
    settings.setup_directories()
    logger.info(f"Created temp directories at {settings.temp_storage_path}")
    
    # Validate LLM configuration
    user_llm_config = settings.get_user_llm_config()
    processing_llm_config = settings.get_processing_llm_config()
    
    logger.info(f"User LLM: {user_llm_config['provider']} - {user_llm_config['model']}")
    logger.info(f"Processing LLM: {processing_llm_config['provider']} - {processing_llm_config['model']}")
    
    if not user_llm_config['api_key']:
        logger.warning(f"No API key configured for user LLM provider: {user_llm_config['provider']}")
    
    if not processing_llm_config['api_key']:
        logger.warning(f"No API key configured for processing LLM provider: {processing_llm_config['provider']}")
    
    logger.info("Application setup complete")


async def start_mcp_server():
    """Start the MCP server"""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize MCP server
        mcp_server = CloudMusicVideoMCP()
        
        logger.info("Starting MCP server...")
        await mcp_server.run_server()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        raise
    finally:
        logger.info("MCP server stopped")


async def main():
    """Main application entry point"""
    try:
        # Setup application
        await setup_application()
        
        # Start MCP server
        await start_mcp_server()
        
    except Exception as e:
        logging.error(f"Application startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())