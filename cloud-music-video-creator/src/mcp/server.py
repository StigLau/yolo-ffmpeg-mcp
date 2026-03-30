#!/usr/bin/env python3
"""
Cloud Music Video Creator - MCP Server
Provides komposition and video processing tools for LLM integration
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from fastmcp import FastMCP
from pydantic import BaseModel

from ..models.komposition import Komposition, KompositionSpec, Segment, VideoOutput
from ..models.media import MediaReference, MediaMetadata
from ..registry.komposition_registry import KompositionRegistry
from ..registry.media_registry import MediaRegistry
from ..services.komposition_processor import KompositionProcessor
from ..services.video_processor import VideoProcessor
from ..llm.processing_llm import ProcessingLLM
from ..storage.temp_storage import TempStorageBackend

logger = logging.getLogger(__name__)

class CloudMusicVideoMCP:
    """
    MCP Server for Cloud Music Video Creator
    
    Provides tools for komposition management, video processing,
    and media registry operations to user-facing LLMs.
    """
    
    def __init__(self):
        self.app = FastMCP("cloud-music-video-creator")
        
        # Initialize core services
        self.storage = TempStorageBackend()
        self.komposition_registry = KompositionRegistry(self.storage)
        self.media_registry = MediaRegistry(self.storage)
        
        # Initialize processing services
        self.processing_llm = ProcessingLLM()
        self.komposition_processor = KompositionProcessor(
            processing_llm=self.processing_llm,
            media_registry=self.media_registry
        )
        self.video_processor = VideoProcessor(
            processing_llm=self.processing_llm,
            media_registry=self.media_registry
        )
        
        # Register all MCP tools
        self._register_komposition_tools()
        self._register_media_tools()
        self._register_processing_tools()
        self._register_utility_tools()
        
        logger.info("Cloud Music Video Creator MCP Server initialized")
    
    def _register_komposition_tools(self):
        """Register komposition management tools"""
        
        @self.app.tool()
        async def create_komposition(
            title: str,
            description: str,
            user_id: str,
            bpm: float,
            duration_seconds: float,
            audio_file_path: Optional[str] = None,
            visual_concept: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Create a new komposition from basic parameters.
            
            Args:
                title: Komposition title
                description: User's creative description
                user_id: User identifier
                bpm: Beats per minute for synchronization
                duration_seconds: Target duration
                audio_file_path: Optional path to audio file
                visual_concept: Optional visual style description
            
            Returns:
                Created komposition data
            """
            try:
                spec = KompositionSpec(
                    title=title,
                    description=description,
                    bpm=bpm,
                    duration_seconds=duration_seconds,
                    audio_file_path=audio_file_path,
                    visual_concept=visual_concept
                )
                
                komposition = await self.komposition_processor.create_from_spec(
                    spec=spec,
                    user_id=user_id
                )
                
                logger.info(f"Created komposition {komposition.id} for user {user_id}")
                return komposition.dict()
                
            except Exception as e:
                logger.error(f"Error creating komposition: {e}")
                raise
        
        @self.app.tool()
        async def get_komposition(komposition_id: str) -> Dict[str, Any]:
            """
            Retrieve komposition by ID.
            
            Args:
                komposition_id: Komposition identifier
                
            Returns:
                Komposition data including processing status and generated videos
            """
            try:
                komposition = await self.komposition_registry.get(komposition_id)
                if not komposition:
                    raise ValueError(f"Komposition {komposition_id} not found")
                
                return komposition.dict()
                
            except Exception as e:
                logger.error(f"Error retrieving komposition {komposition_id}: {e}")
                raise
        
        @self.app.tool()
        async def update_komposition(
            komposition_id: str,
            updates: Dict[str, Any]
        ) -> Dict[str, Any]:
            """
            Update existing komposition with new parameters.
            
            Args:
                komposition_id: Komposition identifier
                updates: Dictionary of fields to update
                
            Returns:
                Updated komposition data
            """
            try:
                komposition = await self.komposition_registry.update(
                    komposition_id=komposition_id,
                    updates=updates
                )
                
                logger.info(f"Updated komposition {komposition_id}")
                return komposition.dict()
                
            except Exception as e:
                logger.error(f"Error updating komposition {komposition_id}: {e}")
                raise
        
        @self.app.tool()
        async def list_user_kompositions(user_id: str) -> List[Dict[str, Any]]:
            """
            List all kompositions for a user.
            
            Args:
                user_id: User identifier
                
            Returns:
                List of user's kompositions
            """
            try:
                kompositions = await self.komposition_registry.list_user_kompositions(user_id)
                return [k.dict() for k in kompositions]
                
            except Exception as e:
                logger.error(f"Error listing kompositions for user {user_id}: {e}")
                raise
    
    def _register_media_tools(self):
        """Register media management tools"""
        
        @self.app.tool()
        async def register_media_file(
            file_path: str,
            media_type: str,
            metadata: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Register a media file in the system.
            
            Args:
                file_path: Path to media file
                media_type: Type of media ("video", "audio", "image")
                metadata: Optional metadata dictionary
                
            Returns:
                Media reference data
            """
            try:
                media_metadata = MediaMetadata(
                    type=media_type,
                    **metadata or {}
                )
                
                media_ref = await self.media_registry.register_file(
                    file_path=file_path,
                    metadata=media_metadata
                )
                
                logger.info(f"Registered media file {media_ref.id}")
                return media_ref.dict()
                
            except Exception as e:
                logger.error(f"Error registering media file {file_path}: {e}")
                raise
        
        @self.app.tool()
        async def get_media_file(media_id: str) -> Dict[str, Any]:
            """
            Get media file information by ID.
            
            Args:
                media_id: Media reference identifier
                
            Returns:
                Media file data and metadata
            """
            try:
                media_file = await self.media_registry.get_file(media_id)
                if not media_file:
                    raise ValueError(f"Media file {media_id} not found")
                
                return media_file.dict()
                
            except Exception as e:
                logger.error(f"Error retrieving media file {media_id}: {e}")
                raise
    
    def _register_processing_tools(self):
        """Register video processing tools"""
        
        @self.app.tool()
        async def analyze_video_strategy(
            komposition_id: str
        ) -> Dict[str, Any]:
            """
            Analyze komposition and recommend processing strategy.
            
            Args:
                komposition_id: Komposition to analyze
                
            Returns:
                Processing strategy and cost estimates
            """
            try:
                komposition = await self.komposition_registry.get(komposition_id)
                if not komposition:
                    raise ValueError(f"Komposition {komposition_id} not found")
                
                strategy = await self.video_processor.analyze_processing_strategy(komposition)
                
                logger.info(f"Analyzed processing strategy for {komposition_id}")
                return strategy.dict()
                
            except Exception as e:
                logger.error(f"Error analyzing strategy for {komposition_id}: {e}")
                raise
        
        @self.app.tool()
        async def process_komposition_video(
            komposition_id: str,
            processing_options: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Generate video for komposition.
            
            Args:
                komposition_id: Komposition to process
                processing_options: Optional processing parameters
                
            Returns:
                Video output data and processing metadata
            """
            try:
                komposition = await self.komposition_registry.get(komposition_id)
                if not komposition:
                    raise ValueError(f"Komposition {komposition_id} not found")
                
                # Update status to processing
                await self.komposition_registry.update(
                    komposition_id=komposition_id,
                    updates={"status": "processing", "updated_at": datetime.utcnow()}
                )
                
                # Generate video
                video_output = await self.video_processor.generate_video(
                    komposition=komposition,
                    options=processing_options or {}
                )
                
                # Update komposition with output
                await self.komposition_registry.update(
                    komposition_id=komposition_id,
                    updates={
                        "status": "completed",
                        "generated_videos": komposition.generated_videos + [video_output],
                        "updated_at": datetime.utcnow()
                    }
                )
                
                logger.info(f"Generated video for komposition {komposition_id}")
                return video_output.dict()
                
            except Exception as e:
                logger.error(f"Error processing komposition {komposition_id}: {e}")
                
                # Update status to failed
                await self.komposition_registry.update(
                    komposition_id=komposition_id,
                    updates={"status": "failed", "updated_at": datetime.utcnow()}
                )
                raise
        
        @self.app.tool()
        async def get_processing_status(komposition_id: str) -> Dict[str, Any]:
            """
            Get processing status for komposition.
            
            Args:
                komposition_id: Komposition identifier
                
            Returns:
                Processing status and metadata
            """
            try:
                komposition = await self.komposition_registry.get(komposition_id)
                if not komposition:
                    raise ValueError(f"Komposition {komposition_id} not found")
                
                return {
                    "komposition_id": komposition_id,
                    "status": komposition.status,
                    "updated_at": komposition.updated_at,
                    "generated_videos": len(komposition.generated_videos),
                    "processing_metadata": komposition.processing_metadata or {}
                }
                
            except Exception as e:
                logger.error(f"Error getting status for {komposition_id}: {e}")
                raise
    
    def _register_utility_tools(self):
        """Register utility and system tools"""
        
        @self.app.tool()
        async def cleanup_temp_files(older_than_hours: int = 24) -> Dict[str, int]:
            """
            Clean up temporary files older than specified hours.
            
            Args:
                older_than_hours: Age threshold for cleanup
                
            Returns:
                Cleanup statistics
            """
            try:
                cleanup_time = datetime.utcnow().replace(
                    hour=datetime.utcnow().hour - older_than_hours
                )
                
                media_cleaned = await self.media_registry.cleanup_temp_files(cleanup_time)
                
                logger.info(f"Cleaned up {media_cleaned} temporary files")
                return {"media_files_cleaned": media_cleaned}
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                raise
        
        @self.app.tool()
        async def get_system_stats() -> Dict[str, Any]:
            """
            Get system statistics and health information.
            
            Returns:
                System statistics
            """
            try:
                # Gather basic stats
                stats = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "storage_backend": type(self.storage).__name__,
                    "processing_llm": type(self.processing_llm).__name__,
                }
                
                # Add registry stats
                total_kompositions = await self.komposition_registry.count()
                total_media_files = await self.media_registry.count()
                
                stats.update({
                    "total_kompositions": total_kompositions,
                    "total_media_files": total_media_files,
                })
                
                return stats
                
            except Exception as e:
                logger.error(f"Error getting system stats: {e}")
                raise
    
    async def run_server(self, host: str = "localhost", port: int = 3001):
        """Run the MCP server"""
        logger.info(f"Starting MCP server on {host}:{port}")
        await self.app.run(transport="stdio")

async def main():
    """Main entry point for MCP server"""
    server = CloudMusicVideoMCP()
    await server.run_server()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())