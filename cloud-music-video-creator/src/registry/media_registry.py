"""
Media Registry for Cloud Music Video Creator
Manages media file lifecycle, metadata, and storage references
"""

import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..models.media import MediaReference, MediaFile, MediaMetadata, MediaType, StorageType, ProcessingStatus
from ..storage.temp_storage import TempStorageBackend


class MediaRegistry:
    """Registry for managing media files and their metadata"""
    
    def __init__(self, storage_backend: TempStorageBackend):
        self.storage = storage_backend
        self.registry_path = "media-registry"
        
        # Ensure registry directory exists
        self.storage.ensure_directory(self.registry_path)
    
    async def register_file(self, file_path: str, metadata: MediaMetadata) -> MediaReference:
        """Register a media file in the registry"""
        media_id = f"media_{uuid.uuid4().hex[:8]}"
        
        # Calculate file metadata
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path_obj.stat().st_size
        
        # Generate checksum for integrity
        checksum = await self._calculate_checksum(file_path_obj)
        
        # Determine storage type based on file path
        storage_type = StorageType.TEMP if "/tmp/" in str(file_path_obj) else StorageType.LOCAL
        
        # Create media reference
        media_ref = MediaReference(
            id=media_id,
            type=metadata.type,
            storage_type=storage_type,
            storage_path=str(file_path_obj),  # Store full path for simplicity
            metadata=MediaMetadata(
                type=metadata.type,
                filename=file_path_obj.name,
                file_size_bytes=file_size,
                checksum=checksum,
                **metadata.dict(exclude={'type', 'filename', 'file_size_bytes', 'checksum'})
            ),
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24) if storage_type == StorageType.TEMP else None,
            processing_status=ProcessingStatus.PENDING
        )
        
        # Save to registry
        await self._save_media_reference(media_ref)
        
        return media_ref
    
    async def get_file(self, media_id: str) -> Optional[MediaFile]:
        """Get media file by ID"""
        media_ref = await self.get_reference(media_id)
        
        if not media_ref:
            return None
        
        # Update access time
        media_ref.update_access_time()
        await self._save_media_reference(media_ref)
        
        # Create MediaFile object
        media_file = MediaFile(
            reference=media_ref,
            content_path=media_ref.full_path
        )
        
        return media_file
    
    async def get_reference(self, media_id: str) -> Optional[MediaReference]:
        """Get media reference by ID"""
        try:
            ref_path = f"{self.registry_path}/{media_id}.json"
            data = await self.storage.read_json(ref_path)
            
            if data:
                return MediaReference.parse_obj(data)
            
            return None
            
        except Exception as e:
            print(f"Error retrieving media reference {media_id}: {e}")
            return None
    
    async def update_status(self, media_id: str, status: ProcessingStatus, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update media processing status"""
        media_ref = await self.get_reference(media_id)
        
        if not media_ref:
            return False
        
        media_ref.processing_status = status
        
        if metadata:
            if media_ref.processing_metadata is None:
                media_ref.processing_metadata = {}
            media_ref.processing_metadata.update(metadata)
        
        await self._save_media_reference(media_ref)
        return True
    
    async def list_by_type(self, media_type: MediaType) -> List[MediaReference]:
        """List media files by type"""
        media_refs = []
        
        registry_dir = Path(self.storage.base_path) / self.registry_path
        
        if registry_dir.exists():
            for json_file in registry_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    if data.get('type') == media_type:
                        media_ref = MediaReference.parse_obj(data)
                        media_refs.append(media_ref)
                        
                except Exception as e:
                    print(f"Error reading media file {json_file}: {e}")
                    continue
        
        return media_refs
    
    async def cleanup_temp_files(self, older_than: datetime) -> int:
        """Clean up temporary files older than specified date"""
        cleaned_count = 0
        
        registry_dir = Path(self.storage.base_path) / self.registry_path
        
        if registry_dir.exists():
            for json_file in registry_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Parse media reference
                    media_ref = MediaReference.parse_obj(data)
                    
                    # Check if temp file and expired
                    if (media_ref.storage_type == StorageType.TEMP and 
                        media_ref.expires_at and 
                        media_ref.expires_at < older_than):
                        
                        # Delete actual file if it exists
                        file_path = Path(media_ref.full_path)
                        if file_path.exists():
                            file_path.unlink()
                        
                        # Delete registry entry
                        json_file.unlink()
                        cleaned_count += 1
                        
                except Exception as e:
                    print(f"Error during cleanup of {json_file}: {e}")
                    continue
        
        return cleaned_count
    
    async def count(self) -> int:
        """Count total media files"""
        registry_dir = Path(self.storage.base_path) / self.registry_path
        
        if registry_dir.exists():
            return len(list(registry_dir.glob("*.json")))
        
        return 0
    
    async def get_audio_files(self) -> List[MediaReference]:
        """Get all audio files"""
        return await self.list_by_type(MediaType.AUDIO)
    
    async def get_video_files(self) -> List[MediaReference]:
        """Get all video files"""  
        return await self.list_by_type(MediaType.VIDEO)
    
    async def _save_media_reference(self, media_ref: MediaReference) -> None:
        """Save media reference to storage"""
        ref_path = f"{self.registry_path}/{media_ref.id}.json"
        
        # Convert to dict and save
        data = media_ref.dict()
        
        # Handle datetime serialization
        data['created_at'] = media_ref.created_at.isoformat()
        data['last_accessed'] = media_ref.last_accessed.isoformat()
        
        if media_ref.expires_at:
            data['expires_at'] = media_ref.expires_at.isoformat()
        
        await self.storage.write_json(ref_path, data)
    
    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()[:16]  # First 16 chars