#!/usr/bin/env python3
"""
Komposteur Bridge Processor - Komposteur-compatible interface
Expected by Komposteur's findMcpPythonProcessor() discovery mechanism

This file provides the exact interface Komposteur expects:
- Class: KompositionProcessor  
- Method: async process_komposition(kompost_data)
- Return: {"output_path": str, "success": bool}
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KomposteurBridgeProcessor:
    """
    Komposteur-compatible processor that bridges to our MCP video processing system
    Expected interface: async process_komposition(kompost_data) -> {"output_path": str}
    """
    
    def __init__(self):
        """Initialize the bridge processor"""
        try:
            from src.config import SecurityConfig
            from src.file_manager import FileManager  
            from src.ffmpeg_wrapper import FFMPEGWrapper
            from src.komposition_processor_mcp import KompositionProcessor as MCPProcessor
            
            self.config = SecurityConfig()
            self.file_manager = FileManager()
            self.ffmpeg_wrapper = FFMPEGWrapper(self.file_manager)
            self.mcp_processor = MCPProcessor(self.file_manager, self.ffmpeg_wrapper)
            
            logger.info("✅ Komposteur bridge processor initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize bridge processor: {e}")
            raise
        
    async def process_komposition(self, kompost_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process komposition using MCP video processing system
        
        Args:
            kompost_data: Komposition JSON structure with segments, metadata, etc.
            
        Returns:
            {"output_path": "path/to/final/video.mp4", "success": True/False, "error": str}
        """
        try:
            logger.info("🎬 Starting komposition processing via MCP bridge")
            
            # Log komposition metadata for debugging
            metadata = kompost_data.get('metadata', {})
            logger.info(f"Processing: {metadata.get('title', 'Unknown')} - {metadata.get('description', 'No description')}")
            logger.info(f"BPM: {metadata.get('bpm', 120)}, Segments: {len(kompost_data.get('segments', []))}")
            
            # Process using our existing MCP komposition processor
            result = await self.mcp_processor.process_komposition(kompost_data)
            
            if result.get("success", False):
                output_path = result.get("output_file")
                if output_path and Path(output_path).exists():
                    logger.info(f"✅ Komposition processed successfully: {output_path}")
                    return {
                        "success": True,
                        "output_path": output_path,
                        "processing_log": result.get("composition_info", {}),
                        "duration": result.get("composition_info", {}).get("total_duration_seconds"),
                        "segments_processed": result.get("composition_info", {}).get("segments_processed", 0)
                    }
                else:
                    logger.error(f"❌ Output file not found: {output_path}")
                    return {
                        "success": False,
                        "error": f"Output video not created: {output_path}",
                        "raw_result": result
                    }
            else:
                logger.error(f"❌ MCP processing failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown MCP processing error"),
                    "raw_result": result
                }
                
        except Exception as e:
            logger.error(f"❌ Komposition processor crashed: {e}")
            return {
                "success": False,
                "error": f"Processor exception: {str(e)}",
                "exception_type": type(e).__name__
            }

# Alias for Komposteur discovery mechanism compatibility
KompositionProcessor = KomposteurBridgeProcessor

# Entry point for Komposteur subprocess calls
async def main():
    """Entry point for Komposteur subprocess calls"""
    try:
        logger.info("🚀 Komposteur bridge processor started")
        
        if len(sys.argv) < 2:
            error_result = {"success": False, "error": "No komposition data provided"}
            print(json.dumps(error_result))
            logger.error("❌ No arguments provided")
            return
            
        # Parse komposition data from argument (Komposteur passes JSON as string)
        kompost_data_str = sys.argv[1]
        logger.info(f"Received komposition data: {len(kompost_data_str)} characters")
        
        try:
            kompost_data = json.loads(kompost_data_str)
        except json.JSONDecodeError as e:
            error_result = {"success": False, "error": f"Invalid JSON: {str(e)}"}
            print(json.dumps(error_result))
            logger.error(f"❌ JSON parse error: {e}")
            return
        
        # Process using our bridge
        processor = KomposteurBridgeProcessor()
        result = await processor.process_komposition(kompost_data)
        
        # Return result as JSON for Komposteur
        print(json.dumps(result, indent=2))
        
        if result.get("success"):
            logger.info("✅ Processing completed successfully")
        else:
            logger.error(f"❌ Processing failed: {result.get('error')}")
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Main execution failed: {str(e)}",
            "exception_type": type(e).__name__
        }
        print(json.dumps(error_result, indent=2))
        logger.error(f"❌ Main execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
